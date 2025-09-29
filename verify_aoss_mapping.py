#!/usr/bin/env python3
"""
AOSS 인덱스 매핑 확인 도구
embedding 필드가 knn_vector dim=1536인지 검증
"""

import json
import boto3
import requests
from requests_aws4auth import AWS4Auth

# 설정
REGION = "us-east-1"
AOSS_ENDPOINT = "https://iwvt29rkcwesncyf8sw8.us-east-1.aoss.amazonaws.com"
INDEX_NAME = "kb-rag"
COLLECTION_NAME = "kb-rag"

# AWS 인증 설정
session = boto3.Session()
creds = session.get_credentials().get_frozen_credentials()
awsauth = AWS4Auth(creds.access_key, creds.secret_key, REGION, "aoss", session_token=creds.token)

def check_mapping():
    """인덱스 매핑 확인"""
    url = f"{AOSS_ENDPOINT}/{INDEX_NAME}/_mapping"
    headers = {
        "Content-Type": "application/json",
        "x-amz-collection-name": COLLECTION_NAME,
    }
    
    try:
        response = requests.get(url, auth=awsauth, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            mapping = response.json()
            print("=== 인덱스 매핑 정보 ===")
            print(json.dumps(mapping, indent=2, ensure_ascii=False))
            
            # embedding 필드 확인
            try:
                props = mapping[INDEX_NAME]["mappings"]["properties"]
                if "embedding" in props:
                    emb_info = props["embedding"]
                    print(f"\n✅ embedding 필드 발견:")
                    print(f"   Type: {emb_info.get('type')}")
                    print(f"   Dimension: {emb_info.get('dimension')}")
                    
                    if emb_info.get('type') == 'knn_vector' and emb_info.get('dimension') == 1536:
                        print("✅ 매핑이 올바르게 구성됨!")
                    else:
                        print("❌ 매핑 구성에 문제가 있음")
                else:
                    print("❌ embedding 필드를 찾을 수 없음")
            except KeyError as e:
                print(f"❌ 매핑 구조 파싱 실패: {e}")
        else:
            print(f"❌ 매핑 조회 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    check_mapping()
