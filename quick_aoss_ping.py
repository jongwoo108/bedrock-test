# quick_aoss_ping.py
import os, boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

region = "us-east-1"
host = os.environ["AOSS_HOST"]  # 반드시 도메인만 (https:// 빼고)

credentials = boto3.Session().get_credentials()
auth = AWSV4SignerAuth(credentials, region, "aoss")

client = OpenSearch(
    hosts=[{"host": host, "port": 443}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
)

print(client.info())
