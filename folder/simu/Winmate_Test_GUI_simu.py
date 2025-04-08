import os
import time
import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext, font
import subprocess
import threading
import psutil

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
    button.breathe_dir = 1  # 1 表示變亮，-1 表示變暗

    # 可以自行微調這些參數來改變呼吸節奏和亮暗範圍
    max_phase = 15  # 呼吸來回的細分總步數
    interval = 15  # 每步的時間間隔 (毫秒)

    # 定義「暗」與「亮」兩端顏色（僅針對黃系做輕微變化即可）
    # 例如從 #FFF200 (亮黃) 到 #FFD800 (稍暗的黃)
    dark_rgb = (0xFF, 0xFF, 0xB9)  # #FFD800
    bright_rgb = (0xF9, 0xF9, 0x00)  # #FFF200

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
        # 先把按鈕拉到 #FFFF00，然後開始呼吸
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
# 以下為原測試程式邏輯
# --------------------------------------------------

success_check = False


def get_mac_address_by_name():
    for interface, addrs in psutil.net_if_addrs().items():
        if interface == "乙太網路 2":
            for addr in addrs:
                if addr.family == psutil.AF_LINK:  # AF_LINK 表示 MAC 地址
                    return addr.address
    return "Unknown"


def start_all():
    bt()
    ping()
    wr()
    rs485()


def start_all_thread():
    start_button.config(state=tk.DISABLED)
    BT_subprocess_exe_button.config(state=tk.DISABLED)
    PingTest_subprocess_exe_button.config(state=tk.DISABLED)
    WR_subprocess_exe_button.config(state=tk.DISABLED)
    RS485_subprocess_exe_button.config(state=tk.DISABLED)
    threading.Thread(target=bt).start()
    threading.Thread(target=ping).start()
    threading.Thread(target=rs485).start()
    threading.Thread(target=wr).start()


def BT_thread():
    start_button.config(state=tk.DISABLED)
    BT_subprocess_exe_button.config(state=tk.DISABLED)
    threading.Thread(target=bt).start()


def Ping_thread():
    start_button.config(state=tk.DISABLED)
    PingTest_subprocess_exe_button.config(state=tk.DISABLED)
    threading.Thread(target=ping).start()


def WR_thread():
    start_button.config(state=tk.DISABLED)
    WR_subprocess_exe_button.config(state=tk.DISABLED)
    threading.Thread(target=wr).start()


def RS485_thread():
    start_button.config(state=tk.DISABLED)
    RS485_subprocess_exe_button.config(state=tk.DISABLED)
    threading.Thread(target=rs485).start()


def display_result(text):
    result_text.insert(tk.END, text + "\n")
    result_text.see(tk.END)


def check_button_thread():
    threading.Thread(target=check_button).start()


def check_button():
    global success_check
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
        if (button_list[0].cget("state") ==
                button_list[1].cget("state") ==
                button_list[2].cget("state") ==
                button_list[3].cget("state") == "normal"):
            start_button.config(state=tk.NORMAL)

        # 若所有按鈕都是綠燈(#00ff00)且還沒寫入檔案，就寫一筆 success log
        if (button_list[0].cget("bg") ==
                button_list[1].cget("bg") ==
                button_list[2].cget("bg") ==
                button_list[3].cget("bg") == "#00ff00"
                and success_check == False):
            with open(".\\log\\Winmate_Test_log.txt", 'a', encoding='utf-8') as file:
                mac_address = get_mac_address_by_name()
                file.write(f'{datetime.now().strftime("%Y%m%d:%H%M%S")}: {mac_address} Success.\n')
            success_check = True

        time.sleep(1)


def bt():
    fade_to_color(BT_subprocess_exe_button, 'yellow')  # 呼吸效果
    display_result('藍牙: Testing...')
    try:
        result = subprocess.run('0\\Winmate_Test_GUI\\exes_simu\\BT_subprocess_simu.exe', capture_output=True, text=True)
        output = result.stdout
    except Exception as e:
        output = str(e)

    if 'PASS' in output:
        fade_to_color(BT_subprocess_exe_button, 'green')
    else:
        fade_to_color(BT_subprocess_exe_button, 'red')

    BT_subprocess_exe_button.config(state=tk.NORMAL)
    return display_result(output)


