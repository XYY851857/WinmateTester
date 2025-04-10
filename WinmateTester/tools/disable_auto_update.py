import ctypes
import subprocess
import sys
import os
import time
from datetime import datetime

import psutil

lgpo_path = os.path.abspath(".\\0\\DisableAutoUpdate\\LGPO\\LGPO.exe")
backup_folder = os.path.abspath(".\\0\\DisableAutoUpdate\\LGPO\\LGPO_20241106")


def get_mac_address_by_name():
    for interface, addrs in psutil.net_if_addrs().items():
        if interface == "乙太網路 2":
            for addr in addrs:
                if addr.family == psutil.AF_LINK:  # AF_LINK 表示 MAC 地址
                    return addr.address
    return "Unknown"


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        print(f"無法判斷管理員權限: {e}")
        return False


if is_admin():
    try:
        print("嘗試執行 LGPO 指令...")
        subprocess.run([lgpo_path, '/g', backup_folder], check=True)
        with open(".\\log\\DAU_set_log.txt", 'a') as file:
            mac_address = get_mac_address_by_name()
            file.write(f'{datetime.now().strftime("%Y%m%d:%H%M%S")}: {mac_address} Success.\n')
        print("\n成功設定禁止自動更新，5秒後自動關閉視窗，也可直接關閉")
        for i in range(0, 5):
            print(f'{5 - i}')
            time.sleep(1)
    except subprocess.CalledProcessError as e:
        input(f"\n設定發生錯誤: {e}，請按任意鍵結束或直接關閉視窗。")
    except FileNotFoundError:
        input(f"\n無法找到 LGPO 工具或備份資料夾，請檢查路徑: {lgpo_path} 或 {backup_folder}。")
else:
    try:
        print("非管理員權限，嘗試以管理員身份重新啟動...")
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, ' '.join(sys.argv), None, 1
        )
    except Exception as e:
        input(f"無法以管理員權限重新啟動: {e}，請手動以管理員身份執行該程式。")

# 封裝
# pyinstaller --onefile --name "DisableAutoUpdate_V1.0a" disable_auto_update.py
