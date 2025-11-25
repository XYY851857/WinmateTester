import os
import time
import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext, font, messagebox
import subprocess
import threading
import psutil
import json

# --------------------------------------------------
# 「漸變」與「呼吸」的輔助機制
# --------------------------------------------------
color_map = {
    "red": "#FF0000",
    "green": "#00FF00",
    "yellow": "#FFFF00",
    "SystemButtonFace": "#F0F0F0",  # Windows按鈕預設底色
}


def parse_color(color_str):
    """
    將 color_str 轉換成 (r, g, b) 數值。
    color_str 可能是 #RRGGBB 或在 color_map 裡的顏色名稱。
    無法解析時回傳 None。
    """
    if color_str in color_map:
        color_str = color_map[color_str]
    if isinstance(color_str, str) and color_str.startswith("#") and len(color_str) == 7:
        try:
            r = int(color_str[1:3], 16)
            g = int(color_str[3:5], 16)
            b = int(color_str[5:7], 16)
            return (r, g, b)
        except:
            return None
    return None


def stop_breathing(button):
    """
    停止該按鈕的呼吸效果。
    """
    button.breathing = False


def start_breathing(button):
    """
    讓按鈕進入「呼吸燈」效果，不斷地在一小段亮度範圍內明暗交替。
    直到被設定新的顏色（呼叫 fade_to_color(button, X)）才停止。
    """
    button.breathing = True
    button.breathe_phase = 0  # 用來記錄目前到哪個步驟
    button.breathe_dir = 1    # 1 表示變亮，-1 表示變暗

    # 可以自行微調這些參數來改變呼吸節奏和亮暗範圍
    max_phase = 15  # 呼吸來回的細分總步數
    interval = 15   # 每步的時間間隔 (毫秒)

    # 定義「暗」與「亮」兩端顏色（僅針對黃系做輕微變化即可）
    dark_rgb = (0xFF, 0xFF, 0xB9)
    bright_rgb = (0xF9, 0xF9, 0x00)

    def breathe_step():
        if not button.breathing:
            return  # 已被要求停止

        alpha = button.breathe_phase / max_phase
        r = int(dark_rgb[0] + alpha * (bright_rgb[0] - dark_rgb[0]))
        g = int(dark_rgb[1] + alpha * (bright_rgb[1] - dark_rgb[1]))
        b = int(dark_rgb[2] + alpha * (bright_rgb[2] - dark_rgb[2]))
        button.config(bg=f"#{r:02x}{g:02x}{b:02x}")

        button.breathe_phase += button.breathe_dir
        # 走到亮端就往暗端走，走到暗端就往亮端走
        if button.breathe_phase >= max_phase:
            button.breathe_dir = -1
        elif button.breathe_phase <= 0:
            button.breathe_dir = 1

        button.after(interval, breathe_step)

    breathe_step()


def fade_to_color(button, target_color, steps=10, interval=10):
    """
    將按鈕目前的背景顏色在 steps 步內漸變到 target_color，
    若 target_color 為 "yellow"，則改用「呼吸效果」。
    """
    # 若之前在呼吸，先停止
    stop_breathing(button)

    # 若是要變成「呼吸效果的黃色」，先簡單漸變到黃，然後開始呼吸
    if target_color == "yellow":
        do_simple_fade(button, target_color, steps, interval, on_complete=start_breathing)
    else:
        # 一般顏色，就做一般的漸變
        do_simple_fade(button, target_color, steps, interval)


