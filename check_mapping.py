import os
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import boto3

host = os.getenv("AOSS_HOST")
region = "us-east-1"

# boto3 credentials
credentials = boto3.Session().get_credentials()
auth = AWSV4SignerAuth(credentials, region, "aoss")

client = OpenSearch(
    hosts=[{"host": host, "port": 443}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

mapping = client.indices.get_mapping(index="kb-rag")
print(mapping)
