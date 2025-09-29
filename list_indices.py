# list_indices.py
import os, argparse, requests, boto3
from requests_aws4auth import AWS4Auth

parser = argparse.ArgumentParser()
parser.add_argument("--endpoint", required=True)     # e.g. https://<id>.us-east-1.aoss.amazonaws.com
parser.add_argument("--collection", required=True)   # e.g. kb-rag
parser.add_argument("--region", default="us-east-1")
parser.add_argument("--profile", default=None)       # 필요하면 AWS 프로필 지정
args = parser.parse_args()

session = boto3.Session(profile_name=args.profile, region_name=args.region) if args.profile \
    else boto3.Session(region_name=args.region)

creds = session.get_credentials().get_frozen_credentials()
awsauth = AWS4Auth(creds.access_key, creds.secret_key, args.region, "aoss", session_token=creds.token)

url = f"{args.endpoint.rstrip('/')}/_cat/indices?v"
headers = {"x-amz-collection-name": args.collection}

r = requests.get(url, auth=awsauth, headers=headers)
print(r.status_code)
print(r.text)
if r.status_code == 403:
    print("\n[HINT] 403이면, 현재 로컬에서 사용 중인 IAM 주체(사용자/역할)가 AOSS 데이터 접근 정책의 Principal에 포함돼 있는지 확인하세요.")
