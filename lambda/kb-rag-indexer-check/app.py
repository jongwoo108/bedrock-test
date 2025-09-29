import os, json, urllib.parse
import boto3, requests
from requests_aws4auth import AWS4Auth

# WHOAMI 로그 (★ 순서 중요)
sts = boto3.client("sts")
print("[WHOAMI]", json.dumps(sts.get_caller_identity()))

# 환경변수에서 설정
REGION = os.environ.get("AWS_REGION", "us-east-1")
AOSS_ENDPOINT = os.environ["AOSS_ENDPOINT"].rstrip("/")
INDEX_NAME = os.environ.get("INDEX_NAME", "kb-rag")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "amazon.titan-embed-text-v2:0")
COLLECTION_NAME = os.environ["COLLECTION_NAME"]

s3 = boto3.client("s3")
bedrock = boto3.client("bedrock-runtime", region_name=REGION)

session = boto3.Session()
creds = session.get_credentials().get_frozen_credentials()  # ← 얼려서 사용하면 안전
awsauth = AWS4Auth(
    creds.access_key, creds.secret_key, REGION, "aoss", session_token=creds.token
)

def _read_s3_text(bucket, key, max_mb=5):
    obj = s3.get_object(Bucket=bucket, Key=key)
    body = obj["Body"].read()
    if len(body) > max_mb * 1024 * 1024:
        body = body[: max_mb * 1024 * 1024]
    return body.decode("utf-8", errors="ignore")

def _embed(text: str):
    payload = {"inputText": text[:4000]}
    resp = bedrock.invoke_model(
        modelId=EMBEDDING_MODEL,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(payload).encode("utf-8"),
    )
    out = json.loads(resp["body"].read())
    vector = out.get("embedding") or out.get("vector")
    if not vector:
        raise RuntimeError("Titan embedding not found in response")
    return vector

def _index_doc(doc_id: str, text: str, vector):
    url = f"{AOSS_ENDPOINT}/{INDEX_NAME}/_doc/{requests.utils.quote(doc_id, safe='')}"
    body = {"id": doc_id, "content": text, "embedding": vector}
    r = requests.put(
        url,
        auth=awsauth,
        headers={
            "Content-Type": "application/json",
            "x-amz-collection-name": os.environ.get("COLLECTION_NAME", "kb-rag"),
        },
        data=json.dumps(body),
    )
    if r.status_code >= 300:
        raise RuntimeError(f"AOSS index error {r.status_code}: {r.text}")

def lambda_handler(event, context):
    for rec in event.get("Records", []):
        bucket = rec["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(rec["s3"]["object"]["key"])

        if not (key.endswith(".txt") or key.endswith(".md")):
            print(f"skip non-text {key}")
            continue

        text = _read_s3_text(bucket, key)
        if not text.strip():
            print(f"empty text: {key}")
            continue

        vec = _embed(text)
        doc_id = f"s3::{bucket}/{key}"
        _index_doc(doc_id, text, vec)
        print(f"Indexed: {doc_id}")

    return {"ok": True}
