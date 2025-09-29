import argparse, json, requests, boto3
from requests_aws4auth import AWS4Auth

parser = argparse.ArgumentParser()
parser.add_argument("--endpoint", required=True)         # e.g. https://iwvt29rkcwesncyf8sw8.us-east-1.aoss.amazonaws.com
parser.add_argument("--collection", required=True)       # e.g. kb-rag
parser.add_argument("--index", required=True)            # e.g. kb-rag
parser.add_argument("--region", default="us-east-1")
parser.add_argument("--dim", type=int, default=1536)     # Titan v2 = 1536
args = parser.parse_args()

session = boto3.Session(region_name=args.region)
creds = session.get_credentials().get_frozen_credentials()
awsauth = AWS4Auth(creds.access_key, creds.secret_key, args.region, "aoss", session_token=creds.token)

url = f"{args.endpoint.rstrip('/')}/{args.index}"
payload = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "content": {"type": "text"},
            "embedding": {"type": "knn_vector", "dimension": args.dim}
        }
    }
}

r = requests.put(
    url,
    auth=awsauth,
    headers={"Content-Type": "application/json", "x-amz-collection-name": args.collection},
    data=json.dumps(payload),
)
print(r.status_code, r.text)
r.raise_for_status()
print("Index created or already exists.")
