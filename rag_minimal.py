# file: rag_minimal.py
import json, math, boto3

REGION = "us-east-1"
EMBED_MODEL = "amazon.titan-embed-text-v1"               # 방금 성공한 모델
LLM_MODEL   = "anthropic.claude-3-sonnet-20240229-v1:0"  # Claude 3 Sonnet

br = boto3.client("bedrock-runtime", region_name=REGION)

def embed(text: str):
    payload = {"inputText": text}
    res = br.invoke_model(
        modelId=EMBED_MODEL,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(payload)
    )
    return json.loads(res["body"].read().decode())["embedding"]

def cos(a, b):
    dot = sum(x*y for x, y in zip(a, b))
    na  = math.sqrt(sum(x*x for x in a))
    nb  = math.sqrt(sum(y*y for y in b))
    return dot / (na * nb + 1e-12)

# 1) 지식베이스(예시 문서)
docs = [
    ("doc1", "Agentic AI 루프는 Plan-Act-Observe로 구성된다."),
    ("doc2", "AWS Bedrock에서 RAG는 Titan 임베딩과 OpenSearch Serverless를 함께 사용한다."),
    ("doc3", "EKS 클러스터는 FastAPI와 같은 백엔드를 컨테이너로 배포하는 데 적합하다."),
    ("doc4", "SeSAC 프로젝트에서는 Petstagram을 AWS에 배포했고, ALB+EKS+RDS 구성을 사용했다."),
]

# 2) 문서 임베딩 미리 생성
kb = [(doc_id, text, embed(text)) for doc_id, text in docs]

def retrieve(query, topk=2):
    qv = embed(query)
    scored = sorted(((cos(qv, v), doc_id, text) for doc_id, text, v in kb), reverse=True)
    return scored[:topk]

def ask_with_context(question):
    hits = retrieve(question, topk=2)
    context = "\n\n".join(f"[{i+1}] {t}" for i, (_, _, t) in enumerate(hits))
    user_txt = (
        "아래 컨텍스트만 참고해서 답해줘. 모르겠으면 모른다고 말해줘.\n\n"
        f"컨텍스트:\n{context}\n\n질문: {question}"
    )

    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 400,
        "temperature": 0.3,
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": user_txt}]}
        ]
    }
    res = br.invoke_model(
        modelId=LLM_MODEL,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(payload)
    )
    return res["body"].read().decode()

if __name__ == "__main__":
    print(ask_with_context("Agentic AI 루프와 AWS에서 어떻게 구현하는지 요약해줘."))
