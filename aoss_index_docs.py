# file: aoss_index_docs.py
import os, json, boto3, uuid
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

region = "us-east-1"
host = os.environ.get("AOSS_HOST")  # e.g. iwvt29rkcwesncyf8sw8.us-east-1.aoss.amazonaws.com
index_name = "kb-rag"

# AWS SigV4 인증
session = boto3.Session()
credentials = session.get_credentials()
auth = AWSV4SignerAuth(credentials, region, "aoss")

# OpenSearch 클라이언트
client = OpenSearch(
    hosts=[{"host": host, "port": 443}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
)

# Bedrock embed
def embed_text(text: str):
    br = boto3.client("bedrock-runtime", region_name=region)
    resp = br.invoke_model(
        modelId="amazon.titan-embed-text-v1",
        contentType="application/json",
        accept="application/json",
        body=json.dumps({"inputText": text})
    )
    out = json.loads(resp["body"].read())
    return out["embedding"]

def index_documents(docs):
    for text in docs:
        vec = embed_text(text)
        body = {
            "text": text,
            "embedding": vec
        }
        resp = client.index(index=index_name, body=body)
        print(f"Indexed text='{text[:20]}...', result={resp['result']}")

if __name__ == "__main__":
    # 데모용 문서
    documents = [
        "Agentic AI 루프는 관찰, 계획, 실행, 학습 단계를 반복하며 자율적으로 문제를 해결한다.",
        "AWS에서 Agentic AI를 구현할 때는 Bedrock, Lambda, Step Functions, S3, OpenSearch Serverless 등을 조합할 수 있다.",
        "RAG 파이프라인은 S3에서 데이터를 불러와 벡터화한 후 OpenSearch에 저장하고, 질의 시 Bedrock 모델과 결합하여 답변을 생성한다."
    ]
    index_documents(documents)