def do_simple_fade(button, target_color, steps, interval, on_complete=None):
    """
    實際做漸層的函式。漸層完成後如有指定 on_complete 就呼叫。
    """
    start_color_str = button.cget("bg")
    start_rgb = parse_color(start_color_str)
    end_rgb = parse_color(target_color)

    # 無法解析(如系統預設顏色)就直接設定到目標色
    if not start_rgb or not end_rgb:
        button.config(bg=target_color)
        if on_complete:
            on_complete(button)
        return

    r1, g1, b1 = start_rgb
    r2, g2, b2 = end_rgb

    step_count = 0

    def do_step():
        nonlocal step_count
        alpha = step_count / steps
        r = int(r1 + alpha * (r2 - r1))
        g = int(g1 + alpha * (g2 - g1))
        b = int(b1 + alpha * (b2 - b1))
        button.config(bg=f"#{r:02x}{g:02x}{b:02x}")

        if step_count < steps:
            step_count += 1
            button.after(interval, do_step)
        else:
            # 漸層完成
            if on_complete:
                on_complete(button)

    do_step()


# --------------------------------------------------
# 主要測試程式邏輯
# --------------------------------------------------

# 四個要檢查的執行檔路徑
EXES = {
    "BT":    ".\\0\\Winmate_Test_GUI\\exes\\BT_subprocess.exe",
    "Ping":  ".\\0\\Winmate_Test_GUI\\exes\\PingTest_subprocess.exe",
    "WR":    ".\\0\\Winmate_Test_GUI\\exes\\WR_subprocess.exe",
    "RS485": ".\\0\\Winmate_Test_GUI\\exes\\RS485.exe",
}

TIMEOUT_SECONDS = 90

# --------------------------------------------------
# JSON log 記錄相關
# --------------------------------------------------
LOG_DIR = ".\\log"

def ensure_log_dir():
    """確保 log 資料夾存在"""
    if LOG_DIR and not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)

def get_log_path():
    """依照當天日期決定 log 檔名，例如: .\\log\\Winmate_Test_log_20251125.json"""
    ensure_log_dir()
    date_str = datetime.now().strftime("%Y%m%d")
    return os.path.join(LOG_DIR, f"Winmate_Test_log_{date_str}.json")

def load_log_data():
    """讀取 JSON 紀錄，若檔案不存在或格式錯誤則回傳空 dict"""
    path = get_log_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # 檔案壞掉或內容非 JSON，就重新開始
        return {}

def save_log_data(data):
    """將紀錄寫回 JSON 檔"""
    path = get_log_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def update_test_log(test_name, is_ok):
    """
    更新單一測試項目的結果。
    規則：
    - 測試通過時寫入 "OK"。
    - 測試失敗時寫入 "NG"。
    - 若該項目已經是 "OK"，之後就算 NG 也不會覆寫掉 OK。
    JSON 結構（單一檔案，不再內含日期層）：
    {
        "XX:XX:XX:XX:XX": {
            "BT": "OK",
            "RJ-45/Wi-Fi": "NG",
            "USB": "OK",
            "RS-485": "NG"
        },
        "YY:YY:YY:YY:YY": {
            "BT": "NG"
        }
    }
    """
    mac_address = get_mac_address_by_name()

    data = load_log_data()
    if mac_address not in data:
        data[mac_address] = {}

    current = data[mac_address].get(test_name)

    # 若已經是 OK，就不再覆寫（保持 OK 優先權）
    if current == "OK":
        return

    # 依照 is_ok 決定要寫入 OK 或 NG
    data[mac_address][test_name] = "OK" if is_ok else "NG"
    save_log_data(data)

def get_mac_address_by_name():
    for interface, addrs in psutil.net_if_addrs().items():
        if interface == "乙太網路 2":
            for addr in addrs:
                if addr.family == psutil.AF_LINK:  # AF_LINK 表示 MAC 地址
                    return addr.address
    return "Unknown"

def all_exes_exist():
    """ 檢查所有必須的 exe 是否都存在 """
    return all(os.path.exists(path) for path in EXES.values())

def unlock_all_buttons():
    """ 重新解鎖五個按鈕(含四個測試與「全部啟動」) """
    start_button.config(state=tk.NORMAL)
    BT_subprocess_exe_button.config(state=tk.NORMAL)
    PingTest_subprocess_exe_button.config(state=tk.NORMAL)
    WR_subprocess_exe_button.config(state=tk.NORMAL)
    RS485_subprocess_exe_button.config(state=tk.NORMAL)

