import ctypes
import sys
import time
import subprocess
from pywinauto import Application
from pywinauto.keyboard import send_keys
import subprocess

# 設定網卡名稱
network_adapter = "乙太網路"
ip_address = "192.168.255.100"
subnet_mask = "255.255.0.0"
gateway = "192.168.0.1"

# **1. 設定靜態 IP**
try:
    set_ip_cmd = f'netsh interface ip set address name="{network_adapter}" static {ip_address} {subnet_mask} {gateway}'
    print(f"執行指令: {set_ip_cmd}")
    subprocess.run(set_ip_cmd, shell=True)
except Exception as e:
    print(f"設定失敗：{e}")


# 檢查是否有管理員權限
def is_admin():
    return ctypes.windll.shell32.IsUserAnAdmin() != 0


# 如果沒有管理員權限，則重新啟動腳本並以管理員模式執行
if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit()


# **1. 強制關閉 VxComm Utility**
try:
    print("正在關閉 VxComm Utility...")
    subprocess.run("taskkill /F /IM VxComm.exe", shell=True)
    time.sleep(2)  # 確保程式完全關閉
except Exception as e:
    print(f"無法關閉 VxComm Utility: {e}")

# **2. 執行 VxComm 安裝程式**
try:
    print("正在安裝 VxComm Utility...")
    subprocess.run(r".\VxComm_Auto\VxCommW7_v2.14.04_setup.exe /silent /norestart", shell=True)
    print("安裝完成，等待 5 秒以確保應用程式可用...")
    time.sleep(5)  # 等待安裝完成
except Exception as e:
    print(f"無法執行安裝程式: {e}")
    sys.exit()


# **3. 啟動應用程式**
try:
    app = Application().start(r"C:\ICPDAS\VxCommW7\VxComm.exe")
    time.sleep(5)  # 等待應用程式啟動
except Exception as e:
    print(f"無法啟動應用程式: {e}")
    sys.exit()


# **4. 連接應用程式**
try:
    app = Application().connect(title_re="VxComm Utility.*")
    window = app.window(title_re="VxComm Utility.*")
except Exception as e:
    print(f"無法連接應用程式: {e}")
    sys.exit()


# **5. 點擊 File -> Import Configuration**
try:
    window.menu_select("File->Import Configuration")
except Exception as e:
    print(f"選單點擊失敗: {e}")


# **6. 確認「確定」按鈕**
try:
    confirm_window = app.window(title_re="VxComm Utility - Import Configuration from file")
    confirm_button = confirm_window.child_window(title="確定")

    if confirm_button.exists():
        confirm_button.click()
        print("成功點擊「確定」按鈕")
    else:
        print("未找到「確定」按鈕")
except Exception as e:
    print(f"點擊按鈕失敗: {e}")


# **7. 開啟檔案**
try:
    file_dialog = app.window(title_re=".*開啟.*")
    file_path = r"D:\VxComm_Auto\2225i_724i_config.xml"
    file_dialog.child_window(class_name="Edit").set_text(file_path)

    # **模擬按下 Enter 鍵**
    send_keys("{ENTER}")
    time.sleep(5)
    send_keys("{ENTER}")
    time.sleep(0.1)
    send_keys("{ENTER}")

    print(f"成功選擇檔案: {file_path} 並開啟")
except Exception as e:
    print(f"無法處理檔案對話框: {e}")


# **8. 點擊 Tools -> Restart Driver**
try:
    window.menu_select("Tools -> Restart Driver")
    time.sleep(0.1)
    send_keys("{RIGHT}")
    time.sleep(0.1)
    send_keys("{ENTER}")
except Exception as e:
    print(f"選單點擊失敗: {e}")
