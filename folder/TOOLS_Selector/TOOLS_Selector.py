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
    # """根據子資料夾名稱 name，優先在
    # D:\S8521\Update_Repo\{name}\{name}_V*.exe 找最新版本；
    # 若找不到，再到 D:\S8521\Update_Repo\{name}_V*.exe 搜尋。
    # """
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
    # 使用 exe 所在的資料夾作為工作目錄
    subprocess.run(f'"{exe_path}"', shell=True, cwd=os.path.dirname(exe_path))


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

    # 建立主框架
    main_frame = tk.Frame(root, bg="#ffffff")
    main_frame.pack(fill="both", expand=True)

    # 建立 Canvas 與 Scrollbar 的容器
    canvas_container = tk.Frame(main_frame, bg="#ffffff")
    canvas_container.pack(side="top", fill="both", expand=True, padx=40, pady=(40, 10))

    canvas = tk.Canvas(canvas_container, bg="#ffffff", highlightthickness=0)
    scrollbar = tk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)
    
    scrollable_frame = tk.Frame(canvas, bg="#ffffff")

    # 當 scrollable_frame 大小改變時，更新 scrollregion
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    # 在 Canvas 中建立視窗來放置 scrollable_frame
    window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    # 當 Canvas 大小改變時，調整 scrollable_frame 的寬度以符合 Canvas
    def on_canvas_configure(event):
        canvas.itemconfig(window_id, width=event.width)
    
    canvas.bind("<Configure>", on_canvas_configure)
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # 綁定滑鼠滾輪
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # 動態偵測資料夾生成按鈕（完全依據實際存在的子資料夾）
    folders: List[str] = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))])

    for folder_name in folders:
        tk.Button(scrollable_frame,
                  text=folder_name,
                  command=lambda v=folder_name: do_select(v),
                  **btn_style).pack(side="top", fill="x", pady=15)

    # 離開按鈕固定在底部
    bottom_frame = tk.Frame(main_frame, bg="#ffffff")
    bottom_frame.pack(side="bottom", fill="x", padx=100, pady=30)

    exit_btn = tk.Button(bottom_frame, text="離開", command=do_exit,
                        font=("Arial", 32, "bold"),
                        bg="#e57373", activebackground="#ffcdd2",
                        relief="raised", bd=4, fg="#ffffff", height=1)
    exit_btn.pack(fill="x")

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
        subprocess.run(['powershell', '-Command', 'Stop-Process -Name "WebServerUDP" -Force'],  capture_output=True, text=True, check=True)
    except Exception as e:
        print(e)
        pass
    time.sleep(3)
    subprocess.Popen(r"C:\Storage Card\Autorun.vbs", shell=True)
