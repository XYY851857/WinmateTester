import os
import shutil
import subprocess
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox
from tkinter.ttk import Progressbar
import threading
import psutil
import ctypes


def get_mac_address_by_name():
    for interface, addrs in psutil.net_if_addrs().items():
        if interface == "乙太網路 2":
            for addr in addrs:
                if addr.family == psutil.AF_LINK:  # AF_LINK 表示 MAC 地址
                    return addr.address
    return "Unknown"


def read_paths_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        paths = [line.strip() for line in f if line.strip()]

    folder_names = [os.path.basename(path) for path in paths]
    return folder_names, paths


def clear_directory(directory):
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except PermissionError:
                messagebox.showinfo("錯誤", f"{file_path}無法存取或刪除'")
                unlock_button()
            except Exception as e:
                messagebox.showinfo("錯誤", f"刪除{file_path}發生錯誤")
                unlock_button()


def copy_tree_with_progress(src_folder, dst_folder):
    total_files = sum([len(files) for r, d, files in os.walk(src_folder)])
    copied_files = 0

    def copy_file(src_file, dst_file):
        nonlocal copied_files
        with open(src_file, 'rb') as src, open(dst_file, 'wb') as dst:
            buffer = src.read(1024 * 1024)
            while buffer:
                dst.write(buffer)
                buffer = src.read(1024 * 1024)
        copied_files += 1
        progress_var.set(copied_files / total_files * 110)
        root.update_idletasks()

    try:
        for dirpath, dirnames, filenames in os.walk(src_folder):
            dst_dirpath = os.path.join(dst_folder, os.path.relpath(dirpath, src_folder))
            os.makedirs(dst_dirpath, exist_ok=True)
            for filename in filenames:
                src_file = os.path.join(dirpath, filename)
                dst_file = os.path.join(dst_dirpath, filename)
                copy_file(src_file, dst_file)
        connecter_src_folder = '.\\0\\SetupUtility\\Connecter'
        connecter_dst_folder = 'C:\\Connecter'
        # 複製前先刪除舊目的地
        if os.path.exists(connecter_dst_folder):
            shutil.rmtree(connecter_dst_folder)
        if os.path.exists(connecter_src_folder):
            try:
                shutil.copytree(connecter_src_folder, connecter_dst_folder)
            except Exception as e:
                with open(".\\log\\Connecter_install_log.txt", 'a') as file:
                    mac_address = get_mac_address_by_name()
                    file.write(f'{datetime.now().strftime("%Y%m%d:%H%M%S")}: {mac_address} Failed: {e}\n')
                messagebox.showinfo("錯誤", f"Connecter套件安裝錯誤，請再試一次")
                unlock_button()
                return
            else:
                with open(".\\log\\Connecter_install_log.txt", 'a') as file:
                    mac_address = get_mac_address_by_name()
                    file.write(f'{datetime.now().strftime("%Y%m%d:%H%M%S")}: {mac_address} Success.\n')

        def select_behavior(command, behavior_type):
            try:
                subprocess.run(['powershell', '-Command', f'shutdown /{command}'], capture_output=True, text=True,
                               check=True)
            except:
                messagebox.showinfo("錯誤", f"{behavior_type}執行錯誤，請從系統左下角手動點擊關機")
                unlock_button()

        update_button_color("green")
        S_index = selected_option.index('S')
        select_behavior('r', '關機')
        messagebox.showinfo("完成", f"{selected_option[S_index:]}已複製到 C:\\Storage Card")
        # option = selected_var.get()
        # if option == 0:
        #     pass
        # elif option == 1:  # 關機
        #     select_behavior('s', '關機')
        # elif option == 2:  # 登出
        #     select_behavior('l', '登出')
        # elif option == 3:  # 重新啓動
        #     select_behavior('r', '重新啓動')
        unlock_button()
    except Exception as e:
        update_button_color("red")
        messagebox.showerror("錯誤", f"複製資料夾時發生錯誤: {e}")
        unlock_button()


def unlock_button():
    start_button.config(state=tk.NORMAL)
    end_button.config(state=tk.NORMAL)
    return


def lock_button():
    start_button.config(state=tk.DISABLED)
    start_button.config(bg='yellow')
    end_button.config(state=tk.DISABLED)
    return


def update_button_color(color):
    start_button.config(bg=color, fg='white')
    unlock_button()


