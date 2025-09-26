# discover.py
import subprocess
import re

def discover_devices(network="10.40.8.0/24"):
    """
    使用 nmap 扫描网络，返回设备信息：
    [
        {"ip": ..., "mac": ..., "hostname": ..., "vendor": ...},
        ...
    ]
    """
    cmd = ["sudo", "nmap", "-sn", network]
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout

    devices = []
    ignore_list = [100, 254]

    # 每个主机分块解析
    blocks = output.split("Nmap scan report for")
    for blk in blocks[1:]:
        blk = blk.strip()
        lines = blk.splitlines()
        ip = ""
        hostname = ""
        mac = ""
        vendor = ""

        # 第一行可能是 "hostname (ip)" 或 "ip"
        m = re.match(r"(.+)\s+\(([\d\.]+)\)", lines[0])
        if m:
            hostname = m.group(1).strip()
            ip = m.group(2).strip()
        else:
            ip = lines[0].strip()

        try:
            last_octet = int(ip.split('.')[-1])
            if last_octet in ignore_list:
                continue
        except (ValueError, IndexError):
            pass  # IP 格式异常，不过滤

        for line in lines:
            if "MAC Address:" in line:
                # MAC Address: 1C:1A:1B:60:45:54 (Shanghai Sunmi Technology)
                mac_match = re.match(r"MAC Address: ([0-9A-F:]+) \((.*)\)", line)
                if mac_match:
                    mac = mac_match.group(1)
                    vendor = mac_match.group(2)
                else:
                    mac = line.split()[2]
                    vendor = ""

        devices.append({
            "ip": ip,
            "hostname": hostname,
            "mac": mac,
            "vendor": vendor
        })

    return devices

if __name__ == "__main__":
    devs = discover_devices("10.40.8.0/24")
    for d in devs:
        print(d)
