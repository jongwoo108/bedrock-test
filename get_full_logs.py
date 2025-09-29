#!/usr/bin/env python3
"""
전체 로그 확인 스크립트
"""

import boto3
from datetime import datetime, timedelta

def get_all_recent_logs():
    """최근 로그의 모든 내용을 가져오기"""
    logs_client = boto3.client('logs', region_name='us-east-1')
    log_group = '/aws/lambda/kb-rag-indexer'
    
    try:
        # 최신 로그 스트림 찾기
        response = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=1
        )
        
        if not response['logStreams']:
            print("❌ 로그 스트림을 찾을 수 없습니다.")
            return
            
        stream_name = response['logStreams'][0]['logStreamName']
        print(f"📋 최신 로그 스트림: {stream_name}")
        
        # 최근 5분간의 모든 로그 이벤트 가져오기
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(minutes=5)).timestamp() * 1000)
        
        events_response = logs_client.get_log_events(
            logGroupName=log_group,
            logStreamName=stream_name,
            startTime=start_time,
            endTime=end_time
        )
        
        print("\n=== 최근 5분간 전체 로그 ===")
        for event in events_response['events']:
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
            message = event['message'].strip()
            print(f"{timestamp}: {message}")
            
    except Exception as e:
        print(f"❌ 로그 확인 중 오류: {e}")

if __name__ == "__main__":
    get_all_recent_logs()
