import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
import time
from datetime import datetime, timezone


load_dotenv()  # 从 .env 文件读取配置

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "connection_timeout": int(os.getenv("DB_TIMEOUT", 5))  # 超时时间，单位秒
}

TABLE_NAME = os.getenv("DB_TABLE", "devices")


def sync_devices(devices, retries=2, retry_delay=3):
    """
    同步设备信息到 MySQL
    - online: 扫描到的设备标记为 1
    - offline: 数据库中存在但本次扫描未发现的设备标记为 0
    - retries: 如果连接失败，重试次数
    - retry_delay: 重试间隔秒数
    """
    for attempt in range(retries + 1):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            break
        except Error as e:
            print(f"连接 MySQL 失败: {e}")
            if attempt < retries:
                print(f"{retry_delay} 秒后重试 ({attempt + 1}/{retries})...")
                time.sleep(retry_delay)
            else:
                print("已达到最大重试次数，跳过同步。")
                return

    try:
        cur = conn.cursor()
        cur.execute("SET time_zone = 'SYSTEM';")

        # 确保表存在
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ip VARCHAR(32),
                mac VARCHAR(32) UNIQUE,
                hostname VARCHAR(255),
                vendor VARCHAR(255),
                online TINYINT(1),
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 先标记所有设备 offline
        try:
            cur.execute(f"UPDATE {TABLE_NAME} SET online=0")
        except Error as e:
            print(f"更新 offline 失败: {e}")

        for dev in devices:
            mac = dev.get("mac", "")
            ip = dev.get("ip", "")
            hostname = dev.get("hostname", "")
            vendor = dev.get("vendor", "")

            try:
                # 查是否已有该 MAC
                cur.execute(f"SELECT id FROM {TABLE_NAME} WHERE mac=%s", (mac,))
                row = cur.fetchone()
                now = datetime.now()  # 本地时间
                if row:
                    # 更新已有设备信息
                    cur.execute(f"""
                        UPDATE {TABLE_NAME} 
                        SET ip=%s, vendor=%s, online=1, last_seen=%s
                        WHERE id=%s
                    """, (ip, vendor, now, row[0]))
                else:
                    # 插入新设备
                    cur.execute(f"""
                        INSERT INTO {TABLE_NAME} (ip, mac, hostname, vendor, online, last_seen)
                        VALUES (%s, %s, %s, %s, 1, %s)
                    """, (ip, mac, hostname, vendor, now))
            except Error as e:
                print(f"操作设备 {mac} 失败: {e}")

        conn.commit()
        print(f"同步完成，共处理 {len(devices)} 台设备。")
    finally:
        if conn.is_connected():
            cur.close()
            conn.close()