def start_copy(paths_dict):
    lock_button()
    try:
        global selected_option
        selected_option = listbox.get(listbox.curselection())
        dst_base_folder = 'C:\\'
    except tk.TclError:
        messagebox.showwarning("錯誤", "請選擇一個選項")
        unlock_button()
        return

    if selected_option == "清除Card1, Card2":
        storage_card_folder = os.path.join(dst_base_folder, "Storage Card")
        storage_card2_folder = os.path.join(dst_base_folder, "Storage Card2")
        clear_directory(storage_card_folder)
        clear_directory(storage_card2_folder)
        os.makedirs(storage_card_folder, exist_ok=True)
        os.makedirs(storage_card2_folder, exist_ok=True)
        messagebox.showinfo("完成", f"Card, Card2 已清除")
        update_button_color("green")
        # 新增清除 C:\Connecter
        connecter_dst_folder = 'C:\\Connecter'
        if os.path.exists(connecter_dst_folder):
            try:
                shutil.rmtree(connecter_dst_folder)
            except Exception as e:
                messagebox.showinfo("錯誤", f"C:\\Connecter 刪除失敗：{e}")
    else:
        src_folder = paths_dict.get(selected_option)
        if src_folder:
            storage_card_folder = os.path.join(dst_base_folder, "Storage Card")
            storage_card2_folder = os.path.join(dst_base_folder, "Storage Card2")
            clear_directory(storage_card_folder)
            clear_directory(storage_card2_folder)
            os.makedirs(storage_card_folder, exist_ok=True)
            os.makedirs(storage_card2_folder, exist_ok=True)

            threading.Thread(target=copy_tree_with_progress, args=(src_folder, storage_card_folder)).start()


def close_app():
    root.destroy()


def addition_command():
    if os.path.exists('.\\0\\SetupUtility\\a'):
        combined = f'''
                        cd 0;
                        cd SetupUtility;
                        cd a; 
                        .\\setup.exe batch install enable-entry
                    '''
        try:
            subprocess.run(['powershell', '-Command', combined], capture_output=True, text=True, check=True)
            print('開機底圖更換成功')
        except subprocess.CalledProcessError as e:
            messagebox.showinfo("錯誤", f"開機底圖設定失敗，請重試")
            return False, '開機底圖設定'
    if os.path.exists('.\\0\\SetupUtility\\addition_command.txt'):
        try:
            with open('.\\0\\SetupUtility\\addition_command.txt', 'r', encoding='UTF-8') as file:
                for line in file:
                    command = line.strip()  # 移除空白與換行符
                    if command:  # 如果不是空行，執行指令
                        result = subprocess.run(['powershell', '-Command', command], capture_output=True, text=True,
                                                check=True, shell=True)
                        print('插件執行成功')
        except subprocess.CalledProcessError as e:
            messagebox.showinfo("錯誤", f"插件執行失敗，請重試")
            return False, '插件執行'
    return True, 'None'


def warning_font_color():
    while True:
        warning_label.config(fg='blue')
        time.sleep(1)
        warning_label.config(fg='red')
        time.sleep(1)


def _add_fw_rule_port(port, proto="TCP", profiles="any"):
    name = f"SetupUtility_Allow_{proto}_{port}"
    # 先刪除可能存在的同名規則（忽略失敗）
    del_res = subprocess.run(
        f'netsh advfirewall firewall delete rule name={name}',
        capture_output=True, text=True, shell=True
    )
    # 新增規則（針對指定埠、指定協定，套用於所有網路設定檔 profile=any）
    cmd = (
        f'netsh advfirewall firewall add rule name={name} '
        f'dir=in action=allow protocol={proto} localport={port} '
        f'profile={profiles}'
    )
    add_res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    # 回傳是否成功與輸出，讓上層決定如何紀錄/顯示
    return (add_res.returncode == 0), (add_res.stdout or ''), (add_res.stderr or '')


def _is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _has_fw_rule(name: str) -> bool:
    """Return True if a firewall rule with the given DisplayName exists (locale-independent)."""
    try:
        ps_cmd = (
            f'$r = Get-NetFirewallRule -DisplayName "{name}" -ErrorAction SilentlyContinue; '
            f'if ($r) {{ exit 0 }} else {{ exit 1 }}'
        )
        res = subprocess.run(['powershell', '-NoProfile', '-Command', ps_cmd], capture_output=True, text=True)
        return res.returncode == 0
    except Exception:
        return False


