# Bedrock RAG Minimal (Claude 3 Sonnet + Titan Embeddings + FAISS)

간단한 RAG 실습:
- **LLM**: `anthropic.claude-3-sonnet-20240229-v1:0`
- **Embedding**: `amazon.titan-embed-text-v1` (1536d)
- **Vector DB**: FAISS (IndexFlatIP, cosine)

## Prerequisites
- Python 3.10+
- AWS CLI 로그인 완료 (`aws sts get-caller-identity`)
- Bedrock 모델 액세스: Claude 3 Sonnet, Titan Embeddings G1 - Text

## Setup
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 인덱스 생성 (faiss_build.py 실행)
python faiss_build.py

# 질의 실행 (Top-k 검색)
python faiss_query.py --k 4 --min-score 0.2 "Agentic AI 루프와 AWS에서 구현 요소를 요약해줘."
```


## Project Structure
```
bedrock-rag-minimal/
 ├─ call_claude_basic.py    # Claude 3 Sonnet 기본 호출
 ├─ embed_titan_basic.py    # Titan Embeddings 벡터화 예제
 ├─ faiss_build.py          # 샘플 문서 -> FAISS 인덱스 저장
 ├─ faiss_query.py          # RAG 질의 (검색 + LLM)
 ├─ rag_minimal.py          # End-to-End 간단 RAG 파이프라인
 ├─ requirements.txt
 └─ README.md
```

## Sample Output
```json
 {
  "answer": "Agentic AI는 Plan-Act-Observe 루프를 따르며, AWS에서는 다음과 같은 요소들을 활용할 수 있습니다...",
  "contexts": [
    {"score": 0.75, "doc_id": "doc1", "text": "Agentic AI는 Plan-Act-Observe 루프를 따른다."},
    {"score": 0.71, "doc_id": "doc2", "text": "AWS RAG는 Titan Embeddings와 OpenSearch Serverless를 함께 사용하면 좋다."}
  ]
}
```

## License
MIT
## References
- https://aws.amazon.com/ko/bedrock/
- https://github.com/facebookresearch/faiss
