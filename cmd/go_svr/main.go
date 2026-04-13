package main

// 소켓 + mTLS(TLS1.3) 성능 테스트 서버 - Go
// 사용: ./go_svr -addr :9443
//   certs/ca.pem, server.pem, server.key 참조
//   1초 간격 통계: active/total 연결, msg/s, MB/s

import (
	"crypto/tls"
	"crypto/x509"
	"flag"
	"io"
	"log"
	"os"
	"sync/atomic"
	"time"
)

var (
	active   int64
	totalCn  int64
	totalMsg int64
	totalByt int64
)

func handle(c *tls.Conn) {
	atomic.AddInt64(&active, 1)
	atomic.AddInt64(&totalCn, 1)
	defer func() {
		atomic.AddInt64(&active, -1)
		c.Close()
	}()

	if err := c.Handshake(); err != nil {
		return
	}
	st := c.ConnectionState()
	cn := ""
	if len(st.PeerCertificates) > 0 {
		cn = st.PeerCertificates[0].Subject.CommonName
	}
	log.Printf("[+] %s CN=%s tls=0x%x", c.RemoteAddr(), cn, st.Version)

	buf := make([]byte, 8192)
	for {
		n, err := c.Read(buf)
		if n > 0 {
			atomic.AddInt64(&totalMsg, 1)
			atomic.AddInt64(&totalByt, int64(n))
			if _, werr := c.Write(buf[:n]); werr != nil {
				return
			}
		}
		if err != nil {
			if err != io.EOF {
				_ = err
			}
			return
		}
	}
}

func stats() {
	var pm, pb int64
	t := time.NewTicker(1 * time.Second)
	for range t.C {
		m := atomic.LoadInt64(&totalMsg)
		b := atomic.LoadInt64(&totalByt)
		log.Printf("[GO] active=%d total=%d msg/s=%d MB/s=%.2f",
			atomic.LoadInt64(&active),
			atomic.LoadInt64(&totalCn),
			m-pm,
			float64(b-pb)/1024.0/1024.0,
		)
		pm, pb = m, b
	}
}

func main() {
	addr := flag.String("addr", ":9443", "listen addr")
	flag.Parse()

	cert, err := tls.LoadX509KeyPair("certs/server.pem", "certs/server.key")
	if err != nil {
		log.Fatal(err)
	}
	caPem, err := os.ReadFile("certs/ca.pem")
	if err != nil {
		log.Fatal(err)
	}
	pool := x509.NewCertPool()
	pool.AppendCertsFromPEM(caPem)

	cfg := &tls.Config{
		Certificates: []tls.Certificate{cert},
		ClientCAs:    pool,
		ClientAuth:   tls.RequireAndVerifyClientCert,
		MinVersion:   tls.VersionTLS13,
		MaxVersion:   tls.VersionTLS13,
	}

	ln, err := tls.Listen("tcp", *addr, cfg)
	if err != nil {
		log.Fatal(err)
	}
	log.Printf("[GO] mTLS(TLS1.3) 서버 listen %s", *addr)
	go stats()

	for {
		c, err := ln.Accept()
		if err != nil {
			continue
		}
		go handle(c.(*tls.Conn))
	}
}
