#!/usr/bin/env python3
"""Read-only audit of AWS S3 bucket encryption and public access block settings."""
import argparse
from datetime import date, datetime
import json
from typing import Any


def config_or_error(client: Any, method: str, bucket: str, absent_codes: set[str]) -> dict[str, Any]:
    try:
        return {"status": "configured", "value": getattr(client, method)(Bucket=bucket)}
    except Exception as error:
        response = getattr(error, "response", {})
        code = response.get("Error", {}).get("Code", type(error).__name__)
        if code in absent_codes:
            return {"status": "not-configured"}
        return {"status": "unavailable", "reason": code}


def audit_buckets(client: Any, selected: str | None = None) -> list[dict[str, Any]]:
    output = []
    buckets = client.list_buckets().get("Buckets", [])
    for bucket in sorted(buckets, key=lambda item: item["Name"]):
        name = bucket["Name"]
        if selected and name != selected:
            continue
        block = config_or_error(client, "get_public_access_block", name, {"NoSuchPublicAccessBlockConfiguration"})
        encrypt = config_or_error(client, "get_bucket_encryption", name, {"ServerSideEncryptionConfigurationNotFoundError"})
        configuration = block.get("value", {}).get("PublicAccessBlockConfiguration", {})
        algorithms = [
            rule.get("ApplyServerSideEncryptionByDefault", {}).get("SSEAlgorithm", "unknown")
            for rule in encrypt.get("value", {}).get("ServerSideEncryptionConfiguration", {}).get("Rules", [])
        ]
        created = bucket.get("CreationDate")
        output.append({
            "name": name,
            "created": created.isoformat() if isinstance(created, (date, datetime)) else None,
            "public_access_block": {"status": block["status"], **({"settings": configuration} if configuration else {}), **({"reason": block["reason"]} if "reason" in block else {})},
            "default_encryption": {"status": encrypt["status"], "algorithms": algorithms, **({"reason": encrypt["reason"]} if "reason" in encrypt else {})},
        })
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", help="Optional AWS shared configuration profile")
    parser.add_argument("--bucket", help="Audit only this exact bucket name")
    args = parser.parse_args()
    try:
        import boto3
    except ImportError:
        parser.exit(2, "Install the script dependencies: pip install -r requirements.txt\n")
    try:
        session = boto3.Session(profile_name=args.profile) if args.profile else boto3.Session()
        results = audit_buckets(session.client("s3"), args.bucket)
        if args.bucket and not results:
            parser.exit(2, f"Bucket not found in account: {args.bucket}\n")
        print(json.dumps({"buckets": results, "count": len(results)}, indent=2))
    except Exception as error:
        parser.exit(2, f"S3 audit failed: {type(error).__name__}: {error}\n")


if __name__ == "__main__":
    main()