def check_all_exes_and_alert_if_missing():
    """
    若有任一 exe 不存在，則彈出錯誤訊息並將四大按鈕變成紅色，
    並且解鎖按鈕，回傳 False；否則回傳 True。
    """
    if not all_exes_exist():
        messagebox.showerror("錯誤", "執行組建缺少，請再試一次")
        # 將四個按鈕全部變紅
        fade_to_color(BT_subprocess_exe_button, "red", steps=1, interval=1)
        fade_to_color(PingTest_subprocess_exe_button, "red", steps=1, interval=1)
        fade_to_color(WR_subprocess_exe_button, "red", steps=1, interval=1)
        fade_to_color(RS485_subprocess_exe_button, "red", steps=1, interval=1)
        # 解鎖按鈕
        unlock_all_buttons()
        return False
    return True

def check_single_exe_and_alert_if_missing(button, exe_path):
    """
    檢查單一執行檔是否存在。
    若不存在：彈出錯誤訊息、將該按鈕變紅，並解鎖按鈕，回傳 False。
    若存在：回傳 True。
    """
    if not os.path.exists(exe_path):
        messagebox.showerror("錯誤", "執行組建缺少，請再試一次")
        fade_to_color(button, "red", steps=1, interval=1)
        # 解鎖按鈕 (含 start_button 與四個測試按鈕)
        unlock_all_buttons()
        return False
    return True


