import json, boto3, os

REGION   = os.getenv("AWS_REGION", "us-east-1")
LLM_ID   = os.getenv("BEDROCK_LLM_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

br = boto3.client("bedrock-runtime", region_name=REGION)

EVAL_INST = (
    "Evaluate if the provided answer sufficiently addresses the user's question. "
    "Output strict JSON: "
    '{"sufficient": true|false, "reason":"...", "followup_queries":["kw1","kw2"]}'
)

def observe(question: str, answer: str) -> dict:
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 300,
        "temperature": 0.2,
        "messages": [{"role":"user","content":[{"type":"text","text":
            f"{EVAL_INST}\n\nQuestion: {question}\n\nAnswer:\n{answer}"}]}]
    }
    res = br.invoke_model(modelId=LLM_ID,
                          contentType="application/json",
                          accept="application/json",
                          body=json.dumps(payload))
    out = json.loads(res["body"].read().decode("utf-8"))
    txt = out["content"][0]["text"]
    try:
        return json.loads(txt)
    except Exception:
        return {"sufficient": False, "reason": txt, "followup_queries": []}
