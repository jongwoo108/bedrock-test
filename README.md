<<<<<<< HEAD
# AWS Bedrock + OpenSearch Serverless RAG Indexer

AWS Bedrock과 OpenSearch Serverless(AOSS)를 사용한 간단한 RAG(Retrieval-Augmented Generation) 인덱서입니다.

## 📋 개요
=======
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
>>>>>>> f3d27d0bc4bd5374fd85c77fcde4055697621c6a

이 프로젝트는 S3에 업로드된 문서를 자동으로 임베딩하여 OpenSearch Serverless 인덱스에 저장하는 Lambda 기반 RAG 인덱서입니다.

### 🏗️ 아키텍처

```
S3 업로드 → Lambda 트리거 → Bedrock 임베딩 생성 → AOSS 인덱스 저장
```

### ✨ 주요 기능

- **자동 문서 처리**: S3에 업로드된 `.txt`, `.md` 파일 자동 감지
- **임베딩 생성**: AWS Bedrock Titan 모델을 사용한 1536차원 임베딩
- **벡터 검색**: OpenSearch Serverless KNN 인덱스를 통한 의미 기반 검색
- **실시간 처리**: S3 이벤트 기반 실시간 문서 인덱싱

## 🚀 설정 및 배포

### 1. AWS 리소스 생성

#### OpenSearch Serverless 컬렉션
```bash
# 컬렉션 생성 (예시)
aws opensearchserverless create-collection \
  --name kb-rag \
  --type SEARCH \
  --region us-east-1
```

<<<<<<< HEAD
#### Lambda 함수 생성
```bash
# Lambda 함수 배포
cd lambda/kb-rag-indexer
zip -r ../kb-rag-indexer.zip *
aws lambda create-function \
  --function-name kb-rag-indexer \
  --runtime python3.12 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/kb-rag-indexer-role \
  --handler app.lambda_handler \
  --zip-file fileb://../kb-rag-indexer.zip \
  --region us-east-1
```

### 2. 환경변수 설정

```bash
aws lambda update-function-configuration \
  --function-name kb-rag-indexer \
  --region us-east-1 \
  --environment "Variables={
    AOSS_ENDPOINT=https://YOUR_COLLECTION_ID.us-east-1.aoss.amazonaws.com,
    COLLECTION_NAME=kb-rag,
    INDEX_NAME=kb-rag,
    EMBEDDING_MODEL=amazon.titan-embed-text-v1
  }"
```

### 3. IAM 권한 설정

Lambda 실행 역할에 다음 권한이 필요합니다:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "aoss:APIAccessAll"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": "arn:aws:s3:::YOUR_BUCKET/*"
        }
    ]
=======
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
>>>>>>> f3d27d0bc4bd5374fd85c77fcde4055697621c6a
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

### 4. AOSS 액세스 정책

```bash
# 데이터 액세스 정책 적용
aws opensearchserverless put-access-policy \
  --name kb-rag-writer \
  --type data \
  --policy file://aoss-access-simplified.json \
  --region us-east-1
```

### 5. 인덱스 생성

```bash
# 인덱스 생성 및 매핑 설정
python recreate_index.py
```

## 📁 프로젝트 구조

```
├── lambda/
│   └── kb-rag-indexer/
│       ├── app.py                 # 메인 Lambda 함수
│       └── requirements.txt       # Python 의존성
├── aoss-access-simplified.json    # AOSS 데이터 액세스 정책
├── lambda-aoss-policy.json        # Lambda IAM 정책
├── recreate_index.py              # 인덱스 생성/재생성 도구
├── get_full_logs.py              # CloudWatch 로그 확인 도구
├── check_success.py              # 성공 여부 확인 도구
└── README.md
```

## 🔧 주요 구성 요소

### Lambda 함수 (`lambda/kb-rag-indexer/app.py`)

- **S3 이벤트 처리**: S3 업로드 이벤트 수신 및 처리
- **문서 읽기**: S3에서 텍스트/마크다운 파일 읽기
- **임베딩 생성**: Bedrock Titan 모델을 사용한 벡터 임베딩
- **인덱스 저장**: AOSS에 문서와 임베딩 저장

### 핵심 기능

```python
def _embed(text: str):
    """Bedrock Titan을 사용한 임베딩 생성"""
    payload = {"inputText": text[:4000]}
    resp = bedrock.invoke_model(
        modelId=EMBEDDING_MODEL,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(payload).encode("utf-8"),
    )
    # ... 임베딩 반환

def _index_doc(doc_id: str, text: str, vector):
    """AOSS에 문서 인덱싱"""
    url = f"{AOSS_ENDPOINT}/{INDEX_NAME}/_doc"
    body = {"id": doc_id, "content": text, "embedding": vector}
    # ... POST 요청으로 인덱싱
```

## 📊 모니터링

### CloudWatch 로그 확인
```bash
# 성공 여부 확인
python check_success.py

# 전체 로그 확인
python get_full_logs.py
```

### 성공 로그 예시
```
[DEBUG] Using embedding model: amazon.titan-embed-text-v1
[DEBUG] Embedding dimension: 1536
[DEBUG] Response status: 201
Indexed: s3::your-bucket/docs/document.md
```

## 🚨 문제 해결

### 일반적인 문제들

1. **403 Forbidden**: IAM 권한 또는 AOSS 액세스 정책 확인
2. **400 Bad Request**: 임베딩 차원 불일치 확인
3. **ValidationException**: 모델 ID 또는 환경변수 확인

### 디버깅 도구

- `get_full_logs.py`: CloudWatch 로그 전체 확인
- `check_success.py`: 성공/실패 요약 확인
- `recreate_index.py`: 인덱스 재생성

## 📈 사용법

### 문서 업로드
```bash
# 문서를 S3에 업로드하면 자동으로 인덱싱됨
aws s3 cp document.md s3://your-bucket/docs/ --region us-east-1
```

### 검색 (별도 구현 필요)
```python
# 검색 예시 (rag_answer.py 참고)
from opensearchpy import OpenSearch

def search(query_vector, k=5):
    response = client.search(
        index="kb-rag",
        body={
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_vector,
                        "k": k
                    }
                }
            }
        }
    )
    return response
```

## 🏷️ 버전 정보

- **Python**: 3.12
- **AWS Bedrock**: Titan Embed Text v1 (1536 dimensions)
- **OpenSearch Serverless**: KNN Vector Search
- **AWS Lambda**: Serverless compute

## 📝 라이센스

MIT License

## 🤝 기여

Issues와 Pull Requests를 환영합니다!

---

**🎉 완전히 동작하는 RAG 인덱서입니다!**

S3 → Lambda → Bedrock → AOSS 파이프라인이 403 오류 없이 완벽하게 작동합니다.