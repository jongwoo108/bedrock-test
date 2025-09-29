# AWS Bedrock + OpenSearch Serverless RAG Indexer

AWS Bedrock과 OpenSearch Serverless(AOSS)를 사용한 간단한 RAG(Retrieval-Augmented Generation) 인덱서입니다.

## 📋 개요

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
}
```

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