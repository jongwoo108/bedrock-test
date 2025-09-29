# Bedrock Test — RAG + Agentic (Claude 3 Sonnet × Titan Embeddings × AOSS)
간단한 RAG/Agentic 실습 프로젝트입니다.
- **LLM**: `anthropic.claude-3-sonnet-20240229-v1:0`
- **Embedding**: `amazon.titan-embed-text-v1` (1536d)
- **Vector Store**: **OpenSearch Serverless (VECTORSEARCH)** + k-NN (HNSW, cosinesimil)
- **Agentic Loop**: plan → act → observe (샘플 스텝 실행 스크립트 포함)

## Prerequisites
- Python 3.10+
- AWS CLI 로그인 완료 (`aws sts get-caller-identity`)
- Bedrock 모델 액세스: Claude 3 Sonnet, Titan Embeddings G1 - Text
- 리전: us-east-1

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
bedrock-test/
 ├─ agent_plan.py          # plan 단계(검색 전략 등 초안)
 ├─ agent_act.py           # act 단계(검색 실행)
 ├─ agent_observe.py       # observe 단계(결과 요약/다음 액션)
 ├─ rag_agentic.py         # plan→act→observe 에이전트 드라이버
 ├─ rag_answer.py          # AOSS 검색 + Claude로 최종 답변
 ├─ aoss_init_index.py     # AOSS 인덱스 생성 (VECTORSEARCH 매핑)
 ├─ aoss_index_docs.py     # 샘플 문서 임베딩→AOSS 인덱싱
 ├─ aoss_query.py          # 임베딩 쿼리로 AOSS vector search
 ├─ quick_aoss_ping.py     # AOSS 연결 점검
 ├─ check_mapping.py       # 인덱스 매핑 확인
 ├─ check_docs.py          # 색인 문서 샘플 조회
 ├─ call_claude_basic.py   # Bedrock LLM 호출 예제
 ├─ embed_titan_basic.py   # 임베딩 생성 예제
 ├─ requirements.txt
 └─ README.md
```

## OpenSearch Serverless (AOSS) 준비
1. 컬렉션 생성 (VECTORSEARCH 타입)
```
aws opensearchserverless create-collection --name kb-rag --type VECTORSEARCH --region us-east-1
aws opensearchserverless list-collections --region us-east-1
```
2. 엔드포인트 확인 & 환경변수 설정
```
aws opensearchserverless batch-get-collection --ids <COLLECTION_ID> --region us-east-1
REM collectionEndpoint에서 호스트만 추출해 설정 (https:// 제외!)
set AOSS_HOST=<collectionId>.us-east-1.aoss.amazonaws.com
```   
3. 네트워크/데이터 접근 정책 (데모용 퍼블릭 허용)
```
aws opensearchserverless create-security-policy ^
  --type network --name kb-rag-network ^
  --policy "[{\"Rules\":[{\"ResourceType\":\"collection\",\"Resource\":[\"collection/kb-rag\"]}],\"AllowFromPublic\":true}]" ^
  --region us-east-1

for /f "tokens=*" %a in ('aws sts get-caller-identity --query Arn --output text') do @set ME=%a

aws opensearchserverless create-access-policy ^
  --type data --name kb-rag-data ^
  --policy "[{\"Description\":\"kb-rag data access\",\"Rules\":[{\"ResourceType\":\"index\",\"Resource\":[\"index/kb-rag/*\"],\"Permission\":[\"aoss:*\"]},{\"ResourceType\":\"collection\",\"Resource\":[\"collection/kb-rag\"],\"Permission\":[\"aoss:*\"]}],\"Principal\":[\"%ME%\"]}]" ^
  --region us-east-1
```
4. 인덱스 생성 (매핑 포함)
```
python aoss_init_index.py
```
성공 시: Index created: {... 'index': 'kb-rag'}
참고: 인덱스 매핑 확인
python check_mapping.py

## 샘플 데이터 색인 & 질의
1. 샘플 문서 색인
```
python aoss_index_docs.py
```
예)
Indexed text='AWS에서 Agentic AI를 구현...', result=created

2. 벡터 검색 (AOSS)
```
python aoss_query.py "Agentic AI 루프와 AWS에서 구현 요소를 요약해줘." --k 3 --min-score 0.2
```
예시 출력(요약):
```
{
  "query": "...",
  "results": [
    {"score": 0.93, "doc_id": "....", "text": "AWS에서 Agentic AI를 구현할 때는 ..."},
    {"score": 0.90, "doc_id": "....", "text": "Agentic AI 루프는 관찰, 계획, ..."},
    {"score": 0.79, "doc_id": "....", "text": "RAG 파이프라인은 S3에서 데이터를 ..."}
  ]
}
```
3. LLM과 결합한 최종 답변
```
python rag_answer.py "Agentic AI 루프와 AWS에서 구현 요소를 요약해줘." --k 3 --min-score 0.2
```
예시:
```
{
  "answer": "AWS에서 Agentic AI 루프를 구현하려면 Bedrock, Lambda, Step Functions, S3, OpenSearch Serverless를 활용할 수 있다. ... [1][2][3]",
  "contexts": ["...", "...", "..."]
}
```

## Agentic Loop (plan → act → observe)
- agent_plan.py : 쿼리 의도 분석/검색전략 수립(샘플)
- agent_act.py : 실제 검색 실행(AOSS)
- agent_observe.py : 결과 관찰/요약/다음 질문 제안
- rag_agentic.py : 위 스텝을 순차 실행하는 드라이버

실행:
```
python rag_agentic.py "Agentic AI 루프와 AWS에서 구현 요소를 요약해줘." --k 4 --min-score 0.2
```

## 유틸
- 연결 점검: python quick_aoss_ping.py
- 도큐먼트 확인: python check_docs.py
- Bedrock 베이직 호출: python call_claude_basic.py, python embed_titan_basic.py

## Troubleshooting
- 403 AuthorizationException
  데이터/네트워크 정책에 현재 IAM 사용자 ARN이 포함돼 있는지 확인하세요.
  aws sts get-caller-identity --query Arn --output text로 ARN 확인 후, 정책 재적용.
- 400 illegal_argument_exception (VECTORSEARCH)
  컬렉션 타입이 VECTORSEARCH인지 확인. SEARCH 타입은 knn/VectorSearch 미지원.
- AOSS_HOST 값 오류
  set AOSS_HOST 에는 호스트만 넣습니다. https:// 포함하면 안 됨.
  예) set AOSS_HOST=iwvt29rkcwesncyf8sw8.us-east-1.aoss.amazonaws.com

## Roadmap
- [ ] 문서 업서터(동일 doc_id 업데이트)
- [ ] 배치 인덱싱(Bulk API)
- [ ] S3 → Lambda → AOSS 파이프라인
- [ ] LangChain 통합(Retriever/Agent)
- [ ] Step Functions로 Agentic 워크플로 구성

## License
MIT
## References
- https://aws.amazon.com/ko/bedrock/
- https://github.com/facebookresearch/faiss
