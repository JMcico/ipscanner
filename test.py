import subprocess
from datetime import datetime, timedelta

container = "nginx"  # 改成你的容器名字

# 过去一分钟
result = subprocess.run(
    ["docker", "logs", "--since", "1m", container],
    capture_output=True, text=True
)

active_ips = set()
for line in result.stdout.splitlines():
    parts = line.split()
    if len(parts) > 0:
        ip = parts[0]
        active_ips.add(ip)

print("活跃 IP (过去1分钟):")
for ip in active_ips:
    print(ip)
