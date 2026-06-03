"""
AI 运维告警桥接脚本
Prometheus 拉数据 → 超阈值 → Coze AI 流式分析 → 记录日志
"""

import requests, json
from datetime import datetime

# ===== 配置 =====
PROM_URL = "http://localhost:9090"
COZE_BOT_ID = "7646760284791128114"
COZE_TOKEN = "pat_13ZVrE2XuafsklTzmcCq8F9DjllxWqEyob6v5iBlZL23MF1vVyTfQmVqEOx1h3Ri"
LOG_FILE = "/home/ubuner/ops-app/ai_ops/alert.log"

COZE_HEADERS = {
    "Authorization": f"Bearer {COZE_TOKEN}",
    "Content-Type": "application/json"
}

# ===== 1. Prometheus 查询 =====
def query_prom(promql):
    try:
        r = requests.get(f"{PROM_URL}/api/v1/query",
                        params={"query": promql}, timeout=10)
        data = r.json()
        results = data.get("data", {}).get("result", [])
        return float(results[0]["value"][1]) if results else None
    except Exception as e:
        print(f"  [ERROR] Prometheus: {e}")
        return None

# ===== 2. Coze AI 流式分析 =====
def ask_ai(alert_text):
    """发告警给 Coze，流式接收 AI 分析，返回完整回复"""
    print("  发送给 AI 分析...")
    try:
        r = requests.post("https://api.coze.cn/v3/chat",
            headers=COZE_HEADERS,
            json={
                "bot_id": COZE_BOT_ID,
                "user_id": "ops-auto",
                "stream": True,
                "auto_save_history": False,
                "additional_messages": [{
                    "role": "user",
                    "content": alert_text,
                    "content_type": "text"
                }]
            },
            stream=True, timeout=60
        )

        answer_parts = []
        for line in r.iter_lines():
            if not line: continue
            line_str = line.decode('utf-8')
            if line_str.startswith('data:'):
                data_str = line_str[5:].strip()
                if data_str == '[DONE]': break
                try:
                    evt = json.loads(data_str)
                    if evt.get('type') == 'answer':
                        content = evt.get('content', '')
                        answer_parts.append(content)
                except: pass

        return ''.join(answer_parts) if answer_parts else "[AI 无回复]"
    except Exception as e:
        return f"[AI 调用失败] {e}"

# ===== 3. 主流程 =====
def main():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    alerts = []

    # 检查 CPU
    cpu = query_prom("rate(process_cpu_seconds_total[1m]) * 100")
    if cpu is not None:
        print(f"[{now}] CPU: {cpu:.1f}%")
        if cpu > 80:
            alerts.append(
                f"CPU 使用率过高告警："
                f"当前 {cpu:.1f}%，阈值 80%。"
                f"服务：Flask 应用，Docker 容器部署。"
                f"请分析可能原因并给出具体排查命令。"
            )

    # 检查 5xx 错误率
    err = query_prom(
        "sum(rate(http_requests_total{status=~\"5..\"}[1m])) "
        "/ sum(rate(http_requests_total[1m])) * 100"
    )
    if err is not None:
        print(f"[{now}] 5xx: {err:.1f}%")
        if err > 5:
            alerts.append(
                f"HTTP 5xx 错误率过高告警："
                f"当前 {err:.1f}%，阈值 5%。"
                f"服务：Flask 应用。"
                f"请分析可能原因并给出排查步骤。"
            )

    # 处理告警
    if alerts:
        for i, alert in enumerate(alerts):
            print(f"\n{'='*40}")
            print(f"告警 {i+1}/{len(alerts)}")
            ai_reply = ask_ai(alert)

            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"[{now}] 告警 #{i+1}\n{alert}\n\n")
                f.write(f"AI 分析:\n{ai_reply}\n")

            print(f"  结果已写入 {LOG_FILE}")
    else:
        print(f"[{now}] 系统正常，无告警。")
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{now}] 巡检正常\n")

if __name__ == "__main__":
    main()
