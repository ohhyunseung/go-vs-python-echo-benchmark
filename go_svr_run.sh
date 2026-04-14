mkdir -p logs
nohup ./go_svr > logs/go_svr.log 2>&1 &
echo $! > logs/go_svr.pid
echo "PID: $(cat logs/go_svr.pid)"
