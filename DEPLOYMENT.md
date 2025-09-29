# 배포 가이드

이 문서는 RAG 인덱서를 처음부터 배포하는 단계별 가이드입니다.

## 🚀 배포 순서

### 1. OpenSearch Serverless 컬렉션 생성

```bash
# 1-1. 암호화 정책 생성
aws opensearchserverless create-security-policy \
  --name kb-rag-encryption \
  --type encryption \
  --policy '[{
    "Rules": [{
      "ResourceType": "collection",
      "Resource": ["collection/kb-rag"]
    }],
    "AWSOwnedKey": true
  }]' \
  --region us-east-1

# 1-2. 네트워크 정책 생성
aws opensearchserverless create-security-policy \
  --name kb-rag-network \
  --type network \
  --policy '[{
    "Description": "Public access for kb-rag collection",
    "Rules": [{
      "ResourceType": "collection",
      "Resource": ["collection/kb-rag"]
    }],
    "AllowFromPublic": true
  }]' \
  --region us-east-1

# 1-3. 컬렉션 생성
aws opensearchserverless create-collection \
  --name kb-rag \
  --type SEARCH \
  --description "RAG knowledge base collection" \
  --region us-east-1
```

### 2. Lambda 실행 역할 생성

```bash
# 2-1. 신뢰 정책 생성
cat > lambda-trust-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

# 2-2. IAM 역할 생성
aws iam create-role \
  --role-name kb-rag-indexer-role \
  --assume-role-policy-document file://lambda-trust-policy.json \
  --region us-east-1

# 2-3. 기본 Lambda 실행 정책 연결
aws iam attach-role-policy \
  --role-name kb-rag-indexer-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
  --region us-east-1

# 2-4. AOSS 및 Bedrock 액세스 정책 추가
aws iam put-role-policy \
  --role-name kb-rag-indexer-role \
  --policy-name kb-rag-aoss-access \
  --policy-document file://lambda-aoss-policy.json \
  --region us-east-1
```

### 3. AOSS 데이터 액세스 정책 설정

```bash
# 3-1. 계정 ID 확인
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# 3-2. 데이터 액세스 정책 생성
aws opensearchserverless create-access-policy \
  --name kb-rag-writer \
  --type data \
  --policy "[{
    \"Description\": \"Lambda indexer access to kb-rag collection\",
    \"Rules\": [{
      \"ResourceType\": \"index\",
      \"Resource\": [\"index/kb-rag/*\"],
      \"Permission\": [
        \"aoss:DescribeIndex\",
        \"aoss:ReadDocument\",
        \"aoss:WriteDocument\",
        \"aoss:CreateIndex\",
        \"aoss:UpdateIndex\"
      ]
    }, {
      \"ResourceType\": \"collection\",
      \"Resource\": [\"collection/kb-rag\"],
      \"Permission\": [\"aoss:DescribeCollectionItems\"]
    }],
    \"Principal\": [\"arn:aws:iam::${ACCOUNT_ID}:role/kb-rag-indexer-role\"]
  }]" \
  --region us-east-1
```

### 4. Lambda 함수 생성 및 배포

```bash
# 4-1. Lambda 패키지 생성
cd lambda/kb-rag-indexer
pip install -r requirements.txt -t .
zip -r ../../kb-rag-indexer.zip .
cd ../..

# 4-2. Lambda 함수 생성
aws lambda create-function \
  --function-name kb-rag-indexer \
  --runtime python3.12 \
  --role arn:aws:iam::${ACCOUNT_ID}:role/kb-rag-indexer-role \
  --handler app.lambda_handler \
  --zip-file fileb://kb-rag-indexer.zip \
  --timeout 30 \
  --memory-size 512 \
  --region us-east-1

# 4-3. 환경변수 설정 (컬렉션 엔드포인트는 실제 값으로 변경)
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

### 5. OpenSearch 인덱스 생성

```bash
# 5-1. 인덱스 생성 스크립트 실행
python recreate_index.py
```

### 6. S3 버킷 및 트리거 설정

```bash
# 6-1. S3 버킷 생성 (이미 있다면 생략)
aws s3 mb s3://your-rag-bucket --region us-east-1

# 6-2. Lambda 함수에 S3 호출 권한 부여
aws lambda add-permission \
  --function-name kb-rag-indexer \
  --principal s3.amazonaws.com \
  --action lambda:InvokeFunction \
  --source-arn arn:aws:s3:::your-rag-bucket \
  --statement-id s3-trigger \
  --region us-east-1

# 6-3. S3 버킷 알림 설정
aws s3api put-bucket-notification-configuration \
  --bucket your-rag-bucket \
  --notification-configuration file://s3-notification.json \
  --region us-east-1
```

### 7. 테스트

```bash
# 7-1. 테스트 문서 업로드
echo "This is a test document for RAG indexing." > test-document.md
aws s3 cp test-document.md s3://your-rag-bucket/docs/ --region us-east-1

# 7-2. 로그 확인 (15초 후)
sleep 15
python get_full_logs.py

# 7-3. 성공 확인
python check_success.py
```

## 🔧 설정 파일 예시

### s3-notification.json
```json
{
  "LambdaFunctionConfigurations": [
    {
      "Id": "kb-rag-indexer-on-put",
      "LambdaFunctionArn": "arn:aws:lambda:us-east-1:YOUR_ACCOUNT:function:kb-rag-indexer",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [
            {
              "Name": "prefix",
              "Value": "docs/"
            }
          ]
        }
      }
    }
  ]
}
```

## 🚨 문제 해결

### 자주 발생하는 오류들

1. **403 Forbidden**
   - IAM 역할 권한 확인
   - AOSS 데이터 액세스 정책 확인
   - Principal ARN 정확성 확인

2. **400 Bad Request**
   - 임베딩 차원과 인덱스 매핑 일치 확인
   - 모델 ID 유효성 확인

3. **ValidationException**
   - 환경변수 설정 확인
   - Bedrock 모델 접근 권한 확인

### 디버깅 명령어

```bash
# CloudWatch 로그 확인
python get_full_logs.py

# 성공/실패 요약
python check_success.py

# 인덱스 상태 확인
python list_indices.py

# 인덱스 재생성
python recreate_index.py
```

## 📊 모니터링 설정

### CloudWatch 대시보드 생성 (선택사항)

```bash
# Lambda 함수 메트릭 모니터링
aws logs create-log-group \
  --log-group-name /aws/lambda/kb-rag-indexer \
  --region us-east-1

# 메트릭 필터 생성 (성공/실패 카운트)
aws logs put-metric-filter \
  --log-group-name /aws/lambda/kb-rag-indexer \
  --filter-name IndexingSuccess \
  --filter-pattern "[timestamp, request_id, level=\"Indexed:\"]" \
  --metric-transformations \
    metricName=IndexingSuccess,metricNamespace=RAG/Indexer,metricValue=1 \
  --region us-east-1
```

이제 완전히 동작하는 RAG 인덱서가 배포되었습니다! 🎉
