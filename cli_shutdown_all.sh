#!/bin/bash

# 실행 중인 go_client 프로세스 이름을 찾아 종료 시그널(SIGTERM) 전송
echo "Stopping all go_client processes..."
pkill -f go_client

# 프로세스가 완전히 정리될 때까지 잠시 대기
sleep 1

# 남은 프로세스가 있는지 확인
COUNT=$(pgrep -f go_client | wc -l)

if [ $COUNT -eq 0 ]; then
    echo "All clients have been successfully terminated."
else
    echo "Some processes are still running. Force killing..."
    pkill -9 -f go_client
fi
