#!/usr/bin/env bash
# 서버 1개 + 클라이언트 10개 인증서 생성 (ECDSA P-256, TLS1.3용)
set -euo pipefail
cd "$(dirname "$0")"

N_CLIENTS="${1:-10}"
DAYS=3650
SUBJ_BASE="/C=KR/ST=Seoul/L=Seoul/O=Test"

rm -f *.pem *.key *.csr *.srl *.cnf

cat > openssl.cnf <<EOF
[req]
distinguished_name = dn
[dn]
[v3_ca]
basicConstraints = critical,CA:TRUE
keyUsage = critical,keyCertSign,cRLSign
[v3_srv]
basicConstraints = CA:FALSE
keyUsage = critical,digitalSignature,keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = DNS:localhost,IP:127.0.0.1
[v3_cli]
basicConstraints = CA:FALSE
keyUsage = critical,digitalSignature
extendedKeyUsage = clientAuth
EOF

# CA
openssl ecparam -name prime256v1 -genkey -noout -out ca.key
openssl req -x509 -new -key ca.key -sha256 -days $DAYS \
  -subj "${SUBJ_BASE}/CN=TestCA" \
  -extensions v3_ca -config openssl.cnf -out ca.pem

# 서버
openssl ecparam -name prime256v1 -genkey -noout -out server.key
openssl req -new -key server.key -subj "${SUBJ_BASE}/CN=localhost" -out server.csr
openssl x509 -req -in server.csr -CA ca.pem -CAkey ca.key -CAcreateserial \
  -days $DAYS -sha256 -extensions v3_srv -extfile openssl.cnf -out server.pem

# 클라이언트
for i in $(seq 1 "$N_CLIENTS"); do
  openssl ecparam -name prime256v1 -genkey -noout -out "client${i}.key"
  openssl req -new -key "client${i}.key" -subj "${SUBJ_BASE}/CN=client${i}" -out "client${i}.csr"
  openssl x509 -req -in "client${i}.csr" -CA ca.pem -CAkey ca.key -CAcreateserial \
    -days $DAYS -sha256 -extensions v3_cli -extfile openssl.cnf -out "client${i}.pem"
done

rm -f *.csr *.srl openssl.cnf
echo "[ok] 서버 1개 + 클라이언트 ${N_CLIENTS}개 인증서 생성 완료"
ls -1 *.pem *.key
