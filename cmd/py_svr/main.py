import asyncio
import ssl
import argparse
import uvloop

# 전역 통계 변수
active_conns = 0
total_conns = 0
total_msgs = 0
total_bytes = 0

verbose = False  # main()에서 설정


async def handle_echo(reader, writer):
    global active_conns, total_conns, total_msgs, total_bytes

    active_conns += 1
    total_conns += 1

    addr = writer.get_extra_info('peername')
    ssl_obj = writer.get_extra_info('ssl_object')
    cn, tls_version = "Unknown", "Unknown"

    if ssl_obj:
        try:
            cert = ssl_obj.getpeercert()
            tls_version = ssl_obj.version()
            if cert:
                for rdn in cert.get('subject', []):
                    for key, value in rdn:
                        if key == 'commonName':
                            cn = value
        except Exception:
            pass

    if verbose:
        print(f"[+] {addr} CN={cn} tls={tls_version}")

    try:
        while True:
            data = await reader.read(8192)
            if not data:
                break

            total_msgs += 1
            total_bytes += len(data)

            writer.write(data)
            await writer.drain()
    except Exception:
        pass
    finally:
        active_conns -= 1
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass


async def stats_loop():
    prev_msg = 0
    prev_bytes = 0

    while True:
        await asyncio.sleep(1)
        curr_msg = total_msgs
        curr_bytes = total_bytes

        msg_per_sec = curr_msg - prev_msg
        mb_per_sec = (curr_bytes - prev_bytes) / 1024 / 1024

        print(f"[PY] active={active_conns} total={total_conns} "
              f"msg/s={msg_per_sec} MB/s={mb_per_sec:.2f}")

        prev_msg, prev_bytes = curr_msg, curr_bytes


async def main():
    global verbose

    parser = argparse.ArgumentParser()
    parser.add_argument("-addr", default="0.0.0.0:9443", help="listen address (host:port)")
    parser.add_argument("-v", "--verbose", action="store_true", help="연결마다 로그 출력")
    args = parser.parse_args()

    verbose = args.verbose

    host, port = args.addr.rsplit(':', 1)
    if not host:
        host = '0.0.0.0'

    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="certs/server.pem", keyfile="certs/server.key")
    context.load_verify_locations(cafile="certs/ca.pem")
    context.verify_mode = ssl.CERT_REQUIRED
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.maximum_version = ssl.TLSVersion.TLSv1_3

    server = await asyncio.start_server(handle_echo, host, int(port), ssl=context)

    print(f"[PY] mTLS(TLS1.3) 서버 listen {host}:{port}")

    await asyncio.gather(server.serve_forever(), stats_loop())


if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass