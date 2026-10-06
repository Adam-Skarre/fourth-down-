"""Explicit S3 uploads with checksum metadata; no credentials are stored here."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from fourth_down.data import DataError

ALLOWLIST = ('player_games.csv','projections.csv','audit.json','run_manifest.json')


def build_plan(directory: Path, bucket: str, prefix: str='fourth-down/reference') -> list[dict]:
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]', bucket) or '..' in bucket or '.-' in bucket or '-.' in bucket or re.fullmatch(r'\d+\.\d+\.\d+\.\d+',bucket):
        raise DataError('Invalid S3 bucket name.')
    if not re.fullmatch(r'[A-Za-z0-9/_-]{1,120}',prefix) or prefix.startswith('/') or any(part in ('','..','.') for part in prefix.split('/')):
        raise DataError('Prefix must be relative and use letters, digits, /, _ or -.')
    result=[]
    for name in ALLOWLIST:
        path=directory/name
        if not path.is_file() or path.is_symlink():
            raise DataError(f'Missing or symlinked artifact: {path}; run scripts.export_artifacts first.')
        result.append({'path':str(path),'bucket':bucket,'key':prefix+'/'+name,
                       'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    return result


def upload(plan: list[dict], client: object, kms_key: str | None=None) -> None:
    """Client injection allows credential-free contract testing with a fake client."""
    for item in plan:
        extra={'Metadata':{'sha256':item['sha256']}, 'ServerSideEncryption':'AES256',
               'ContentType':'application/json' if item['key'].endswith('.json') else 'text/csv'}
        if kms_key:
            extra.update(ServerSideEncryption='aws:kms',SSEKMSKeyId=kms_key)
        client.upload_file(item['path'],item['bucket'],item['key'],ExtraArgs=extra)


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bucket',required=True)
    parser.add_argument('--prefix',default='fourth-down/reference')
    parser.add_argument('--directory',type=Path,default=Path('data/processed'))
    parser.add_argument('--profile')
    parser.add_argument('--kms-key')
    parser.add_argument('--execute',action='store_true',help='Actually upload. Without this flag, print a dry-run plan only.')
    args=parser.parse_args()
    try:
        plan=build_plan(args.directory,args.bucket,args.prefix)
        if not args.execute:
            print(json.dumps({'mode':'dry-run','uploads':plan},indent=2));return 0
        try:
            import boto3
        except ImportError as exc:
            raise DataError('Cloud upload requires boto3: python -m pip install -r requirements-cloud.txt') from exc
        client=boto3.Session(profile_name=args.profile).client('s3')
        upload(plan,client,args.kms_key)
        print(f'Uploaded {len(plan)} artifacts. S3 storage and request charges may apply.')
        return 0
    except Exception as exc:
        print(f'Upload did not complete: {type(exc).__name__}: {exc}')
        return 1

if __name__=='__main__':
    raise SystemExit(main())
