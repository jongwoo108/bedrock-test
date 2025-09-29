# file: rag_agentic.py
import argparse
from agent_plan import plan
from agent_act import load_index, search, answer_with_context
from agent_observe import observe
from embed_titan_basic import embed  # 이미 만든 임베딩 함수 재사용

MAX_ITERS = 3

def run_agentic_qa(question: str, k=4, min_score=0.2):
    index, docs = load_index()
    it = 0
    history = []

    while it < MAX_ITERS:
        it += 1
        p = plan(question)
        history.append(("plan", p))

        # 임베딩: Plan 단계에서 제안된 쿼리 있으면 우선 사용, 없으면 사용자 질문을 벡터화
        queries = p.get("queries") or [question]
        retrieved = []
        for q in queries:
            vec = embed(q)  # returns List[float] length 1536
            retrieved += search(index, docs, vec, k=k, min_score=min_score)

        # 중복 제거(문서 ID 기준)
        seen = set()
        uniq = []
        for s, d in sorted(retrieved, key=lambda x: -x[0]):
            key = d.get("doc_id") or d.get("id") or d.get("text")[:32]
            if key in seen: 
                continue
            seen.add(key)
            uniq.append((s, d))
        retrieved = uniq[:k]

        answer = answer_with_context(question, retrieved)
        history.append(("answer", answer))

        obs = observe(question, answer)
        history.append(("observe", obs))

        if obs.get("sufficient", False):
            return {"answer": answer, "iterations": it, "history": history}

        # 부족하면 추가 질의로 한 번 더
        extra = obs.get("followup_queries") or []
        if extra:
            # 다음 루프에서 참조하도록 질문 자체를 보강
            question = f"{question}\n(추가 검색 키워드: {', '.join(extra)})"
        else:
            # 더 할 게 없으면 종료
            return {"answer": answer, "iterations": it, "history": history}

    return {"answer": history[-2][1] if history else "", "iterations": it, "history": history}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("question", type=str, help="질문")
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--min-score", type=float, default=0.2)
    args = ap.parse_args()

    result = run_agentic_qa(args.question, k=args.k, min_score=args.min_score)
    print("\n=== FINAL ANSWER ===\n")
    print(result["answer"])
    print("\n--- meta ---")
    print(f"iterations={result['iterations']}")
