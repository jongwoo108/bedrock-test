#!/usr/bin/env python3
"""
최종 성공 확인 스크립트
"""

import boto3
import json
from datetime import datetime, timedelta

def check_latest_logs():
    """최신 CloudWatch 로그 확인"""
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
        
        # 최근 10분간의 로그 이벤트 가져오기
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(minutes=10)).timestamp() * 1000)
        
        events_response = logs_client.get_log_events(
            logGroupName=log_group,
            logStreamName=stream_name,
            startTime=start_time,
            endTime=end_time
        )
        
        # 관련 로그 메시지 필터링
        success_messages = []
        error_messages = []
        whoami_messages = []
        
        for event in events_response['events']:
            message = event['message'].strip()
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
            
            if 'Indexed:' in message:
                success_messages.append(f"✅ {timestamp}: {message}")
            elif '403' in message or 'ERROR' in message or 'error' in message.lower():
                error_messages.append(f"❌ {timestamp}: {message}")
            elif 'WHOAMI' in message:
                whoami_messages.append(f"🔍 {timestamp}: {message}")
        
        # 결과 출력
        print("\n=== 최근 10분간 로그 분석 ===")
        
        if whoami_messages:
            print("\n🔍 WHOAMI 확인:")
            for msg in whoami_messages[-2:]:  # 최근 2개만
                print(f"   {msg}")
        
        if success_messages:
            print("\n✅ 성공적인 인덱싱:")
            for msg in success_messages:
                print(f"   {msg}")
        else:
            print("\n⚠️  'Indexed:' 메시지를 찾을 수 없습니다.")
        
        if error_messages:
            print("\n❌ 오류 메시지:")
            for msg in error_messages:
                print(f"   {msg}")
        else:
            print("\n🎉 오류 메시지가 없습니다!")
        
        # 요약
        print(f"\n📊 요약:")
        print(f"   - 성공한 인덱싱: {len(success_messages)}개")
        print(f"   - 오류 발생: {len(error_messages)}개")
        
        if len(success_messages) > 0 and len(error_messages) == 0:
            print("\n🎉 RAG 인덱서가 403 오류 없이 정상 동작하고 있습니다!")
        elif len(error_messages) > 0:
            print("\n⚠️  일부 오류가 발생했지만 확인이 필요합니다.")
        else:
            print("\n⏳ 아직 새로운 실행 로그가 없습니다. 잠시 후 다시 확인해보세요.")
            
    except Exception as e:
        print(f"❌ 로그 확인 중 오류: {e}")

if __name__ == "__main__":
    print("🔍 RAG 인덱서 최종 상태 확인 중...")
    check_latest_logs()
