# file: faiss_build.py
import json, numpy as np, faiss, boto3

REGION = "us-east-1"
EMBED_MODEL = "amazon.titan-embed-text-v1"
br = boto3.client("bedrock-runtime", region_name=REGION)

def embed(t:str):
    body={"inputText":t}
    r=br.invoke_model(modelId=EMBED_MODEL,contentType="application/json",accept="application/json",body=json.dumps(body))
    return np.array(json.loads(r["body"].read().decode())["embedding"], dtype="float32")

# ▶ 여기에 본인 문서들 계속 추가
docs = [
  ("doc1","Agentic AI는 Plan-Act-Observe 루프를 따른다."),
  ("doc2","AWS RAG는 Titan Embeddings와 OpenSearch Serverless를 함께 사용하면 좋다."),
  ("doc3","EKS는 LLM 서빙/에이전트 마이크로서비스 운영에 적합하다."),
]

vecs = [embed(t) for _,t in docs]
dim  = vecs[0].shape[0]
xb   = np.vstack(vecs)

# 코사인 유사도 = 내적용 → 벡터 정규화
xb = xb / (np.linalg.norm(xb, axis=1, keepdims=True) + 1e-12)

index = faiss.IndexFlatIP(dim)     # 내적
index.add(xb)

faiss.write_index(index, "kb.index")
with open("kb_meta.json","w",encoding="utf-8") as f:
    json.dump(docs, f, ensure_ascii=False)
print("saved: kb.index, kb_meta.json")
