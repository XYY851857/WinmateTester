import subprocess
import time
import sys
import ctypes
import os
import re
import glob
import tkinter as tk
from typing import List


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_generic_tool(name: str):
    """根據子資料夾名稱 name，優先在
    D:\S8521\Update_Repo\{name}\{name}_V*.exe 找最新版本；
    若找不到，再到 D:\S8521\Update_Repo\{name}_V*.exe 搜尋。
    """
    base_dir = r"D:\S8521\Update_Repo"
    candidates = []
    pattern = re.compile(fr"{re.escape(name)}_V(\d+)_(\d+)_(\d+)\.exe", re.I)

    # 1) 子資料夾內搜尋
    folder = os.path.join(base_dir, name)
    if os.path.isdir(folder):
        for file in glob.glob(os.path.join(folder, f"{name}_V*.exe")):
            m = pattern.search(os.path.basename(file))
            if m:
                ver_tuple = tuple(int(x) for x in m.groups())
                candidates.append((ver_tuple, file))

    # 2) 直接在 Update_Repo 根目錄搜尋（與使用者示例相容）
    for file in glob.glob(os.path.join(base_dir, f"{name}_V*.exe")):
        m = pattern.search(os.path.basename(file))
        if m:
            ver_tuple = tuple(int(x) for x in m.groups())
            candidates.append((ver_tuple, file))

    if not candidates:
        print(
            f"找不到 {name} 的版本化執行檔：\n"
            f" - {os.path.join(folder, name + '_V*.exe')}\n"
            f" - {os.path.join(base_dir, name + '_V*.exe')}"
        )
        return

    candidates.sort(reverse=True)
    exe_path = candidates[0][1]
    subprocess.run(f'"{exe_path}"', shell=True)


def show_selector():
    root = tk.Tk()
    root.title("請選擇要執行的項目")
    # 最大化
    root.attributes("-fullscreen", True)
    selection = tk.StringVar(value="")

    base_dir = r"D:\S8521\Update_Repo"

    def do_select(value):
        selection.set(value)
        root.quit()
    def do_exit():
        selection.set("")
        root.quit()

    btn_style = {
        "font": ("Arial", 36),
        "bg": "#f0f0f0",
        "activebackground": "#e1e1e1",
        "relief": "raised",
        "bd": 3,
    }
    frame = tk.Frame(root, bg="#ffffff")
    frame.pack(fill="both", expand=True, padx=40, pady=40)

    # 動態偵測資料夾生成按鈕（完全依據實際存在的子資料夾）
    folders: List[str] = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))])

    for folder_name in folders:
        tk.Button(frame,
                  text=folder_name,
                  command=lambda v=folder_name: do_select(v),
                  **btn_style).pack(side="top", fill="both", expand=True, pady=15)

    # 新增離開按鈕
    exit_btn = tk.Button(frame, text="離開", command=do_exit,
                        font=("Arial", 32, "bold"),
                        bg="#e57373", activebackground="#ffcdd2",
                        relief="raised", bd=4, fg="#ffffff", height=1)
    exit_btn.pack(side="bottom", fill="x", padx=100, pady=30)

    root.mainloop()
    result = selection.get()
    root.destroy()
    return result if result else None

def main():
    if not is_admin():
        print("目前權限不足，正在嘗試以管理員權限重新執行...")
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)

    selection = show_selector()

    if not selection:
        return

    # 全改為動態：根據被點擊的子資料夾名稱，自動尋找對應的 {name}_V*.exe 並執行
    run_generic_tool(selection)

    return


if __name__ == '__main__':
    try:
        main()
        time.sleep(3)
        subprocess.run(['powershell', '-Command', 'Stop-Process -Name "winvnc" -Force'],  capture_output=True, text=True, check=True)
        time.sleep(3)
    except:
        pass
    subprocess.Popen(r"C:\Storage Card\Autorun.vbs", shell=True)
