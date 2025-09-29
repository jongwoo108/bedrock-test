@echo off
echo === Lambda CloudWatch 로그 확인 ===
echo.

echo 1. 최신 로그 스트림 찾기:
aws logs describe-log-streams --log-group-name "/aws/lambda/kb-rag-indexer" --region us-east-1 --order-by LastEventTime --descending --max-items 1 --query "logStreams[0].logStreamName" --output text > latest_stream.tmp
set /p STREAM_NAME=<latest_stream.tmp

echo 로그 스트림: %STREAM_NAME%
echo.

echo 2. 최근 로그 이벤트 확인:
aws logs get-log-events --log-group-name "/aws/lambda/kb-rag-indexer" --log-stream-name "%STREAM_NAME%" --region us-east-1 --start-from-head --output text | findstr /C:"WHOAMI" /C:"Indexed" /C:"403" /C:"ERROR" /C:"AOSS"

del latest_stream.tmp
pause
