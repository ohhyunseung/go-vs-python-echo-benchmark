package main

// mTLS(TLS1.3) 테스트 클라이언트 - Go
// 단일 클라이언트 cert로 -n 개의 병렬 연결을 유지하며 주기적으로 echo 전송
// 사용: ./go_client -cert certs/client1.pem -key certs/client1.key -addr 127.0.0.1:9443 -n 100

import (
	"crypto/tls"
	"crypto/x509"
	"flag"
	"log"
	"os"
	"sync/atomic"
	"time"
)

var sent int64

func worker(addr string, cfg *tls.Config, interval time.Duration, payload []byte) {
	for {
		c, err := tls.Dial("tcp", addr, cfg)
		if err != nil {
			time.Sleep(500 * time.Millisecond)
			continue
		}
		buf := make([]byte, len(payload))
		for {
			if _, err := c.Write(payload); err != nil {
				break
			}
			if _, err := c.Read(buf); err != nil {
				break
			}
			atomic.AddInt64(&sent, 1)
			time.Sleep(interval)
		}
		c.Close()
	}
}

func main() {
	addr := flag.String("addr", "127.0.0.1:9443", "server addr")
	certF := flag.String("cert", "certs/client1.pem", "client cert")
	keyF := flag.String("key", "certs/client1.key", "client key")
	caF := flag.String("ca", "certs/ca.pem", "ca cert")
	n := flag.Int("n", 50, "concurrent conns")
	ms := flag.Int("interval", 100, "send interval ms")
	size := flag.Int("size", 256, "payload bytes")
	flag.Parse()

	cert, err := tls.LoadX509KeyPair(*certF, *keyF)
	if err != nil {
		log.Fatal(err)
	}
	caPem, err := os.ReadFile(*caF)
	if err != nil {
		log.Fatal(err)
	}
	pool := x509.NewCertPool()
	pool.AppendCertsFromPEM(caPem)

	cfg := &tls.Config{
		Certificates: []tls.Certificate{cert},
		RootCAs:      pool,
		ServerName:   "localhost",
		MinVersion:   tls.VersionTLS13,
		MaxVersion:   tls.VersionTLS13,
	}

	payload := make([]byte, *size)
	for i := range payload {
		payload[i] = 'A'
	}

	log.Printf("[CLI-GO] %s conns=%d interval=%dms size=%dB cert=%s",
		*addr, *n, *ms, *size, *certF)

	for i := 0; i < *n; i++ {
		go worker(*addr, cfg, time.Duration(*ms)*time.Millisecond, payload)
		time.Sleep(2 * time.Millisecond)
	}

	var ps int64
	t := time.NewTicker(1 * time.Second)
	for range t.C {
		s := atomic.LoadInt64(&sent)
		log.Printf("[CLI-GO] sent/s=%d total=%d", s-ps, s)
		ps = s
	}
}
