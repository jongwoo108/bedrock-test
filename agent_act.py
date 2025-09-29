import json, os, boto3, faiss
import numpy as np
from typing import List, Tuple

REGION   = os.getenv("AWS_REGION", "us-east-1")
LLM_ID   = os.getenv("BEDROCK_LLM_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

br = boto3.client("bedrock-runtime", region_name=REGION)

def load_index(idx_path="kb.index", meta_path="kb_meta.json"):
    index = faiss.read_index(idx_path)
    raw = json.load(open(meta_path, encoding="utf-8"))
    docs = []
    for item in raw:
        if isinstance(item, dict):
            # 이미 {"doc_id":..,"text":..} 형태이면 그대로
            docs.append(item)
        else:
            # ("doc1","text") 또는 ["doc1","text"] 형태 → dict로 정규화
            doc_id, text = item[0], item[1]
            docs.append({"doc_id": doc_id, "text": text})
    return index, docs

def search(index, docs, query_vec: List[float], k=4, min_score=0.2) -> List[Tuple[float, dict]]:
    x = np.asarray(query_vec, dtype="float32")[None, :]
    faiss.normalize_L2(x)  # IndexFlatIP를 cosine처럼 쓰려면 정규화
    assert x.shape[1] == index.d, f"dim mismatch: vec={x.shape[1]}, index={index.d}"
    D, I = index.search(x, k)
    hits = []
    for score, idx in zip(D[0], I[0]):
        if idx == -1:
            continue
        if float(score) >= min_score:
            hits.append((float(score), docs[idx]))  # docs[idx]는 이제 dict
    return hits

def answer_with_context(question: str, retrieved: List[Tuple[float, dict]]) -> str:
    ctx = "\n\n".join([f"[{i+1}] score={s:.3f} | {d['text']}" for i,(s,d) in enumerate(retrieved)])
    prompt = (
        "You are a precise assistant. Answer the question ONLY using the context. "
        "If the context is insufficient, say so explicitly and propose what extra info is needed.\n\n"
        f"Context:\n{ctx}\n\nQuestion: {question}\nAnswer in Korean."
    )
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "temperature": 0.3,
        "messages": [{"role":"user","content":[{"type":"text","text":prompt}]}]
    }
    res = br.invoke_model(modelId=LLM_ID,
                          contentType="application/json",
                          accept="application/json",
                          body=json.dumps(payload))
    out = json.loads(res["body"].read().decode("utf-8"))
    return out["content"][0]["text"]
