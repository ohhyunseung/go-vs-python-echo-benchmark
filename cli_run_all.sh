#!/bin/bash

# 1부터 10까지 루프
for i in {1..10}
do
   # 명령어 실행
   # -cert와 -key 파일명에 변수 i를 삽입
   # 마지막에 &를 붙여 백그라운드에서 동시에 실행되도록 함
   ./go_client -cert "certs/client${i}.pem" -key "certs/client${i}.key" -addr 192.168.56.103:9443 -n 100 &
   
   echo "Client ${i} started."
done

# 모든 백그라운드 프로세스가 종료될 때까지 대기 (선택 사항)
wait
echo "All clients have finished."
