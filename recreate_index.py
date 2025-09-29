#!/usr/bin/env python3
"""
AOSS 인덱스 재생성 스크립트
"""

import boto3
import requests
import json
from requests_aws4auth import AWS4Auth

# 설정
REGION = "us-east-1"
AOSS_ENDPOINT = "https://iwvt29rkcwesncyf8sw8.us-east-1.aoss.amazonaws.com"
INDEX_NAME = "kb-rag"
COLLECTION_NAME = "kb-rag"

# AWS 인증
session = boto3.Session()
creds = session.get_credentials().get_frozen_credentials()
awsauth = AWS4Auth(creds.access_key, creds.secret_key, REGION, "aoss", session_token=creds.token)

def delete_index():
    """기존 인덱스 삭제"""
    url = f"{AOSS_ENDPOINT}/{INDEX_NAME}"
    headers = {
        "Content-Type": "application/json",
        "x-amz-collection-name": COLLECTION_NAME,
    }
    
    print(f"🗑️ 기존 인덱스 삭제 시도: {INDEX_NAME}")
    response = requests.delete(url, auth=awsauth, headers=headers)
    print(f"삭제 응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ 인덱스 삭제 성공")
    elif response.status_code == 404:
        print("ℹ️ 인덱스가 존재하지 않음")
    else:
        print(f"⚠️ 삭제 응답: {response.text}")

def create_index():
    """새 인덱스 생성"""
    url = f"{AOSS_ENDPOINT}/{INDEX_NAME}"
    headers = {
        "Content-Type": "application/json",
        "x-amz-collection-name": COLLECTION_NAME,
    }
    
    # 인덱스 매핑 (실제 Titan 임베딩 1536차원)
    mapping = {
        "settings": {
            "index": {
                "knn": True,
                "knn.algo_param.ef_search": 100
            }
        },
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "content": {"type": "text"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": 1536,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "nmslib"
                    }
                }
            }
        }
    }
    
    print(f"🔨 새 인덱스 생성 시도: {INDEX_NAME}")
    response = requests.put(url, auth=awsauth, headers=headers, data=json.dumps(mapping))
    print(f"생성 응답 상태: {response.status_code}")
    
    if response.status_code in [200, 201]:
        print("✅ 인덱스 생성 성공!")
        print("📋 매핑 정보:")
        print(json.dumps(mapping, indent=2, ensure_ascii=False))
    else:
        print(f"❌ 생성 실패: {response.text}")
        return False
    
    return True

def test_index_access():
    """인덱스 접근 테스트"""
    url = f"{AOSS_ENDPOINT}/{INDEX_NAME}/_mapping"
    headers = {
        "Content-Type": "application/json",
        "x-amz-collection-name": COLLECTION_NAME,
    }
    
    print(f"🧪 인덱스 접근 테스트...")
    response = requests.get(url, auth=awsauth, headers=headers)
    print(f"테스트 응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ 인덱스 접근 성공!")
        return True
    else:
        print(f"❌ 접근 실패: {response.text}")
        return False

if __name__ == "__main__":
    print("🔄 AOSS 인덱스 재생성 시작...")
    
    # 1. 기존 인덱스 삭제
    delete_index()
    
    # 2. 새 인덱스 생성
    if create_index():
        # 3. 접근 테스트
        if test_index_access():
            print("\n🎉 인덱스 재생성 및 테스트 완료!")
            print("이제 Lambda 함수를 다시 테스트해보세요.")
        else:
            print("\n⚠️ 인덱스는 생성되었지만 접근에 문제가 있습니다.")
    else:
        print("\n❌ 인덱스 생성에 실패했습니다.")
