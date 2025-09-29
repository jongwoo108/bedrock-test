# file: aoss_init_index.py
import os
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import boto3

REGION = "us-east-1"
SERVICE = "aoss"
HOST = os.environ["AOSS_HOST"]  # 예: lgn08...us-east-1.aoss.amazonaws.com
INDEX = "kb-rag"
DIM = 1536  # Titan text embedding 차원

sess = boto3.Session()
auth = AWSV4SignerAuth(sess.get_credentials(), REGION, SERVICE)

client = OpenSearch(
    hosts=[{"host": HOST, "port": 443}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
)

mapping = {
    "settings": {
        "index": {
            "knn": True,
            "knn.algo_param.ef_search": 100
        }
    },
    "mappings": {
        "properties": {
            "doc_id": {"type": "keyword"},
            "text":   {"type": "text"},
            "embedding": {
                "type": "knn_vector",
                "dimension": DIM,
                "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",
                    "engine": "nmslib"   # ← Serverless는 nmslib 권장/지원
                }
            }
        }
    }
}

if not client.indices.exists(index=INDEX):
    resp = client.indices.create(index=INDEX, body=mapping)
    print("Index created:", resp)
else:
    print(f"Index '{INDEX}' already exists")
