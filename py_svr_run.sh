mkdir -p logs
nohup ./py_svr -addr 0.0.0.0:9443 < /dev/null > logs/py_svr.log 2>&1 &
echo $! > logs/py_svr.pid
echo "PID: $(cat logs/py_svr.pid)"
