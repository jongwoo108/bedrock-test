import json, boto3, os

REGION   = os.getenv("AWS_REGION", "us-east-1")
LLM_ID   = os.getenv("BEDROCK_LLM_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

br = boto3.client("bedrock-runtime", region_name=REGION)

SYSTEM = (
    "You are a planning assistant. Given a user question, produce a concise plan "
    "for how to answer it. Decide whether retrieval is needed, and if so, propose 1-3 "
    "search queries. Respond as strict JSON: "
    '{"plan":"...", "need_retrieval": true|false, "queries": ["q1","q2"]}'
)

def plan(question: str) -> dict:
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 400,
        "temperature": 0.2,
        "messages": [
            {"role": "user", "content": [
                {"type": "text", "text": f"{SYSTEM}\n\nUser question: {question}"}
            ]}
        ]
    }
    res = br.invoke_model(modelId=LLM_ID,
                          contentType="application/json",
                          accept="application/json",
                          body=json.dumps(payload))
    out = json.loads(res["body"].read().decode("utf-8"))
    # Out format from Bedrock Claude: {"content":[{"type":"text","text":"..."}], ...}
    txt = out["content"][0]["text"]
    try:
        return json.loads(txt)
    except Exception:
        # fallback: wrap raw text
        return {"plan": txt, "need_retrieval": True, "queries": []}
