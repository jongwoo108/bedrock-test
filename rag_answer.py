# file: rag_answer.py
import os, json, argparse, boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

REGION="us-east-1"; SERVICE="aoss"; INDEX="kb-rag"; HOST=os.environ["AOSS_HOST"]

auth = AWSV4SignerAuth(boto3.Session().get_credentials(), REGION, SERVICE)
os_client = OpenSearch(
    hosts=[{"host": HOST, "port": 443}],
    http_auth=auth, use_ssl=True, verify_certs=True,
    connection_class=RequestsHttpConnection,
)

def embed_text(text:str):
    br = boto3.client("bedrock-runtime", region_name=REGION)
    r = br.invoke_model(
        modelId="amazon.titan-embed-text-v1",
        contentType="application/json", accept="application/json",
        body=json.dumps({"inputText": text})
    )
    data = json.loads(r["body"].read()); emb = data["embedding"]
    if isinstance(emb, str): emb = json.loads(emb)
    return [float(x) for x in emb]

def search(vec, k=4, num_candidates=100):
    body = {
        "size": k,
        "query": {
            "knn": {
                "field":"embedding",
                "query_vector": vec,
                "k": k,
                "num_candidates": num_candidates
            }
        }
    }
    try:
        return os_client.search(index=INDEX, body=body)
    except:
        # fallback 문법
        body2 = {"size":k,"query":{"knn":{"embedding":{"vector":vec,"k":k}}}}
        return os_client.search(index=INDEX, body=body2)

def answer_with_claude(question:str, contexts:list):
    br = boto3.client("bedrock-runtime", region_name=REGION)
    sys = (
        "You are a helpful assistant. Use ONLY the provided context. "
        "If context is insufficient, say so briefly."
    )
    ctx_text = "\n\n".join(f"[{i+1}] {c}" for i,c in enumerate(contexts))
    msg = (
        f"Question: {question}\n\n"
        f"Context:\n{ctx_text}\n\n"
        "Answer in Korean. Be concise. Cite [1],[2] style at the end."
    )
    payload = {
        "anthropic_version":"bedrock-2023-05-31",
        "max_tokens":400,
        "temperature":0.2,
        "messages":[
            {"role":"user","content":[{"type":"text","text": msg}]}
        ]
    }
    r = br.invoke_model(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        contentType="application/json", accept="application/json",
        body=json.dumps(payload)
    )
    return json.loads(r["body"].read())["content"][0]["text"]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--min-score", type=float, default=0.2)
    args = ap.parse_args()

    vec = embed_text(args.question)
    resp = search(vec, k=args.k)
    hits = resp.get("hits",{}).get("hits",[])

    contexts = []
    for h in hits:
        if h.get("_score",0.0) >= args.min_score:
            contexts.append(h["_source"].get("text",""))

    if not contexts:
        print(json.dumps({"answer":"관련 컨텍스트가 없습니다.","contexts":[]}, ensure_ascii=False, indent=2))
    else:
        out = answer_with_claude(args.question, contexts)
        print(json.dumps({"answer": out, "contexts": contexts}, ensure_ascii=False, indent=2))
