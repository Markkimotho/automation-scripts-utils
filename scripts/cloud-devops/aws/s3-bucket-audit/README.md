# AWS S3 Bucket Audit

Inventory accessible AWS S3 buckets and check default encryption and account-visible bucket Public Access Block settings. The audit uses read-only Boto3 APIs; it does not change S3 configuration.

## Prerequisites

Python 3.10+, AWS credentials with `s3:ListAllMyBuckets`, `s3:GetBucketPublicAccessBlock`, and `s3:GetEncryptionConfiguration` permissions. Configure credentials through the default AWS credential provider chain or a named profile. Missing permissions are reported as unavailable, rather than silently interpreted as insecure.

```bash
python3 -m pip install -r scripts/cloud-devops/aws/s3-bucket-audit/requirements.txt
python3 scripts/cloud-devops/aws/s3-bucket-audit/script.py --profile audit-role
python3 scripts/cloud-devops/aws/s3-bucket-audit/script.py --bucket my-bucket
automation info s3-bucket-audit
automation run s3-bucket-audit --dry-run
```

## Output

JSON bucket inventory, creation timestamp where present, public access block configuration and default encryption algorithms. Run in an account you are authorized to audit. No credentials are stored or printed.

## Tests

```bash
python3 scripts/cloud-devops/aws/s3-bucket-audit/test_script.py
```

The test stubs the S3 client: no AWS account or network is needed.
