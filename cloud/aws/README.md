# Optional AWS S3 path

**Status:** four reference artifacts were uploaded through the AWS console to the private, versioned, SSE-S3-encrypted project bucket in us-east-2. The uploader below has only been tested locally; it was not used for that upload. The CloudFormation template was not deployed. See `reports/cloud_setup_status.json`.

## Storage first

`storage.yaml` creates a private S3 bucket with blocked public access, bucket-owner enforced ownership, default AES256 server-side encryption, versioning and a policy rejecting insecure transport. The template does not create access keys or grant an unrestricted principal read/write access. Use a dedicated IAM role or profile with permissions scoped to this project bucket and prefix.

The template retains the bucket when the stack is deleted. Versions also remain until deliberately removed. Storage, requests, optional KMS and other cloud resources can incur charges. Review the template in your own AWS account before creating resources. Do not make the bucket public to make the demo work.

## Build and inspect the upload plan

From the project root:

```bash
python -m scripts.export_artifacts
python -m cloud.aws.upload --bucket YOUR-BUCKET-NAME
```

Without `--execute`, this only prints the four planned uploads. It does not need boto3 or credentials and makes no network requests.

Only these files are eligible: `player_games.csv`, `projections.csv`, `audit.json`, `run_manifest.json`. The adapter rejects missing/symlinked files and unsafe prefixes. It attaches each file's SHA-256 as S3 object metadata. It does not enumerate your home directory or upload credentials.

## Execute only in a configured account

```bash
python -m pip install -r requirements-cloud.txt
python -m cloud.aws.upload --bucket YOUR-BUCKET-NAME --profile YOUR-PROFILE --execute
```

Use the standard AWS SDK credential chain or your named profile. Do not put access keys in source code, notebooks or GitHub. No profile is needed when the environment supplies an appropriate role. For an approved KMS key, add `--kms-key alias/YOUR-KEY`; KMS permissions and charges are separate.

S3 success is not a Databricks integration test. Verify the actual uploaded objects and your access controls before claiming cloud deployment.

## Official references

- Upload API: https://docs.aws.amazon.com/boto3/latest/reference/services/s3/client/upload_file.html
- S3 block-public-access: https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html
- Encryption examples: https://docs.aws.amazon.com/boto3/latest/guide/s3-example-server-side-encryption.html
