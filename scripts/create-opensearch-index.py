import boto3
import json
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

region = "us-east-1"
service = "aoss"

credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    region,
    service,
    session_token=credentials.token
)

aoss = boto3.client("opensearchserverless", region_name=region)
response = aoss.batch_get_collection(ids=["sh6oof5487ocyqovc0z4"])
endpoint = response["collectionDetails"][0]["collectionEndpoint"]
print(f"Collection endpoint: {endpoint}")

host = endpoint.replace("https://", "")

client = OpenSearch(
    hosts=[{"host": host, "port": 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=300
)

index_body = {
    "settings": {
        "index.knn": True
    },
    "mappings": {
        "properties": {
            "bedrock-knowledge-base-default-vector": {
                "type": "knn_vector",
                "dimension": 1024,
                "method": {
                    "engine": "faiss",
                    "name": "hnsw",
                    "parameters": {}
                }
            },
            "AMAZON_BEDROCK_TEXT_CHUNK": {
                "type": "text"
            },
            "AMAZON_BEDROCK_METADATA": {
                "type": "text",
                "index": False
            }
        }
    }
}

try:
    resp = client.indices.create(index="bedrock-kb-default-index", body=index_body)
    print(f"Index created: {json.dumps(resp, indent=2)}")
except Exception as e:
    print(f"Error: {e}")
