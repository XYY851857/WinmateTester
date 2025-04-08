import tkinter as tk
import tkinter.messagebox as mb
import requests
import subprocess
import sys
import threading

# 假設 tDS-700 預設 IP
TDS700_DEFAULT_IP = "192.168.0.100"


def ping_host(ip):
    """
    使用系統 ping 指令來測試某 IP 是否可通。
    在 Windows 下會使用 '-n 1'，在 Linux/macOS 下使用 '-c 1'。
    回傳 True 表示 Ping 成功，False 表示 Ping 失敗。
    """
    param = '-n' if sys.platform.startswith('win') else '-c'
    command = ["ping", param, "1", ip]
    try:
        result = subprocess.run(command, capture_output=True)
        return (result.returncode == 0)
    except Exception:
        return False


def check_ping_16(app):
    """
    在後台 Ping 192.168.255.16 並依結果呼叫 app.mark_2225i()
    """
    def run():
        status = ping_host("192.168.255.16")
        # 回到主執行緒做 UI 更新
        app.master.after(0, lambda: app.mark_2225i(status))
    threading.Thread(target=run, daemon=True).start()


def check_ping_17(app):
    """
    在後台 Ping 192.168.255.17 並依結果呼叫 app.mark_724i()
    """
    def run():
        status = ping_host("192.168.255.17")
        app.master.after(0, lambda: app.mark_724i(status))
    threading.Thread(target=run, daemon=True).start()


def set_device_ip(current_ip, new_ip):
    """
    傳送 CGI 指令給 tDS-700 進行 IP 設定 (僅範例)。
    若發生連線問題就由上層去彈出對話窗。
    """
    url = f"http://{current_ip}/assign.cgi"
    params = {
        'ip': new_ip
    }
    resp = requests.get(url, params=params, timeout=5)
    if resp.status_code == 200:
        return f"設定 IP 成功：{new_ip}\n請稍後嘗試以新 IP 連線！"
    else:
        return f"設定失敗，HTTP 狀態碼：{resp.status_code}"


class IPKeypadApp:
    def __init__(self, master):
        self.master = master
        self.master.title("tDS-700 IP 設定")

        # 預設顯示於數字鍵盤輸入框的 IP
        self.ip_var = tk.StringVar(value="192.168.255.1")

        # 用來放結果訊息
        self.result_var = tk.StringVar(value="")

        # 主框架
        main_frame = tk.Frame(master)
        main_frame.pack(padx=10, pady=10)

        # 說明文字
        tk.Label(main_frame, font=10, text="請輸入欲設定的 IP：").grid(row=0, column=0, columnspan=3, pady=5)

        # IP 輸入框
        self.entry = tk.Entry(main_frame, textvariable=self.ip_var, width=16, font=10, justify='center')
        self.entry.grid(row=1, column=0, columnspan=3, pady=5)

        # 數字鍵盤按鈕 (0~9, '.', '刪除')
        keypad_values = [
            ['7', '8', '9'],
            ['4', '5', '6'],
            ['1', '2', '3'],
            ['.', '0', '刪除']
        ]
        for row_index, row_values in enumerate(keypad_values):
            for col_index, val in enumerate(row_values):
                btn = tk.Button(main_frame, text=val, width=10, height=4, font=10,
                                command=lambda v=val: self.on_keypad_click(v))
                btn.grid(row=row_index + 2, column=col_index, padx=2, pady=2)

        # 確定/送出的按鈕
        confirm_button = tk.Button(main_frame, text="確定", width=16, font=10, command=self.on_confirm)
        confirm_button.grid(row=6, column=0, columnspan=3, pady=10)

        # 快速鍵按鈕 (2225i & 724i)
        self.btn_2225i = tk.Button(main_frame, text="2225i", width=10, height=2, font=10,
                                   command=self.set_2225i)
        self.btn_2225i.grid(row=7, column=0, padx=2, pady=2)

        self.btn_724i = tk.Button(main_frame, text="724i", width=10, height=2, font=10,
                                  command=self.set_724i)
        self.btn_724i.grid(row=7, column=2, padx=2, pady=2)

        # 顯示執行結果
        tk.Label(main_frame, textvariable=self.result_var, fg="blue").grid(row=8, column=0, columnspan=3)

    def on_keypad_click(self, value):
        """ 處理數字鍵盤被按下的事件 """
        if value == "刪除":
            current_text = self.ip_var.get()
            self.ip_var.set(current_text[:-1])
        else:
            self.ip_var.set(self.ip_var.get() + value)

    def on_confirm(self):
        """
        使用者按下「確定」後，嘗試連線設定 IP。
        若連線失敗，彈出簡單的「連線失敗」視窗。
        """
        current_device_ip = TDS700_DEFAULT_IP
        new_ip = self.ip_var.get().strip()
        if not new_ip:
            self.result_var.set("IP 不可為空白！")
            return

        try:
            result = set_device_ip(current_device_ip, new_ip)
            self.result_var.set(result)
        except requests.exceptions.RequestException:
            mb.showerror("連線失敗", "連線失敗")

    def set_2225i(self):
        """ 點選 2225i 時將 IP 欄位改為 192.168.255.16 """
        self.ip_var.set("192.168.255.16")

    def set_724i(self):
        """ 點選 724i 時將 IP 欄位改為 192.168.255.17 """
        self.ip_var.set("192.168.255.17")

    def mark_2225i(self, has_ping):
        """ 根據 ping 結果，將 2225i 按鈕漸變為綠色或灰色 """
        if has_ping:
            self.fade_background(self.btn_2225i, "green")
        else:
            self.fade_background(self.btn_2225i, "gray")

    def mark_724i(self, has_ping):
        """ 根據 ping 結果，將 724i 按鈕漸變為綠色或灰色 """
        if has_ping:
            self.fade_background(self.btn_724i, "green")
        else:
            self.fade_background(self.btn_724i, "gray")

    def fade_background(self, widget, target_color, steps=10, delay=10):
        """
        讓 widget 的背景色從目前顏色漸漸變到 target_color。
          - steps: 漸變分成幾步
          - delay: 每一步的延遲 (毫秒)
        """
        # 先嘗試抓取 widget 目前背景色
        # 比如 "SystemButtonFace"、"#rrggbb" 或 "grey" 等等。
        # widget.winfo_rgb(color) 會回傳 (r, g, b) in 0..65535
        try:
            start_color = widget.cget("bg")
        except:
            start_color = "SystemButtonFace"

        r1, g1, b1 = self.master.winfo_rgb(start_color)
        r2, g2, b2 = self.master.winfo_rgb(target_color)

        # 在 step 之間插值計算
        def do_step(step=0):
            if step > steps:
                return  # 結束

            # 計算比例
            fraction = step / steps
            # 新的 RGB = 起點 + fraction * (終點 - 起點)
            nr = int(r1 + (r2 - r1) * fraction)
            ng = int(g1 + (g2 - g1) * fraction)
            nb = int(b1 + (b2 - b1) * fraction)

            # 0..65535 轉成 0..255，再組成 #RRGGBB
            nr_8 = nr >> 8
            ng_8 = ng >> 8
            nb_8 = nb >> 8
            hex_color = f"#{nr_8:02x}{ng_8:02x}{nb_8:02x}"

            widget.config(bg=hex_color, fg="black")
            widget.after(delay, do_step, step+1)

        do_step()


def main():
    root = tk.Tk()
    app = IPKeypadApp(root)

    # 開程式後就開始嘗試 Ping .16 與 .17，不阻塞主程式
    check_ping_16(app)
    check_ping_17(app)

    root.mainloop()


if __name__ == "__main__":
    main()
