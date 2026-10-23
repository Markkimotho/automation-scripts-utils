"""Offline integration checks for representative multi-language automations."""
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]

def script(domain, topic, identifier, suffix):
    return ROOT / "scripts" / domain / topic / identifier / ("script." + suffix)

class MultiLanguageTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js not installed")
    def test_node_http_status_with_local_server(self):
        class Handler(BaseHTTPRequestHandler):
            def do_HEAD(self):
                self.send_response(200)
                self.end_headers()
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/health"
            path = script("api-integrations", "http", "http-status-check", "js")
            p = subprocess.run(["node", str(path), url], capture_output=True, text=True, timeout=20)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(json.loads(p.stdout)["status"], 200)
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=3)

    @unittest.skipUnless(shutil.which("node"), "Node.js not installed")
    def test_playwright_script_has_help_without_browser_download(self):
        path = script("web-browser", "playwright", "page-link-export", "js")
        p = subprocess.run(["node", str(path), "--help"], capture_output=True, text=True, timeout=10)
        self.assertEqual(p.returncode, 0, p.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node.js not installed")
    def test_typescript_json_property_select(self):
        v = subprocess.run(["node", "-p", "process.versions.node"], capture_output=True, text=True, timeout=10)
        parts = [int(x) for x in v.stdout.strip().split(".")[:2]]
        if tuple(parts) < (22, 6):
            self.skipTest("Node 22.6+ is required")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.json"
            path.write_text('{"name":"automation","count":2}', encoding="utf-8")
            entry = script("files-documents", "json", "json-property-select", "ts")
            p = subprocess.run(["node", "--experimental-strip-types", str(entry), str(path), "count"], capture_output=True, text=True, timeout=20)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(json.loads(p.stdout), 2)

    @unittest.skipUnless(shutil.which("ruby"), "Ruby not installed")
    def test_ruby_image_manifest(self):
        with tempfile.TemporaryDirectory() as folder:
            content = b"sample-data"
            (Path(folder) / "image.png").write_bytes(content)
            entry = script("media-processing", "files", "image-checksum-manifest", "rb")
            p = subprocess.run(["ruby", str(entry), folder], capture_output=True, text=True, timeout=20)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(json.loads(p.stdout)[0]["sha256"], hashlib.sha256(content).hexdigest())

    @unittest.skipUnless(shutil.which("go"), "Go is not installed")
    def test_go_tcp_connection(self):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            entry = script("networking-monitoring", "tcp", "tcp-connect-check", "go")
            p = subprocess.run(["go", "run", str(entry), "-host", "127.0.0.1", "-port", str(listener.getsockname()[1])], capture_output=True, text=True, timeout=90)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertTrue(json.loads(p.stdout)["reachable"])

    def test_terraform_wrapper_help_without_installation(self):
        entry = script("cloud-devops", "terraform", "terraform-workspaces", "sh")
        p = subprocess.run(["bash", str(entry), "--help"], capture_output=True, text=True, timeout=10)
        self.assertEqual(p.returncode, 0, p.stderr)

    @unittest.skipUnless(shutil.which("pwsh"), "PowerShell not installed")
    def test_powershell_help(self):
        entry = script("system-administration", "windows", "windows-services-report", "ps1")
        p = subprocess.run(["pwsh", "-NoProfile", "-File", str(entry), "-Help"], capture_output=True, text=True, timeout=20)
        self.assertEqual(p.returncode, 0, p.stderr)

if __name__ == "__main__":
    unittest.main()
