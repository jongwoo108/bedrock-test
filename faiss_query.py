# file: faiss_query.py
import json, math, argparse
import numpy as np
import faiss, boto3

REGION = "us-east-1"
EMBED_MODEL = "amazon.titan-embed-text-v1"
LLM_MODEL   = "anthropic.claude-3-sonnet-20240229-v1:0"

br = boto3.client("bedrock-runtime", region_name=REGION)

def _norm(v: np.ndarray) -> np.ndarray:
    return v / (np.linalg.norm(v) + 1e-12)

def embed(text: str) -> np.ndarray:
    payload = {"inputText": text}
    res = br.invoke_model(
        modelId=EMBED_MODEL,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(payload)
    )
    v = np.array(json.loads(res["body"].read().decode())["embedding"], dtype="float32")
    return _norm(v)

def load_index():
    index = faiss.read_index("kb.index")
    docs  = json.load(open("kb_meta.json", encoding="utf-8"))
    return index, docs

def retrieve(index, docs, query: str, k: int, min_score: float):
    qv = embed(query).reshape(1, -1)
    # FAISS IndexFlatIP 이므로 입력도 정규화된 벡터여야 코사인 유사도와 동일
    D, I = index.search(qv, k)
    out = []
    for score, idx in zip(D[0].tolist(), I[0].tolist()):
        if idx == -1:  # 검색 결과 부족 시
            continue
        if score < min_score:
            continue
        doc_id, text = docs[idx][0], docs[idx][1]
        out.append({"score": float(score), "doc_id": doc_id, "text": text})
    return out

def ask_with_context(question: str, contexts: list[dict]) -> dict:
    ctx_block = "\n\n".join(f"[{i+1}] {c['text']}" for i, c in enumerate(contexts))
    user_txt = (
        "아래 컨텍스트만 참고해서 질문에 답해줘. "
        "컨텍스트에 없으면 '모르겠습니다'라고 답해줘.\n\n"
        f"컨텍스트:\n{ctx_block}\n\n질문: {question}"
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
    raw = json.loads(res["body"].read().decode("utf-8"))
    # Claude 3 응답 파싱
    text = ""
    if isinstance(raw, dict) and "content" in raw and raw["content"]:
        parts = raw["content"]
        # content: [{"type":"text","text":"..."}]
        for p in parts:
            if p.get("type") == "text":
                text += p.get("text", "")
    usage = raw.get("usage", {})
    return {
        "answer": text.strip(),
        "contexts": contexts,
        "usage": {"input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens")}
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="*", help="질문 문장")
    ap.add_argument("--k", type=int, default=3, help="Top-k 문맥 개수 (default: 3)")
    ap.add_argument("--min-score", type=float, default=0.15, help="코사인 유사도 임계값 (0~1, default: 0.15)")
    args = ap.parse_args()

    question = " ".join(args.question) if args.question else "Agentic AI 루프와 AWS 구현 요소를 요약해줘."
    index, docs = load_index()
    hits = retrieve(index, docs, question, k=args.k, min_score=args.min_score)

    # 컨텍스트가 없을 때도 JSON으로 응답
    if not hits:
        print(json.dumps({"answer": "관련 컨텍스트가 없어 답변할 수 없습니다.",
                          "contexts": [], "usage": None}, ensure_ascii=False))
        return

    result = ask_with_context(question, hits)
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
