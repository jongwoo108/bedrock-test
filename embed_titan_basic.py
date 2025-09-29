# file: embed_titan_basic.py
import json, boto3

REGION   = "us-east-1"
MODEL_ID = "amazon.titan-embed-text-v1"   # list-foundation-models 로 확인해도 됨

br = boto3.client("bedrock-runtime", region_name=REGION)

def embed(text: str):
    payload = {"inputText": text}
    res = br.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(payload)
    )
    out = json.loads(res["body"].read().decode("utf-8"))
    return out["embedding"]  # 리스트(float[]) 반환

if __name__ == "__main__":
    v = embed("Agentic AI는 계획-행동-관찰 루프를 통해 목표를 수행한다.")
    print(len(v), "dims")  # 벡터 차원 수 출력