def ping():
    name_list = ['乙太網路', '乙太網路 2', 'Wi-Fi 2']
    fade_to_color(PingTest_subprocess_exe_button, 'yellow')  # 呼吸效果
    display_result('RJ45/Wi-Fi: Testing...')
    try:
        result = subprocess.run('0\\Winmate_Test_GUI\\exes_simu\\PingTest_subprocess_simu.exe', capture_output=True, text=True)
        output = result.stdout
    except Exception as e:
        output = str(e)

    if output.count("PASS") == 3:
        fade_to_color(PingTest_subprocess_exe_button, 'green')
    else:
        for i in name_list:
            if i in output:
                name_list.remove(i)
        output = f'RJ45/WiFi: {", ".join(name_list)} Failed'
        fade_to_color(PingTest_subprocess_exe_button, 'red')

    PingTest_subprocess_exe_button.config(state=tk.NORMAL)
    return display_result(output)


def wr():
    fade_to_color(WR_subprocess_exe_button, 'yellow')  # 呼吸效果
    display_result('USB: Testing...')
    try:
        result = subprocess.run('0\\Winmate_Test_GUI\\exes_simu\\WR_subprocess_simu.exe', capture_output=True, text=True)
        output = result.stdout
    except Exception as e:
        output = str(e)

    if output.count("PASS") == 2:
        fade_to_color(WR_subprocess_exe_button, 'green')
    else:
        fade_to_color(WR_subprocess_exe_button, 'red')

    if os.path.exists('WR_report.txt'):
        os.remove('WR_report.txt')
    WR_subprocess_exe_button.config(state=tk.NORMAL)
    return display_result(output)


def rs485():
    fade_to_color(RS485_subprocess_exe_button, 'yellow')  # 呼吸效果
    display_result('RS485: Testing...')
    try:
        result = subprocess.run('0\\Winmate_Test_GUI\\exes_simu\\RS485_simu.exe', capture_output=True, text=True)
        output = result.stdout
    except Exception as e:
        output = str(e)

    print(output)
    if 'PASS' in output:
        fade_to_color(RS485_subprocess_exe_button, 'green')
    else:
        display_result('RS485: Failed')
        fade_to_color(RS485_subprocess_exe_button, 'red')

    if os.path.exists('485_report.txt'):
        os.remove('485_report.txt')
    RS485_subprocess_exe_button.config(state=tk.NORMAL)
    return display_result(output)


def close_window():
    window.destroy()


if __name__ == "__main__":
    window = tk.Tk()
    window.title("WinMate控制器功能測試V1.1d")
    window.attributes('-fullscreen', True)
    font_style = font.Font(size=20)

    start_button = tk.Button(window, text="全部啟動", width=140, height=3, command=start_all_thread, font=font_style)
    start_button.grid(row=0, column=0, columnspan=5, pady=10)

    exes = [
        '.\\0\\Winmate_Test_GUI\\exes_simu\\BT_subprocess_simu.exe',
        '.\\0\\Winmate_Test_GUI\\exes_simu\\PingTest_subprocess_simu.exe',
        '.\\0\\Winmate_Test_GUI\\exes_simu\\WR_subprocess_simu.exe',
        '.\\0\\Winmate_Test_GUI\\exes_simu\\RS485_simu.exe'
    ]
    button_width = 23
    button_height = 3

    # 預設先給個屬性用來記錄呼吸狀態
    BT_subprocess_exe_button = tk.Button(window, text="藍牙", width=button_width, height=button_height,
                                         font=font_style, command=BT_thread)
    BT_subprocess_exe_button.breathing = False  # 為了安全，先給個屬性
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

    check_button_thread()
    window.mainloop()

# pyinstaller --onefile --name "Winmate_Test_GUI_V1.1d" .\Winmate_Test_GUI.py
