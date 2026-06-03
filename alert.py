import requests
from datetime import datetime

PROM_URL = "http://localhost:9090"

def check_error_rate(threshold=5):
    query = 'sum(rate(http_requests_total{status=~"5.."}[1m])) / sum(rate(http_requests_total[1m])) * 100'
    r = requests.get(f"{PROM_URL}/api/v1/query", params={"query": query})
    data = r.json()
    for result in data.get("data", {}).get("result", []):
        val = float(result["value"][1])
        if val > threshold:
            print(f"[{datetime.now()}] ALERT: 5xx Error Rate {val:.1f}% > {threshold}%")

def check_cpu(threshold=80):
    query = 'rate(process_cpu_seconds_total[1m]) * 100'
    r = requests.get(f"{PROM_URL}/api/v1/query", params={"query": query})
    data = r.json()
    for result in data.get("data", {}).get("result", []):
        val = float(result["value"][1])
        if val > threshold:
            print(f"[{datetime.now()}] ALERT: CPU {val:.1f}% > {threshold}%")

if __name__ == "__main__":
    print(f"{'='*40}")
    print(f"[{datetime.now()}] 巡检开始")
    check_cpu()
    check_error_rate()
    print(f"[{datetime.now()}] 巡检结束")
    print(f"{'='*40}")