# --------------------------------------------------
# 四大測試：每個都有 timeout=90 秒機制
# --------------------------------------------------
def bt():
    fade_to_color(BT_subprocess_exe_button, 'yellow')
    display_result('藍牙: Testing...')
    try:
        result = subprocess.run(EXES["BT"], capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        output = result.stdout
    except subprocess.TimeoutExpired:
        fade_to_color(BT_subprocess_exe_button, 'red')
        display_result('藍牙: Timeout Fail')
        BT_subprocess_exe_button.config(state=tk.NORMAL)
        return
    except Exception as e:
        output = str(e)

    if 'PASS' in (output or ''):
        fade_to_color(BT_subprocess_exe_button, 'green')
        is_ok = True
    else:
        fade_to_color(BT_subprocess_exe_button, 'red')
        is_ok = False

    update_test_log("BT", is_ok)

    BT_subprocess_exe_button.config(state=tk.NORMAL)
    return display_result(output)


def ping():
    fade_to_color(PingTest_subprocess_exe_button, 'yellow')  # 呼吸效果
    display_result('RJ45/Wi-Fi: Testing...')
    try:
        result = subprocess.run(EXES["Ping"], capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        output = result.stdout
    except subprocess.TimeoutExpired:
        fade_to_color(PingTest_subprocess_exe_button, 'red')
        display_result('RJ45/WiFi: Timeout Fail')
        PingTest_subprocess_exe_button.config(state=tk.NORMAL)
        return
    except Exception as e:
        output = str(e)

    name_list = ['乙太網路', '乙太網路 2', 'Wi-Fi 2']
    # 假設要檢查 PASS == 4
    if output and output.count("PASS") == 4:
        fade_to_color(PingTest_subprocess_exe_button, 'green')
        is_ok = True
    else:
        # 當部分介面失敗時輸出是 "Failed" ?
        # 顯示哪個介面 Failed
        for i in name_list[:]:
            if i in (output or ''):
                name_list.remove(i)
        out_str = f'RJ45/WiFi: {", ".join(name_list)} Failed'
        fade_to_color(PingTest_subprocess_exe_button, 'red')
        output += "\n" + out_str
        is_ok = False

    update_test_log("RJ-45/Wi-Fi", is_ok)

    PingTest_subprocess_exe_button.config(state=tk.NORMAL)
    return display_result(output)


def wr():
    fade_to_color(WR_subprocess_exe_button, 'yellow')
    display_result('USB: Testing...')
    try:
        result = subprocess.run(EXES["WR"], capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        output = result.stdout
    except subprocess.TimeoutExpired:
        fade_to_color(WR_subprocess_exe_button, 'red')
        display_result('USB: Timeout Fail')
        WR_subprocess_exe_button.config(state=tk.NORMAL)
        return
    except Exception as e:
        output = str(e)

    if output and output.count("PASS") == 2:
        fade_to_color(WR_subprocess_exe_button, 'green')
        is_ok = True
    else:
        fade_to_color(WR_subprocess_exe_button, 'red')
        is_ok = False

    update_test_log("USB", is_ok)

    if os.path.exists('WR_report.txt'):
        os.remove('WR_report.txt')
    WR_subprocess_exe_button.config(state=tk.NORMAL)
    return display_result(output)


def rs485():
    fade_to_color(RS485_subprocess_exe_button, 'yellow')
    display_result('RS485: Testing...')
    try:
        result = subprocess.run(EXES["RS485"], capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        output = result.stdout
    except subprocess.TimeoutExpired:
        fade_to_color(RS485_subprocess_exe_button, 'red')
        display_result('RS485: Timeout Fail')
        RS485_subprocess_exe_button.config(state=tk.NORMAL)
        return
    except Exception as e:
        output = str(e)

    print(output)
    if 'PASS' in (output or ''):
        fade_to_color(RS485_subprocess_exe_button, 'green')
        is_ok = True
    else:
        display_result('RS485: Failed')
        fade_to_color(RS485_subprocess_exe_button, 'red')
        is_ok = False

    update_test_log("RS-485", is_ok)

    if os.path.exists('485_report.txt'):
        os.remove('485_report.txt')
    RS485_subprocess_exe_button.config(state=tk.NORMAL)
    return display_result(output)


# --------------------------------------------------
# 按鈕事件
# --------------------------------------------------
def start_all():
    # 在真正執行四個測試前，先檢查四個執行檔是否都存在
    if not check_all_exes_and_alert_if_missing():
        return

    # 一次啟動四個測試，採用四個 Thread 並行執行
    t1 = threading.Thread(target=bt)
    t2 = threading.Thread(target=ping)
    t3 = threading.Thread(target=wr)
    t4 = threading.Thread(target=rs485)
    t1.start()
    t2.start()
    t3.start()
    t4.start()


def start_all_thread():
    start_button.config(state=tk.DISABLED)
    BT_subprocess_exe_button.config(state=tk.DISABLED)
    PingTest_subprocess_exe_button.config(state=tk.DISABLED)
    WR_subprocess_exe_button.config(state=tk.DISABLED)
    RS485_subprocess_exe_button.config(state=tk.DISABLED)
    threading.Thread(target=start_all).start()


def BT_thread():
    start_button.config(state=tk.DISABLED)
    BT_subprocess_exe_button.config(state=tk.DISABLED)

    if not check_single_exe_and_alert_if_missing(BT_subprocess_exe_button, EXES["BT"]):
        return  # 已在函式內解鎖，這邊直接結束

    threading.Thread(target=bt).start()


def Ping_thread():
    start_button.config(state=tk.DISABLED)
    PingTest_subprocess_exe_button.config(state=tk.DISABLED)

    if not check_single_exe_and_alert_if_missing(PingTest_subprocess_exe_button, EXES["Ping"]):
        return

    threading.Thread(target=ping).start()


def WR_thread():
    start_button.config(state=tk.DISABLED)
    WR_subprocess_exe_button.config(state=tk.DISABLED)

    if not check_single_exe_and_alert_if_missing(WR_subprocess_exe_button, EXES["WR"]):
        return

    threading.Thread(target=wr).start()


def RS485_thread():
    start_button.config(state=tk.DISABLED)
    RS485_subprocess_exe_button.config(state=tk.DISABLED)

    if not check_single_exe_and_alert_if_missing(RS485_subprocess_exe_button, EXES["RS485"]):
        return

    threading.Thread(target=rs485).start()


def display_result(text):
    if text:
        result_text.insert(tk.END, text + "\n")
        result_text.see(tk.END)

def check_button_thread():
    threading.Thread(target=check_button).start()

def check_button():
    while True:
        button_list = [
            BT_subprocess_exe_button,
            PingTest_subprocess_exe_button,
            WR_subprocess_exe_button,
            RS485_subprocess_exe_button,
        ]
        for button in button_list:
            state = button.cget("state")
            if state == 'disabled':
                start_button.config(state=tk.DISABLED)

        # 當所有按鈕都恢復到 normal，才把 start_button 打開
        if all(button.cget("state") == "normal" for button in button_list):
            start_button.config(state=tk.NORMAL)

        # (移除 success_check 及舊的 txt log 寫入)
        time.sleep(1)

def close_window():
    window.destroy()


# --------------------------------------------------
# 主程式啟動
# --------------------------------------------------
if __name__ == "__main__":
    window = tk.Tk()
    window.title("WinMate控制器功能測試V1.1d")
    window.attributes('-fullscreen', True)
    font_style = font.Font(size=20)

    start_button = tk.Button(window, text="全部啟動", width=140, height=3, command=start_all_thread, font=font_style)
    start_button.grid(row=0, column=0, columnspan=5, pady=10)

    button_width = 23
    button_height = 3

    # 預設先給個屬性用來記錄呼吸狀態
    BT_subprocess_exe_button = tk.Button(window, text="藍牙", width=button_width, height=button_height,
                                         font=font_style, command=BT_thread)
    BT_subprocess_exe_button.breathing = False
    BT_subprocess_exe_button.grid(row=1, column=0, padx=5, pady=5)

    PingTest_subprocess_exe_button = tk.Button(window, text="RJ45/WiFi", width=button_width, height=button_height,
                                               font=font_style, command=Ping_thread)
    PingTest_subprocess_exe_button.breathing = False
    PingTest_subprocess_exe_button.grid(row=1, column=1, padx=5, pady=5)

    WR_subprocess_exe_button = tk.Button(window, text="USB", width=button_width, height=button_height,
                                         font=font_style, command=WR_thread)
    WR_subprocess_exe_button.breathing = False
    WR_subprocess_exe_button.grid(row=1, column=2, padx=5, pady=5)

    RS485_subprocess_exe_button = tk.Button(window, text="RS485", width=button_width, height=button_height,
                                            font=font_style, command=RS485_thread)
    RS485_subprocess_exe_button.breathing = False
    RS485_subprocess_exe_button.grid(row=1, column=3, padx=5, pady=5)

    result_text = scrolledtext.ScrolledText(window, width=240, height=30, font=font_style)
    result_text.grid(row=2, column=0, columnspan=5, padx=10, pady=10)

    exit_button = tk.Button(window, text='離開端口測試程式', width=240, font=font_style, command=close_window)
    exit_button.grid(row=3, column=0, columnspan=5, padx=10, pady=10)

    window.grid_rowconfigure(0, weight=0)
    window.grid_rowconfigure(1, weight=0)
    window.grid_rowconfigure(2, weight=1)

    window.grid_columnconfigure(0, weight=1)
    window.grid_columnconfigure(1, weight=1)
    window.grid_columnconfigure(2, weight=1)
    window.grid_columnconfigure(3, weight=1)
    window.grid_columnconfigure(4, weight=1)

    # 啟動程式時，先檢查四個執行檔是否都存在，不存在就彈窗並把四按鈕變紅，最後解鎖按鈕
    check_all_exes_and_alert_if_missing()

    check_button_thread()
    window.mainloop()

# pyinstaller --onefile --name "Winmate_Test_GUI_V1.1d" .\Winmate_Test_GUI.py
