# AWS Bedrock + OpenSearch Serverless RAG Indexer

이 프로젝트는 AWS Bedrock과 OpenSearch Serverless(AOSS)를 기반으로 한 Retrieval-Augmented Generation(RAG) 인덱서입니다.  
S3에 업로드된 문서를 자동으로 임베딩하고 AOSS 인덱스에 저장하여 의미 기반 검색이 가능하도록 구성되었습니다.

## 개요

아키텍처 흐름:

S3 업로드 → Lambda 트리거 → Bedrock 임베딩 생성 → AOSS 인덱스 저장

markdown
코드 복사

## 주요 기능

- S3에 업로드된 `.txt`, `.md` 파일 자동 감지 및 처리
- AWS Bedrock Titan 임베딩 모델(1536차원) 사용
- OpenSearch Serverless KNN 인덱스를 통한 벡터 검색
- Lambda 기반 실시간 문서 인덱싱 파이프라인

## 설정 및 배포

### 1. OpenSearch Serverless 컬렉션 생성

```
aws opensearchserverless create-collection \
  --name kb-rag \
  --type VECTORSEARCH \
  --region us-east-1
```
### 2. Lambda 함수 생성

```
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
### 3. 환경 변수 설정
```
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
### 4. IAM 권한
Lambda 실행 역할에 다음 권한이 필요합니다:
```
json
코드 복사
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["aoss:*"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::YOUR_BUCKET/*"
    }
  ]
}
```
### 5. AOSS 데이터 접근 정책
```
aws opensearchserverless put-access-policy \
  --name kb-rag-writer \
  --type data \
  --policy file://aoss-access-simplified.json \
  --region us-east-1
```
### 6. 인덱스 생성 및 매핑 확인
```
python recreate_index.py
python check_mapping.py
```

## 프로젝트 구조
```
├── lambda/
│   └── kb-rag-indexer/
│       ├── app.py                 # Lambda 함수 코드
│       └── requirements.txt       # Python 의존성
├── aoss-access-simplified.json    # AOSS 데이터 접근 정책
├── lambda-aoss-policy.json        # Lambda IAM 정책
├── recreate_index.py              # 인덱스 생성/재생성
├── get_full_logs.py               # CloudWatch 로그 확인
├── check_success.py               # 성공 여부 점검
└── README.md
```
## Lambda 함수 설명
lambda/kb-rag-indexer/app.py는 다음을 수행합니다:
1. S3 이벤트 수신 및 문서 경로 파싱
2. 문서 본문 읽기 (.txt, .md 지원)
3. Bedrock Titan 임베딩 모델을 사용하여 벡터 생성
4. AOSS에 문서 및 임베딩 업서트

## 코드 예시
```
def _embed(text: str):
    payload = {"inputText": text[:4000]}
    resp = bedrock.invoke_model(
        modelId=EMBEDDING_MODEL,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(payload).encode("utf-8"),
    )
    return json.loads(resp["body"].read()).get("embedding")

def _index_doc(doc_id: str, text: str, vector):
    url = f"{AOSS_ENDPOINT}/{INDEX_NAME}/_doc"
    body = {"id": doc_id, "content": text, "embedding": vector}
    requests.post(url, headers={"x-amz-collection-name": COLLECTION_NAME}, data=json.dumps(body))
```

## 모니터링 및 디버깅
- get_full_logs.py: CloudWatch 로그 스트림 전체 확인
- check_success.py: 최근 인덱싱 성공 여부 확인
- recreate_index.py: 인덱스 매핑 재생성
성공 로그 예시:

```
[DEBUG] Using embedding model: amazon.titan-embed-text-v1
[DEBUG] Response status: 201
Indexed: s3::your-bucket/docs/document.md
```

## 문제 해결
1. 403 Forbidden: IAM 권한 또는 AOSS 데이터 접근 정책 검증 필요
2. 400 Bad Request: 임베딩 차원 불일치 확인 (Titan v1 = 1536차원)
3. ValidationException: 환경변수 또는 모델 ID 확인 필요

## 사용 예시
문서 업로드 및 인덱싱
bash
코드 복사
aws s3 cp document.md s3://your-bucket/docs/ --region us-east-1
검색 (별도 구현 필요)
python
코드 복사
from opensearchpy import OpenSearch

def search(query_vector, k=5):
    response = client.search(
        index="kb-rag",
        body={
            "query": {
                "knn": {"embedding": {"vector": query_vector, "k": k}}
            }
        }
    )
    return response
## 버전 정보
- Python 3.12
- AWS Bedrock Titan Embed Text v1 (1536 dimensions)
- OpenSearch Serverless (KNN Vector Search)
- AWS Lambda (Serverless compute)
