import requests, json, time

BOT_ID = "7646760284791128114"
TOKEN = "pat_13ZVrE2XuafsklTzmcCq8F9DjllxWqEyob6v5iBlZL23MF1vVyTfQmVqEOx1h3Ri"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# ====== Step 1: 发起对话 ======
print(">>> Step 1/3: 发起对话...")
r = requests.post("https://api.coze.cn/v3/chat", headers=HEADERS, json={
    "bot_id": BOT_ID,
    "user_id": "ops-script",
    "stream": False,
    "auto_save_history": True,
    "additional_messages": [{
        "role": "user",
        "content": "CPU 使用率 95%，超过 80% 告警阈值。服务是 Flask Web 应用，跑在 Docker 容器里。请分析可能原因并给出排查命令。",
        "content_type": "text"
    }]
}, timeout=30)

d = r.json()
chat_id = d["data"]["id"]
conv_id = d["data"]["conversation_id"]
print(f"   chat_id={chat_id}, conv_id={conv_id}")

# ====== Step 2: 轮询等对话完成 ======
print(">>> Step 2/3: 等待对话完成...")
for i in range(10):
    time.sleep(2)
    r2 = requests.get("https://api.coze.cn/v3/chat/retrieve",
                      headers=HEADERS,
                      params={"chat_id": chat_id, "conversation_id": conv_id},
                      timeout=30)
    status = r2.json().get("data", {}).get("status", "")
    print(f"   轮询 {i+1}/10: status={status}")
    if status == "completed":
        print("   对话完成!")
        break

# ====== Step 3: 取 AI 回复 ======
print(">>> Step 3/3: 获取 AI 回复...")
r3 = requests.get("https://api.coze.cn/v3/chat/message/list",
                   headers=HEADERS,
                   params={"chat_id": chat_id, "conversation_id": conv_id},
                   timeout=30)
msgs = r3.json()

for msg in msgs.get("data", []):
    role = msg.get("role", "")
    ctype = msg.get("type", "")
    if role == "assistant" and ctype == "answer":
        print("\n" + "=" * 50)
        print("  AI 分析结果")
        print("=" * 50)
        print(msg.get("content", ""))
        print("=" * 50)
        break
else:
    # 调试：打印所有消息
    print("消息列表:")
    for msg in msgs.get("data", [])[-5:]:
        print(f"  [{msg.get('role')}/{msg.get('type')}] {msg.get('content','')[:100]}")

