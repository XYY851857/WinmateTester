import os.path
import time
import tkinter as tk
from tkinter import scrolledtext, font
import subprocess
import threading


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
                for step in button_list:
                    start_button.config(state=tk.DISABLED)
        if button_list[0].cget("state") == button_list[1].cget("state") == button_list[2].cget("state") == button_list[3].cget("state") and button_list[0].cget("state") == "normal":
            start_button.config(state=tk.NORMAL)
        time.sleep(1)


def bt():
    BT_subprocess_exe_button.config(bg='yellow')
    display_result('藍牙: Testing...')
    try:
        result = subprocess.run(f'exes\\BT_subprocess.exe', capture_output=True, text=True)
        output = result.stdout
    except Exception as e:
        output = str(e)
    if 'PASS' in output:
        BT_subprocess_exe_button.config(bg='green')
    else:
        BT_subprocess_exe_button.config(bg='red')
    BT_subprocess_exe_button.config(state=tk.NORMAL)
    return display_result(output)


def ping():
    name_list = ['乙太網路', '乙太網路 2', 'Wi-Fi 2']
    PingTest_subprocess_exe_button.config(bg='yellow')
    display_result('RJ45/Wi-Fi: Testing...')
    try:
        result = subprocess.run(f'exes\\PingTest_subprocess.exe', capture_output=True, text=True)
        output = result.stdout
    except Exception as e:
        output = str(e)
    if output.count("PASS") == 3:
        PingTest_subprocess_exe_button.config(bg='green')
    else:
        for i in name_list:
            if i in output:
                name_list.remove(i)
        output = f'RJ45/WiFi: {', '.join(name_list)} Failed'
        PingTest_subprocess_exe_button.config(bg='red')
    PingTest_subprocess_exe_button.config(state=tk.NORMAL)
    return display_result(output)


def wr():
    WR_subprocess_exe_button.config(bg='yellow')
    display_result('USB: Testing...')
    try:
        result = subprocess.run(f'exes\\WR_subprocess.exe', capture_output=True, text=True)
        output = result.stdout
    except Exception as e:
        output = str(e)
    if output.count("PASS") == 2:
        WR_subprocess_exe_button.config(bg='green')
    else:
        WR_subprocess_exe_button.config(bg='red')
    if os.path.exists('WR_report.txt'):
        os.remove('WR_report.txt')
    WR_subprocess_exe_button.config(state=tk.NORMAL)
    return display_result(output)


def rs485():
    RS485_subprocess_exe_button.config(bg='yellow')
    display_result('RS485: Testing...')
    try:
        result = subprocess.run(f'exes\\RS485.exe', capture_output=True, text=True)
        output = result.stdout
    except Exception as e:
        output = str(e)
    print(output)
    if 'PASS' in output:
        RS485_subprocess_exe_button.config(bg='green')
    else:
        RS485_subprocess_exe_button.config(bg='red')
    if os.path.exists('485_report.txt'):
        os.remove('485_report.txt')
    RS485_subprocess_exe_button.config(state=tk.NORMAL)
    return display_result(output)


window = tk.Tk()
window.title("WinMate控制器功能測試V1.0")
window.state('zoomed')
font_style = font.Font(size=20)
start_button = tk.Button(window, text="全部啟動", width=140, height=3, command=start_all_thread, font=font_style)
start_button.grid(row=0, column=0, columnspan=5, pady=10)

exes = ['.\\exes\\BT_subprocess.exe', '.\\exes\\PingTest_subprocess.exe', '.\\exes\\WR_subprocess.exe',
        '.\\exes\\RS485.exe']
button_width = 23
button_height = 3

BT_subprocess_exe_button = tk.Button(window, text=f"藍牙", width=button_width, height=button_height, font=font_style,
                                     command=BT_thread)
BT_subprocess_exe_button.grid(row=1, column=0, padx=5, pady=5)  # 藍牙測試按鈕

PingTest_subprocess_exe_button = tk.Button(window, text=f"RJ45/WiFi", width=button_width, height=button_height,
                                           font=font_style, command=Ping_thread)
PingTest_subprocess_exe_button.grid(row=1, column=1, padx=5, pady=5)  # WiFi設定及ping測試

WR_subprocess_exe_button = tk.Button(window, text=f"USB", width=button_width, height=button_height, font=font_style,
                                     command=WR_thread)
WR_subprocess_exe_button.grid(row=1, column=2, padx=5, pady=5)  # USB讀寫測試

RS485_subprocess_exe_button = tk.Button(window, text=f"RS485", width=button_width, height=button_height,
                                        font=font_style, command=RS485_thread)
RS485_subprocess_exe_button.grid(row=1, column=3, padx=5, pady=5)  # RS485測試

result_text = scrolledtext.ScrolledText(window, width=240, height=30, font=font_style)  # 建立輸出框
result_text.grid(row=2, column=0, columnspan=5, padx=10, pady=10)

window.grid_rowconfigure(0, weight=0)  # 權重設定
window.grid_rowconfigure(1, weight=0)
window.grid_rowconfigure(2, weight=1)

window.grid_columnconfigure(0, weight=1)
window.grid_columnconfigure(1, weight=1)
window.grid_columnconfigure(2, weight=1)
window.grid_columnconfigure(3, weight=1)
window.grid_columnconfigure(4, weight=1)

check_button_thread()
window.mainloop()
