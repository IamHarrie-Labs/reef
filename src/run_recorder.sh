#!/bin/sh
# Waits for api.bitget.com to become reachable, then launches recorder.py.
# If the recorder ever exits (crash, network drop), waits and relaunches.
# Logs everything to data/timeseries/recorder_wrapper.log.
cd "$(dirname "$0")/.."
LOG=data/timeseries/recorder_wrapper.log
echo "[wrapper] started $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG"
while true; do
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
    "https://api.bitget.com/api/v2/mix/market/tickers?productType=USDT-FUTURES")
  if [ "$code" = "200" ]; then
    echo "[wrapper] network up ($code), launching recorder.py $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG"
    python src/recorder.py >> data/timeseries/recorder.log 2>&1
    echo "[wrapper] recorder.py exited, will retry in 60s $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG"
  else
    echo "[wrapper] network down (HTTP $code), retry in 60s $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG"
  fi
  sleep 60
done
