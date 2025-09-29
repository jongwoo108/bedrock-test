# file: call_claude_basic.py
import json, boto3

REGION = "us-east-1"
# list-inference-profiles 에서 확인한 프로파일 ARN 또는 ID
MODEL_ID = "arn:aws:bedrock:us-east-1:348823728620:inference-profile/us.anthropic.claude-3-sonnet-20240229-v1:0"
# MODEL_ID = "us.anthropic.claude-3-sonnet-20240229-v1:0"  # ← ID만 써도 됨

br = boto3.client("bedrock-runtime", region_name=REGION)

payload = {
    "anthropic_version": "bedrock-2023-05-31",  # Claude 3 계열 필수
    "max_tokens": 300,
    "temperature": 0.5,
    "messages": [
        {
            "role": "user",
            "content": [{"type": "text", "text": "Agentic AI의 plan→act→observe 루프를 3줄로 설명해줘."}]
        }
    ]
}

res = br.invoke_model(
    modelId=MODEL_ID,                        # ← 여기!
    contentType="application/json",
    accept="application/json",
    body=json.dumps(payload)
)

print(res["body"].read().decode("utf-8"))
