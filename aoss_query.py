# file: aoss_query.py
import os, json, argparse, boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

REGION = "us-east-1"
SERVICE = "aoss"
INDEX = "kb-rag"
HOST = os.environ["AOSS_HOST"]  # 예: iwvt29rkcwesncyf8sw8.us-east-1.aoss.amazonaws.com

# --- OpenSearch (SigV4) client ---
auth = AWSV4SignerAuth(boto3.Session().get_credentials(), REGION, SERVICE)
client = OpenSearch(
    hosts=[{"host": HOST, "port": 443}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
)

# --- Bedrock Titan Embeddings ---
def embed_text(text: str):
    br = boto3.client("bedrock-runtime", region_name=REGION)
    res = br.invoke_model(
        modelId="amazon.titan-embed-text-v1",
        contentType="application/json",
        accept="application/json",
        body=json.dumps({"inputText": text})
    )
    data = json.loads(res["body"].read())
    emb = data["embedding"]
    # 혹시 문자열로 올 경우 리스트로 변환
    if isinstance(emb, str):
        emb = json.loads(emb)
    # float 배열 보장
    return [float(x) for x in emb]

# --- AOSS VectorSearch: KNN 쿼리 (양식 자동 호환) ---
def search_knn(vec, k: int, num_candidates: int = 100):
    """
    1) OpenSearch 최신 문법:
       {"query":{"knn":{"field":"embedding","query_vector":[...],"k":K,"num_candidates":N}}}
    2) 구버전/대체 문법:
       {"query":{"knn":{"embedding":{"vector":[...],"k":K}}}}
    두 가지를 순차 시도해 호환성 보장.
    """
    # 1차 시도: field + query_vector + num_candidates
    body1 = {
        "size": k,
        "query": {
            "knn": {
                "field": "embedding",
                "query_vector": vec,
                "k": k,
                "num_candidates": num_candidates
            }
        }
    }
    try:
        return client.search(index=INDEX, body=body1)
    except Exception as e1:
        # 2차 시도: embedding 내 vector 형식
        body2 = {
            "size": k,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": vec,
                        "k": k
                    }
                }
            }
        }
        return client.search(index=INDEX, body=body2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--k", type=int, default=4)
    parser.add_argument("--min-score", type=float, default=0.2)
    parser.add_argument("--num-candidates", type=int, default=100)
    args = parser.parse_args()

    qv = embed_text(args.question)
    print("✅ DEBUG vector:", type(qv), len(qv), type(qv[0]))

    resp = search_knn(qv, k=args.k, num_candidates=args.num_candidates)

    results = []
    for h in resp.get("hits", {}).get("hits", []):
        score = h.get("_score", 0.0)
        if score >= args.min_score:
            results.append({
                "score": score,
                "doc_id": h.get("_id"),
                "text": h.get("_source", {}).get("text", "")
            })

    print(json.dumps({"query": args.question, "results": results}, ensure_ascii=False, indent=2))
