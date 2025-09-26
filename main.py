# main.py
from discover import discover_devices
from sync import sync_devices

def main():
    # 配置网络段
    network = "10.40.8.0/24"

    print(f"开始扫描网络: {network}")
    devices = discover_devices(network=network)

    if not devices:
        print("未发现设备。")
        return

    print("\n扫描结果:")
    for dev in devices:
        print(f"IP: {dev['ip']}, MAC: {dev['mac']}, Hostname: {dev['hostname']}, Vendor: {dev['vendor']}")

    print("\n同步设备到 MySQL...")
    sync_devices(devices)
    print("同步完成。")

if __name__ == "__main__":
    main()
