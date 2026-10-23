#!/usr/bin/env python3
"""Create a PostgreSQL archive only after a private, non-superuser restore succeeds."""

import argparse
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

TOOLS = ("postgres", "initdb", "pg_isready", "psql", "pg_dump", "pg_restore")


def binaries(directory=None):
    if directory:
        candidates = [Path(directory)]
    else:
        candidates = []
        if shutil.which("postgres"):
            candidates.append(Path(shutil.which("postgres")).resolve().parent)
        if shutil.which("pg_config"):
            result = subprocess.run(
                [shutil.which("pg_config"), "--bindir"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                candidates.append(Path(result.stdout.strip()))
        candidates.extend(
            sorted(Path("/usr/lib/postgresql").glob("*/bin"), reverse=True)
        )
    for candidate in candidates:
        if all(
            (candidate / tool).is_file() and os.access(candidate / tool, os.X_OK)
            for tool in TOOLS
        ):
            return {tool: str((candidate / tool).resolve()) for tool in TOOLS}
    raise ValueError("PostgreSQL server/client tools are missing; use --pg-bin")


def clean_environment():
    result = {
        key: value for key, value in os.environ.items() if not key.startswith("PG")
    }
    result.update(PGPASSFILE=os.devnull, PGCONNECT_TIMEOUT="3")
    return result


def remaining(deadline):
    seconds = deadline - time.monotonic()
    if seconds <= 0:
        raise TimeoutError("operation deadline exceeded")
    return seconds


def checked(command, environment, deadline, *, capture=False):
    result = subprocess.run(
        command,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=remaining(deadline),
    )
    if result.returncode:
        raise ValueError("PostgreSQL command failed")
    if capture and len(result.stdout) > 1 << 20:
        raise ValueError("command result exceeds metadata limit")
    return result.stdout if capture else b""


class PrivateCluster:
    """An owned temporary PostgreSQL instance accepting only private Unix sockets."""

    def __init__(self, tools, deadline):
        self.tools, self.deadline = tools, deadline
        self.temporary = None
        self.process = None
        self.environment = clean_environment()

    def __enter__(self):
        self.temporary = tempfile.TemporaryDirectory(
            prefix="automation-pg-", dir="/tmp"
        )
        root = Path(self.temporary.name)
        socket = root / "socket"
        socket.mkdir(mode=0o700)
        self.environment.update(
            PGHOST=str(socket),
            PGPORT="5432",
            PGUSER="automation_admin",
            PGDATABASE="postgres",
        )
        try:
            checked(
                [
                    self.tools["initdb"],
                    "-D",
                    str(root / "data"),
                    "--username=automation_admin",
                    "--auth-local=trust",
                    "--auth-host=reject",
                    "--encoding=UTF8",
                    "--no-locale",
                    "--no-sync",
                ],
                self.environment,
                self.deadline,
            )
            command = [
                self.tools["postgres"],
                "-D",
                str(root / "data"),
                "-c",
                "listen_addresses=",
                "-c",
                "unix_socket_directories=" + str(socket),
                "-c",
                "unix_socket_permissions=0700",
                "-c",
                "max_connections=10",
                "-c",
                "shared_buffers=16MB",
                "-c",
                "work_mem=2MB",
                "-c",
                "maintenance_work_mem=16MB",
                "-c",
                "fsync=off",
                "-c",
                "jit=off",
            ]
            self.process = subprocess.Popen(
                command,
                env=self.environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            while True:
                if self.process.poll() is not None:
                    raise ValueError("temporary PostgreSQL server stopped")
                probe = subprocess.run(
                    [self.tools["pg_isready"], "-q", "-t", "1"],
                    env=self.environment,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=min(2, remaining(self.deadline)),
                )
                if probe.returncode == 0:
                    break
                time.sleep(min(0.05, remaining(self.deadline)))
            return self
        except BaseException:
            self.close()
            raise

    def sql(self, statement, environment=None):
        return (
            checked(
                [
                    self.tools["psql"],
                    "-X",
                    "-w",
                    "-A",
                    "-t",
                    "-v",
                    "ON_ERROR_STOP=1",
                    "-c",
                    statement,
                ],
                environment or self.environment,
                self.deadline,
                capture=True,
            )
            .decode("utf-8")
            .strip()
        )

    def verifier(self):
        self.sql(
            "CREATE ROLE automation_restore LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION"
        )
        self.sql("CREATE DATABASE automation_check OWNER automation_restore")
        environment = dict(
            self.environment, PGUSER="automation_restore", PGDATABASE="automation_check"
        )
        environment["PGOPTIONS"] = "-c statement_timeout=" + str(
            max(1, int(remaining(self.deadline) * 1000))
        )
        return environment

    def close(self):
        if self.process is not None and self.process.poll() is None:
            self.process.send_signal(signal.SIGINT)
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(self.process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                self.process.wait(timeout=10)
        if self.temporary is not None:
            self.temporary.cleanup()
            self.temporary = None

    def __exit__(self, *_):
        self.close()


def dump(command, environment, deadline, target, limit):
    with target.open("xb") as output:
        os.chmod(target, 0o600)
        process = subprocess.Popen(
            command,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        timer = None
        total = 0
        try:

            def stop_dump():
                try:
                    process.kill()
                except ProcessLookupError:
                    pass

            timer = threading.Timer(remaining(deadline), stop_dump)
            timer.daemon = True
            timer.start()
            while True:
                block = process.stdout.read(65536)
                if not block:
                    break
                remaining(deadline)
                total += len(block)
                if total > limit:
                    raise ValueError("archive exceeds max-bytes")
                output.write(block)
            if process.wait(timeout=remaining(deadline)):
                raise ValueError("pg_dump failed")
            output.flush()
            os.fsync(output.fileno())
        finally:
            if timer is not None:
                timer.cancel()
            if process.poll() is None:
                process.kill()
            process.wait(timeout=10)
            process.stdout.close()
    return total


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("database", "host", "username"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--port", type=int, default=5432)
    parser.add_argument("--pg-bin", type=Path)
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--max-bytes", type=int, default=1 << 30)
    parser.add_argument(
        "--sslmode",
        choices=("verify-full", "verify-ca", "require", "disable", "prefer"),
        default="verify-full",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    phase = "preflight"
    try:
        if os.name == "nt" or not hasattr(os, "geteuid") or os.geteuid() == 0:
            raise ValueError("requires a non-root POSIX user")
        if not all(
            re.fullmatch(r"[A-Za-z_][A-Za-z0-9_$-]{0,62}", value)
            for value in (args.database, args.username)
        ):
            raise ValueError(
                "database and username must be simple identifiers, not connection strings"
            )
        if not args.host or any(
            character.isspace() or character in "=@" for character in args.host
        ):
            raise ValueError(
                "host must be a hostname, IP address or simple absolute Unix socket path"
            )
        if (
            not 1 <= args.port <= 65535
            or not math.isfinite(args.timeout)
            or not 0 < args.timeout <= 600
            or not 0 < args.max_bytes <= 1 << 40
        ):
            raise ValueError("invalid port, timeout or archive byte budget")
        output = args.output.expanduser().absolute()
        output = output.parent.resolve(strict=True) / output.name
        if os.path.lexists(output):
            raise ValueError("output exists")
        if not args.apply:
            print(
                json.dumps(
                    {
                        "apply": False,
                        "database": args.database,
                        "host": args.host,
                        "output": str(output),
                        "restore_verification": "private-non-superuser-cluster",
                    }
                )
            )
            return 0
        deadline = time.monotonic() + args.timeout
        tools = binaries(args.pg_bin)
        versions = []
        for name in ("postgres", "pg_dump", "pg_restore"):
            version = checked(
                [tools[name], "--version"], clean_environment(), deadline, capture=True
            ).decode("utf-8")
            match = re.search(r"(\d+)\.", version)
            if match is None:
                raise ValueError("cannot identify PostgreSQL version")
            versions.append(int(match.group(1)))
        if min(versions) < 15 or len(set(versions)) != 1:
            raise ValueError("require matching PostgreSQL >=15 server and client tools")
        environment = clean_environment()
        for key in (
            "PGPASSWORD",
            "PGPASSFILE",
            "PGSSLROOTCERT",
            "PGSSLCERT",
            "PGSSLKEY",
            "PGSSLCRL",
            "PGSSLCRLDIR",
        ):
            if key in os.environ:
                environment[key] = os.environ[key]
        environment.update(
            PGSSLMODE=args.sslmode,
            PGCONNECT_TIMEOUT=str(max(1, math.ceil(min(10, remaining(deadline))))),
            PGOPTIONS="-c default_transaction_read_only=on -c statement_timeout="
            + str(max(1, int(remaining(deadline) * 1000))),
        )
        with tempfile.TemporaryDirectory(
            prefix=".postgres-backup-", dir=output.parent
        ) as directory:
            archive = Path(directory) / "snapshot.dump"
            phase = "dump"
            size = dump(
                [
                    tools["pg_dump"],
                    "--format=custom",
                    "--compress=0",
                    "--no-owner",
                    "--no-privileges",
                    "--no-password",
                    "--host=" + args.host,
                    "--port=" + str(args.port),
                    "--username=" + args.username,
                    "--dbname=" + args.database,
                ],
                environment,
                deadline,
                archive,
                args.max_bytes,
            )
            phase = "private-restore"
            with PrivateCluster(tools, deadline) as cluster:
                verifier = cluster.verifier()
                checked(
                    [
                        tools["pg_restore"],
                        "--exit-on-error",
                        "--no-owner",
                        "--no-privileges",
                        "--no-password",
                        "--dbname=automation_check",
                        str(archive),
                    ],
                    verifier,
                    deadline,
                )
                tables = int(
                    cluster.sql(
                        "SELECT COUNT(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.relkind IN ('r','p') AND n.nspname NOT LIKE 'pg_%' AND n.nspname <> 'information_schema'",
                        verifier,
                    )
                )
            phase = "publication"
            os.link(archive, output)
        print(
            json.dumps(
                {
                    "apply": True,
                    "output": str(output),
                    "bytes": size,
                    "restore_verified": True,
                    "verified_tables": tables,
                    "postgres_major": versions[0],
                }
            )
        )
        return 0
    except (OSError, ValueError, subprocess.SubprocessError):
        print(
            "postgres-verified-backup: "
            + phase
            + " failed; check tool versions, permissions, source access, restore compatibility, limits and output collisions; server diagnostics are omitted",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
