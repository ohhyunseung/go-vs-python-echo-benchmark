# 성능 비교: Python (uvloop) vs Go (Goroutine)

### 측정 환경

- 동시 연결: 1,000개
- 프로토콜: mTLS TLS 1.3 Echo
- 버퍼 크기: 8,192 bytes

### 빌드
#### 인증서 생성
```
cd certs
./gen_certs.sh
cd ..
```
#### Go
```
go build -o go_svr ./cmd/go_svr
go build -o go_client ./cmd/go_client
```
#### python
```
cd cmd/py_svr
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirement.txt
pyinstaller --onefile --name py_svr main.py
cp dist/py_svr ../../.
```

#### server
```
virtualbox : Debian
메모리 : 6144 MB
CPU Core : 3 개
cmd/go_svr
cmd/py_svr
```

#### client
```
virtualbox : ubuntu
메모리 : 4096 MB
CPU Core : 4 개
cmd/go_client 동일 사용
10개 client
```

## 수치 요약

| 지표           | Python (uvloop) | Go           | 비율 (Go/PY) | 비고                |
|----------------|-----------------|--------------|--------------|---------------------|
| 평균 msg/s     | 2,508           | 6,270        | 2.50x        |                     |
| 최대 msg/s     | 2,987           | 7,472        | 2.50x        |                     |
| 최소 msg/s     | 1,822           | 4,757        | 2.61x        |                     |
| 평균 MB/s      | 0.61            | 1.53         | 2.51x        |                     |
| 최대 MB/s      | 0.73            | 1.82         | 2.49x        |                     |
| 최소 MB/s      | 0.44            | 1.16         | 2.64x        |                     |
| msg/s 표준편차 | ~249            | ~503         | —            |                     |
| 안정성 (CV)    | ~9.9%           | ~8.0%        | Go가 소폭 안정 |