def setup_firewall_rules():
    try:
        os.makedirs('.\\log', exist_ok=True)
        log_path = '.\\log\\SetupUtility_FW_log.txt'
        mac_address = get_mac_address_by_name()
        ts = datetime.now().strftime("%Y%m%d:%H%M%S")

        if not _is_admin():
            with open(log_path, 'a', encoding='utf-8') as file:
                file.write(f'{ts}: {mac_address} SKIP: not running as Administrator, firewall rules not applied.\n')
            return

        results = []
        for port in (502, 5001):
            for proto in ("TCP", "UDP"):
                ok, out, err = _add_fw_rule_port(port, proto, "any")
                name = f"SetupUtility_Allow_{proto}_{port}"
                verified = _has_fw_rule(name) if ok else False
                status = 'Success' if (ok and verified) else 'Failed'
                results.append((name, status, out, err))

        with open(log_path, 'a', encoding='utf-8') as file:
            file.write(f'{ts}: {mac_address} Applying FW rules for TCP/UDP ports 502, 5001 (profiles=any)\n')
            for name, status, out, err in results:
                file.write(f'  {name}: {status}\n')
                if status != 'Success':
                    if out.strip():
                        file.write(f'    stdout: {out.strip()}\n')
                    if err.strip():
                        file.write(f'    stderr: {err.strip()}\n')
    except Exception as e:
        try:
            os.makedirs('.\\log', exist_ok=True)
            with open('.\\log\\SetupUtility_ERROR_report.txt', 'a', encoding='utf-8') as errfile:
                errfile.write(f'Firewall setup failed: {e}\n')
        except Exception:
            pass


def create_gui():
    global root, progress_var, combo, start_button, end_button, entry, listbox, launch_photo_button
    global warning_label
    result, detail = addition_command()
    if result is False:
        return False, detail
    # 防火牆規則在背景執行緒設定，主執行緒繼續渲染 GUI
    threading.Thread(target=setup_firewall_rules, daemon=True).start()
    root = tk.Tk()
    root.title("SetupUtility")
    root.attributes('-fullscreen', True)
    font = ('Arial', 20)

    folder_names, paths = read_paths_from_file(".\\0\\SetupUtility\\data\\path.txt")
    formatted_names = [f'清除Card1, Card2,  安裝{name}' for name in folder_names]
    formatted_names.append("清除Card1, Card2")
    paths_dict = dict(zip(formatted_names[:-1], paths))
    label = tk.Label(root, text="請選擇執行項目:", font=font)
    label.pack(pady=10)

    entry = tk.Entry(root, font=font, width=0)
    entry.forget()

    listbox_frame = tk.Frame(root)
    listbox_frame.pack(pady=5, fill='x')
    listbox = tk.Listbox(listbox_frame, font=font, height=0)
    for item in formatted_names:
        listbox.insert(tk.END, item)
    listbox.pack(side='left', fill='x', expand=True)

    def on_select(event):
        entry.delete(0, tk.END)
        selection = listbox.get(listbox.curselection())
        entry.insert(0, selection)

    listbox.bind('<ButtonRelease-1>', on_select)

    button_frame = tk.Frame(root)
    button_frame.pack(pady=10, fill='x')

    start_button = tk.Button(button_frame, text="開始執行", command=lambda: start_copy(paths_dict), font=font)
    start_button.pack(side='right', padx=5, expand=True, fill='x')

    end_button = tk.Button(button_frame, text="結束程序", command=close_app, font=font)
    end_button.pack(side='left', padx=5, expand=True, fill='x')

    progress_frame = tk.Frame(root)
    progress_frame.pack(pady=5, padx=20, fill='x')

    progress_var = tk.DoubleVar()
    progress_bar = Progressbar(progress_frame, variable=progress_var, maximum=100)
    progress_bar.pack(side='left', fill='x', expand=True)

    warning_frame = tk.Frame(root)
    warning_frame.pack(pady=5, padx=20, fill='x')

    warning_label = tk.Label(warning_frame, text='執行完成會自動重新啓動\n請勿直接斷電', font=font)
    warning_label.pack()
    threading.Thread(target=warning_font_color).start()

    # checkbox_frame = tk.Frame(root)
    # checkbox_frame.pack(pady=20, padx=20, fill='x')
    # checkbox_frame.columnconfigure((0, 1, 2), weight=1)

    # selected_var = tk.IntVar(value=1)
    # radio1_shutdown = tk.Radiobutton(checkbox_frame, text='關機', font=font, variable=selected_var, value=1)
    # radio1_shutdown.grid(row=0, column=0, sticky='ew', padx=10)
    #
    # radio2_logout = tk.Radiobutton(checkbox_frame, text='登出', font=font, variable=selected_var, value=2)
    # radio2_logout.grid(row=0, column=1, sticky='ew', padx=10)
    #
    # radio3_restart = tk.Radiobutton(checkbox_frame, text='重新啓動', font=font, variable=selected_var, value=3)
    # radio3_restart.grid(row=0, column=2, sticky='ew', padx=10)

    root.mainloop()


if __name__ == "__main__":
    report, detail = create_gui()
    if report is False:
        with open('\\log\\SetupUtility_ERROR_report.txt', 'a') as errfile:
            errfile.write(f'SetupUtility: {detail} Failed\n')
