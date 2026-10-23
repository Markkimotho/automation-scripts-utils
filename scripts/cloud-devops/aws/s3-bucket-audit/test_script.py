"""Offline tests for S3 audit using a stubbed boto3 client."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("s3_bucket_audit", Path(__file__).with_name("script.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class FakeClient:
    def list_buckets(self):
        return {"Buckets": [{"Name": "private-bucket"}]}
    def get_public_access_block(self, Bucket):
        return {"PublicAccessBlockConfiguration": {"BlockPublicAcls": True, "IgnorePublicAcls": True, "BlockPublicPolicy": True, "RestrictPublicBuckets": True}}
    def get_bucket_encryption(self, Bucket):
        return {"ServerSideEncryptionConfiguration": {"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}}

class AuditTests(unittest.TestCase):
    def test_audit_settings_without_network(self):
        items = mod.audit_buckets(FakeClient())
        self.assertEqual(len(items), 1)
        self.assertTrue(items[0]["public_access_block"]["settings"]["BlockPublicAcls"])
        self.assertEqual(items[0]["default_encryption"]["algorithms"], ["AES256"])
    def test_exact_bucket_filter(self):
        self.assertEqual(mod.audit_buckets(FakeClient(), "other"), [])

if __name__ == "__main__":
    unittest.main()
