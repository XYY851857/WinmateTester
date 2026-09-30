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

import base64

# 使用者中止旗標：開始執行後可由「終止安裝」按鈕設置
abort_event = threading.Event()

# 是否複製 Connecter 套件：True=複製 / False=略過
COPY_CONNECTER = True

# 是否套用防火牆規則：True=建立/清理規則，False=完全略過
APPLY_FIREWALL_RULES = True


# 是否複製 WebServer 附加檔案：True=複製 / False=略過
COPY_WEBSERVER = True

# 警示文字是否啟用紅藍閃爍效果
warning_blink_enabled = True


import uuid

def get_mac_address_by_name():
    try:
        # 取得 MAC 位址的 48-bit 整數並格式化為 AA-BB-CC-DD-EE-FF
        mac_num = uuid.getnode()
        mac_hex = f'{mac_num:012x}'.upper()
        return '-'.join(mac_hex[i:i+2] for i in range(0, 12, 2))
    except Exception:
        return "Unknown"


def _flush_log(msg):
    try:
        os.makedirs('.\\log', exist_ok=True)
        with open('.\\log\\SetupUtility_FLUSH_log.txt', 'a', encoding='utf-8') as lf:
            lf.write(f'{datetime.now().strftime("%Y%m%d:%H%M%S")}: {get_mac_address_by_name()} {msg}\n')
    except Exception:
        pass


def _flush_volume_path(volume_path):
    """將磁碟區（\\\\.\\C: 或 \\\\?\\Volume{GUID}）的快取（檔案內容 + 檔案系統中繼資料）強制寫入磁碟；需系統管理員權限"""
    GENERIC_READ = 0x80000000
    GENERIC_WRITE = 0x40000000
    FILE_SHARE_READ = 0x1
    FILE_SHARE_WRITE = 0x2
    OPEN_EXISTING = 3
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    k32.CreateFileW.restype = ctypes.c_void_p
    k32.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
                                ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
    k32.FlushFileBuffers.restype = ctypes.c_int
    k32.FlushFileBuffers.argtypes = [ctypes.c_void_p]
    k32.CloseHandle.argtypes = [ctypes.c_void_p]
    h = k32.CreateFileW(volume_path, GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE,
                        None, OPEN_EXISTING, 0, None)
    if h is None or h == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        if not k32.FlushFileBuffers(h):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        k32.CloseHandle(h)


def flush_volume(drive='C:'):
    _flush_volume_path(f'\\\\.\\{drive}')


def flush_all_volumes():
    """強制寫入系統上所有磁碟區（含無磁碟代號的 EFI 系統分割區）；回傳是否全部成功（無法開啟的磁碟區僅記錄略過）"""
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    k32.FindFirstVolumeW.restype = ctypes.c_void_p
    k32.FindFirstVolumeW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32]
    k32.FindNextVolumeW.restype = ctypes.c_int
    k32.FindNextVolumeW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint32]
    k32.FindVolumeClose.argtypes = [ctypes.c_void_p]
    buf = ctypes.create_unicode_buffer(260)
    h = k32.FindFirstVolumeW(buf, len(buf))
    if h is None or h == ctypes.c_void_p(-1).value:
        _flush_log(f'FAIL: FindFirstVolumeW: {ctypes.WinError(ctypes.get_last_error())}')
        return False
    ok = True
    try:
        while True:
            # FindFirstVolumeW 回傳 \\?\Volume{GUID}\，開啟磁碟區 handle 時需去掉結尾反斜線
            vol = buf.value.rstrip('\\')
            try:
                _flush_volume_path(vol)
                _flush_log(f'OK: volume {vol} flushed')
            except OSError as e:
                # 1=不支援、19=防寫、21=裝置未就緒（空的讀卡機/光碟機）：不影響判定；5=拒絕存取（非管理員）視為失敗
                if getattr(e, 'winerror', None) in (1, 19, 21):
                    _flush_log(f'SKIP: volume {vol}: {e}')
                else:
                    ok = False
                    _flush_log(f'FAIL: volume {vol}: {e}')
            if not k32.FindNextVolumeW(h, buf, len(buf)):
                break
    finally:
        k32.FindVolumeClose(h)
    return ok


def flush_registry(subkey=r'SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy'):
    """強制將登錄檔 hive（預設 SYSTEM，防火牆規則所在）寫入磁碟"""
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey, 0, winreg.KEY_READ) as k:
            winreg.FlushKey(k)
        _flush_log(f'OK: registry HKLM\\{subkey} flushed')
        return True
    except Exception as e:
        _flush_log(f'FAIL: registry HKLM\\{subkey} flush: {e}')
        return False


def _fsync_paths(paths):
    """備援：逐檔 fsync（無法開啟磁碟區時使用）；回傳失敗數"""
    failures = 0
    files = []
    for p in paths:
        if os.path.isfile(p):
            files.append(p)
        elif os.path.isdir(p):
            for dirpath, _, filenames in os.walk(p):
                files.extend(os.path.join(dirpath, f) for f in filenames)
    for f in files:
        try:
            with open(f, 'r+b') as fh:
                os.fsync(fh.fileno())
        except Exception as e:
            failures += 1
            _flush_log(f'FSYNC_FAIL: {f}: {e}')
    return failures


def flush_to_disk(paths, drive='C:'):
    """確保資料已實際寫入磁碟，避免過早斷電造成檔案不完整；回傳是否成功"""
    try:
        flush_volume(drive)
        _flush_log(f'OK: volume {drive} flushed')
        return True
    except Exception as e:
        _flush_log(f'WARN: volume {drive} flush failed ({e}), fallback to per-file fsync')
    if not paths:
        # 刪除類操作（僅中繼資料）無逐檔備援可用
        _flush_log('FAIL: no per-file fallback available')
        return False
    failures = _fsync_paths(paths)
    _flush_log(f'{"OK" if failures == 0 else "FAIL"}: per-file fsync done, failures={failures}')
    return failures == 0


def flush_to_disk_with_ui(paths, drive='C:'):
    """寫入磁碟期間顯示「請勿斷電」並切換不定量進度條；可於主線程或背景執行緒呼叫"""
    def _begin():
        try:
            start_button.config(text="寫入磁碟中，請勿斷電...")
            progress_bar.config(mode='indeterminate')
            progress_bar.start(20)
        except Exception:
            pass

    def _end():
        try:
            progress_bar.stop()
            progress_bar.config(mode='determinate')
            progress_var.set(100)
            start_button.config(text="開始執行")
        except Exception:
            pass

    on_main = threading.current_thread() is threading.main_thread()
    if on_main:
        _begin()
        try:
            root.update_idletasks()
        except Exception:
            pass
    else:
        root.after(0, _begin)
    ok = flush_to_disk(paths, drive)
    if on_main:
        _end()
    else:
        root.after(0, _end)
    if not ok:
        messagebox.showwarning("警告", "資料寫入磁碟未完全確認，請勿直接斷電，請使用「重新啟動」")
    return ok


def ensure_admin():
    """未以系統管理員身分執行時，自動以 runas 重新啟動自己（保留原工作目錄）；回傳 True 表示本程序應繼續執行"""
    import sys
    # 提權後的子程序：還原工作目錄（程式大量使用相對路徑 .\\0\\...、.\\log）
    for arg in sys.argv[1:]:
        if arg.startswith('--cwd='):
            try:
                os.chdir(arg[len('--cwd='):])
            except Exception:
                pass
    if _is_admin():
        return True
    if '--elevated' in sys.argv:
        # 已嘗試過提權仍非管理員，避免無限重啟
        _flush_log('WARN: still not admin after elevation, continue without admin')
        return True
    cwd = os.getcwd()
    if getattr(sys, 'frozen', False):
        args = sys.argv[1:]
    else:
        args = [os.path.abspath(sys.argv[0])] + sys.argv[1:]
    args = [a for a in args if not a.startswith('--cwd=')] + ['--elevated', f'--cwd={cwd}']
    try:
        ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable,
                                                  subprocess.list2cmdline(args), cwd, 1)
    except Exception as e:
        ret = 0
        _flush_log(f'WARN: elevation error: {e}')
    if ret > 32:
        return False
    # 使用者拒絕 UAC 或提權失敗：以一般權限繼續，寫入磁碟時會改用逐檔 fsync
    _flush_log(f'WARN: elevation declined/failed (code={ret}), continue without admin')
    return True


def read_paths_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        paths = [line.strip() for line in f if line.strip()]

    folder_names = [os.path.basename(path) for path in paths]
    return folder_names, paths


def clear_directory(directory, keep_parame=False):
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            if keep_parame:
                if filename in ("PARAME", "Parameter"):
                    continue
                if directory.lower().endswith("storage card2") and filename.lower() in ("graphic", "program"):
                    continue
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except PermissionError:
                try:
                    root.after(0, lambda fp=file_path: messagebox.showinfo("錯誤", f"{fp}無法存取或刪除"))
                except Exception:
                    pass
            except Exception as e:
                try:
                    root.after(0, lambda fp=file_path: messagebox.showinfo("錯誤", f"刪除{fp}發生錯誤"))
                except Exception:
                    pass


def copy_tree_with_progress(src_folder, dst_folder):
    total_files = sum([len(files) for r, d, files in os.walk(src_folder)])
    # 新增：共通附加檔案清單（不論選擇哪個項目都會一起複製）
    extra_copies = [
        (r'.\\0\\SetupUtility\\data\\WebServer\\Newtonsoft.Json.Compact.dll', r'C:\\Storage Card'),
        (r'.\\0\\SetupUtility\\data\\WebServer\\nModbusCE.dll',              r'C:\\Storage Card'),
        (r'.\\0\\SetupUtility\\data\\WebServer\\WebserverCe.dll',            r'C:\\Storage Card'),
        (r'.\\0\\SetupUtility\\data\\WebServer\\WebServerUDP.exe',           r'C:\\Storage Card'),
        (r'.\\0\\SetupUtility\\data\\WebServer\\HackTimer.js',               r'C:\\Windows\\www\\wwwpub'),
        (r'.\\0\\SetupUtility\\data\\WebServer\\terchy.html',                r'C:\\Windows\\www\\wwwpub'),
    ]
    if 'install_ipps_var' in globals() and install_ipps_var.get():
        extra_copies.extend([
            (r'.\\0\\SetupUtility\\data\\IPPS\\IP_Provisioning_System_Client.exe', r'C:\\IPPS'),
            (r'.\\0\\SetupUtility\\data\\IPPS\\client_config.json', r'C:\\IPPS'),
        ])
    # 僅當啟用時才把附加檔案計入總數
    if COPY_WEBSERVER:
        extra_existing = [src for src, _ in extra_copies if os.path.isfile(src)]
        total_files += len(extra_existing)
    else:
        extra_existing = []

    copied_files = 0
    # --- 併行：在主包 copy 的同時進行防火牆規則寫入 ---
    fw_thread = None
    try:
        os.makedirs('.\\log', exist_ok=True)
        fw_log_path = '.\\log\\SetupUtility_FW_log.txt'
    except Exception:
        fw_log_path = None
    program_path = None
    try:
        S_index = selected_option.index('S')
        s_name = selected_option[S_index:]
        program_path = os.path.join('C:\\Storage Card', f'{s_name}.exe')
    except Exception:
        pass
    if APPLY_FIREWALL_RULES:
        progs = []
        if program_path:
            progs.append(program_path)
            if not os.path.isfile(program_path) and fw_log_path:
                with open(fw_log_path, 'a', encoding='utf-8') as fwl:
                    mac_address = get_mac_address_by_name()
                    fwl.write(f'{datetime.now().strftime("%Y%m%d:%H%M%S")}: {mac_address} WARN: program not found for selection "{selected_option}" -> expected "{program_path}", rule still attempted\n')
        else:
            if fw_log_path:
                with open(fw_log_path, 'a', encoding='utf-8') as fwl:
                    mac_address = get_mac_address_by_name()
                    fwl.write(f'{datetime.now().strftime("%Y%m%d:%H%M%S")}: {mac_address} WARN: cannot derive program name from selection "{selected_option}"\n')
        webserver_udp_path = r'C:\Storage Card\WebServerUDP.exe'
        progs.append(webserver_udp_path)
        if not os.path.isfile(webserver_udp_path) and fw_log_path:
            with open(fw_log_path, 'a', encoding='utf-8') as fwl:
                mac_address = get_mac_address_by_name()
                fwl.write(f'{datetime.now().strftime("%Y%m%d:%H%M%S")}: {mac_address} WARN: WebServerUDP.exe not found at "{webserver_udp_path}", rule still attempted\n')
        
        winvnc_path = r'C:\Program Files (x86)\apps\winvnc.exe'
        progs.append(winvnc_path)
        if not os.path.isfile(winvnc_path) and fw_log_path:
            with open(fw_log_path, 'a', encoding='utf-8') as fwl:
                mac_address = get_mac_address_by_name()
                fwl.write(f'{datetime.now().strftime("%Y%m%d:%H%M%S")}: {mac_address} WARN: winvnc.exe not found at "{winvnc_path}", rule still attempted\n')
                
        # 背景執行，與主包 copy 併行
        fw_thread = threading.Thread(target=lambda: ensure_program_fw_rules_batch(progs), daemon=True)
        fw_thread.start()
    else:
        # 略過所有防火牆操作（不清舊規則、不新增），僅記錄 SKIP（包含 WebServerUDP）
        if fw_log_path:
            with open(fw_log_path, 'a', encoding='utf-8') as fwl:
                mac_address = get_mac_address_by_name()
                ts = datetime.now().strftime("%Y%m%d:%H%M%S")
                fwl.write(f'{ts}: {mac_address} SKIP: APPLY_FIREWALL_RULES=False for selection "{selected_option}"\n')
                fwl.write(f'{ts}: {mac_address} SKIP: WebServerUDP.exe not applied due to APPLY_FIREWALL_RULES=False\n')

    def copy_file(src_file, dst_file, verify=False):
        nonlocal copied_files
        # 逐塊拷貝；可選擇是否進行 I/O 級驗證（檔案大小一致）
        with open(src_file, 'rb') as src, open(dst_file, 'wb') as dst:
            while True:
                if abort_event.is_set():
                    raise Exception('USER_ABORT')
                buffer = src.read(1024 * 1024)
                if not buffer:
                    break
                dst.write(buffer)
            dst.flush()
            if verify:
                os.fsync(dst.fileno())
        # 僅在 verify=True 時檢查大小一致
        if verify and (os.path.getsize(src_file) != os.path.getsize(dst_file)):
            raise IOError(f'Copy incomplete (size mismatch): {src_file} -> {dst_file}')
        copied_files += 1
        pct = (copied_files / max(1, total_files)) * 100.0
        val = min(pct, 100.0)
        try:
            root.after(0, lambda v=val: progress_var.set(v))
        except Exception:
            pass

    try:
        for dirpath, dirnames, filenames in os.walk(src_folder):
            if 'keep_parame_var' in globals() and keep_parame_var.get():
                if os.path.relpath(dirpath, src_folder) == '.':
                    if "PARAME" in dirnames:
                        dirnames.remove("PARAME")
                    if "Parameter" in dirnames:
                        dirnames.remove("Parameter")
                    filenames = [f for f in filenames if f not in ("PARAME", "Parameter")]

            dst_dirpath = os.path.join(dst_folder, os.path.relpath(dirpath, src_folder))
            os.makedirs(dst_dirpath, exist_ok=True)
            if abort_event.is_set():
                raise Exception('USER_ABORT')
            for filename in filenames:
                src_file = os.path.join(dirpath, filename)
                dst_file = os.path.join(dst_dirpath, filename)
                copy_file(src_file, dst_file, verify=False)  # 主體：關閉逐檔 I/O 驗證
        if COPY_CONNECTER:
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
        else:
            # 跳過 Connecter 複製（保留既有內容），記錄略過事件
            try:
                os.makedirs('.\\log', exist_ok=True)
                with open('.\\log\\Connecter_install_log.txt', 'a', encoding='utf-8') as file:
                    mac_address = get_mac_address_by_name()
                    file.write(f"{datetime.now().strftime('%Y%m%d:%H%M%S')}: {mac_address} SKIP: COPY_CONNECTER=False\n")
            except Exception:
                pass

        def select_behavior(command, behavior_type):
            # 若使用者在「準備關機」階段按下終止，直接跳過關機
            if abort_event.is_set():
                return
            try:
                _run_hidden(['powershell', '-NoProfile', '-NonInteractive', '-WindowStyle', 'Hidden',
                             '-Command', f'shutdown /{command}'], capture_output=True, text=True, check=True)
            except:
                messagebox.showinfo("錯誤", f"{behavior_type}執行錯誤，請從系統左下角手動點擊關機")
                unlock_button()

        # 主體資料夾拷貝完成後，先做完整性驗證（僅比對 src→dst 的存在與大小）
        try:
            os.makedirs('.\\log', exist_ok=True)
            verify_log_path = '.\\log\\SetupUtility_COPY_verify_log.txt'
        except Exception:
            verify_log_path = None

        verify_errors = []
        for dirpath, dirnames, filenames in os.walk(src_folder):
            if 'keep_parame_var' in globals() and keep_parame_var.get():
                if os.path.relpath(dirpath, src_folder) == '.':
                    if "PARAME" in dirnames:
                        dirnames.remove("PARAME")
                    if "Parameter" in dirnames:
                        dirnames.remove("Parameter")
                    filenames = [f for f in filenames if f not in ("PARAME", "Parameter")]

            rel_dir = os.path.relpath(dirpath, src_folder)
            dst_dir = os.path.join(dst_folder, rel_dir)
            for filename in filenames:
                s = os.path.join(dirpath, filename)
                d = os.path.join(dst_dir, filename)
                if not os.path.isfile(d):
                    verify_errors.append(f'MISSING: {os.path.relpath(s, src_folder)}')
                else:
                    try:
                        if os.path.getsize(s) != os.path.getsize(d):
                            verify_errors.append(
                                f'SIZE_MISMATCH: {os.path.relpath(s, src_folder)} ({os.path.getsize(s)} != {os.path.getsize(d)})'
                            )
                    except Exception as e:
                        verify_errors.append(f'CHECK_ERROR: {os.path.relpath(s, src_folder)}: {e}')

        if verify_errors:
            if verify_log_path:
                with open(verify_log_path, 'a', encoding='utf-8') as vf:
                    mac = get_mac_address_by_name()
                    ts = datetime.now().strftime("%Y%m%d:%H%M%S")
                    for line in verify_errors:
                        vf.write(f'{ts}: {mac} {line}\n')
            update_button_color("red")
            messagebox.showwarning("完整性驗證失敗", "主體資料夾複製完整性驗證未通過，已中止後續動作。\n" + "\n".join(verify_errors[:20]))
            unlock_button()
            return

        # 嚴格模式：任何一個檔案失敗就警示並中止後續關機/重啟
        extra_failures = []

        if COPY_WEBSERVER:
            # 新增：複製共通附加檔案到指定目的地；一律嘗試拷貝，失敗寫入 log 不中斷流程
            try:
                os.makedirs('.\\log', exist_ok=True)
                extra_log_path = '.\\log\\SetupUtility_EXTRA_copy_log.txt'
            except Exception:
                extra_log_path = None

            for src_path, dst_dir in extra_copies:
                if abort_event.is_set():
                    raise Exception('USER_ABORT')
                try:
                    os.path.isdir(dst_dir) or os.makedirs(dst_dir, exist_ok=True)
                    dst_file = os.path.join(dst_dir, os.path.basename(src_path))
                    # 嘗試拷貝；若來源不存在或 I/O 錯誤，copy_file 會丟出例外
                    copy_file(src_path, dst_file, verify=True)  # WebServer：逐檔 I/O 級驗證
                except Exception as e:
                    if extra_log_path:
                        with open(extra_log_path, 'a', encoding='utf-8') as lf:
                            mac_address = get_mac_address_by_name()
                            lf.write(f'{datetime.now().strftime("%Y%m%d:%H%M%S")}: {mac_address} Failed to copy {src_path} -> {dst_dir}: {e}\n')
                    extra_failures.append(f'ERROR: {src_path} -> {dst_dir}: {e}')

            # 若有任何附加檔案缺失或複製錯誤，發出警示並中止後續流程（不進行重啟）
            if extra_failures:
                update_button_color("red")
                msg = "偵測到以下附加檔案未成功複製：\n" + "\n".join(extra_failures)
                messagebox.showwarning("附加檔案複製失敗", msg)
                unlock_button()
                return
        else:
            # 略過 WebServer 附加檔案複製，記錄 SKIP
            try:
                os.makedirs('.\\log', exist_ok=True)
                with open('.\\log\\SetupUtility_EXTRA_copy_log.txt', 'a', encoding='utf-8') as lf:
                    mac_address = get_mac_address_by_name()
                    lf.write(f'{datetime.now().strftime("%Y%m%d:%H%M%S")}: {mac_address} SKIP: COPY_WEBSERVER=False\n')
            except Exception:
                pass

        # 等待防火牆背景任務（若仍在執行），避免重開機時規則未套完
        try:
            if fw_thread and fw_thread.is_alive():
                fw_thread.join(timeout=60)
            if fw_thread and fw_thread.is_alive() and fw_log_path:
                with open(fw_log_path, 'a', encoding='utf-8') as fwl:
                    fwl.write(f'{datetime.now().strftime("%Y%m%d:%H%M%S")}: {get_mac_address_by_name()} WARN: firewall task still running after 60s\n')
        except Exception:
            pass
        # 強制將所有複製結果寫入磁碟後才回報完成，避免過早斷電造成檔案不完整
        flush_paths = [dst_folder, 'C:\\Storage Card2']
        if COPY_CONNECTER:
            flush_paths.append('C:\\Connecter')
        if COPY_WEBSERVER:
            flush_paths.extend(os.path.join(d, os.path.basename(s)) for s, d in extra_copies)
        flush_to_disk_with_ui(flush_paths)
        update_button_color("green")
        if abort_event.is_set():
            # 使用者在準備關機階段按下中止
            unlock_button()
            messagebox.showinfo("已終止", "已停止關機動作")
            return
        # 啟動 10 秒重新啟動倒數計時
        try:
            root.after(0, enable_restart_countdown)
        except Exception:
            pass
        S_index = selected_option.index('S')
        messagebox.showinfo("完成", f"{selected_option[S_index:]}已複製到 C:\\Storage Card")
        # 標記清單項目為成功（綠底）
        try:
            root.after(0, mark_option_success)
        except Exception:
            pass
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
        if 'USER_ABORT' in str(e):
            update_button_color("red")
            # 取消任何已排程的關機（若有）
            try:
                _run_hidden(['powershell', '-NoProfile', '-NonInteractive', '-WindowStyle', 'Hidden',
                             '-Command', 'shutdown /a'], capture_output=True, text=True)
            except Exception:
                pass
            messagebox.showinfo("已終止", "安裝已被使用者終止")
            unlock_button()
        else:
            update_button_color("red")
            messagebox.showerror("錯誤", f"複製資料夾時發生錯誤: {e}")
            unlock_button()


def unlock_button():
    start_button.config(state=tk.NORMAL)
    end_button.config(state=tk.NORMAL)
    try:
        stop_button.config(state=tk.DISABLED)
    except Exception:
        pass
    return


def abort_install():
    # 設置中止旗標
    abort_event.set()
    # 嘗試終止任何已排程的關機（若關機已經被觸發）
    try:
        _run_hidden(['powershell', '-NoProfile', '-NonInteractive', '-WindowStyle', 'Hidden',
                     '-Command', 'shutdown /a'], capture_output=True, text=True)
    except Exception:
        pass
    # 使用者要求：中止時立即複製 AutoRun.vbs 到 C:\Storage Card1\
    src_vbs = '.\\0\\SetupUtility\\data\\AutoRun.vbs'
    dst_dir = 'C:\\Storage Card'
    dst_path = os.path.join(dst_dir, 'AutoRun.vbs')
    try:
        os.makedirs('.\\log', exist_ok=True)
        abort_log = '.\\log\\SetupUtility_ABORT_log.txt'
    except Exception:
        abort_log = None
    try:
        os.makedirs(dst_dir, exist_ok=True)
        shutil.copy2(src_vbs, dst_path)
        if abort_log:
            with open(abort_log, 'a', encoding='utf-8') as lf:
                mac_address = get_mac_address_by_name()
                lf.write(f'{datetime.now().strftime("%Y%m%d:%H%M%S")}: {mac_address} Copied AutoRun.vbs -> {dst_path}\n')
        flush_to_disk([dst_path])
    except Exception as e:
        if abort_log:
            with open(abort_log, 'a', encoding='utf-8') as lf:
                mac_address = get_mac_address_by_name()
                lf.write(f'{datetime.now().strftime("%Y%m%d:%H%M%S")}: {mac_address} ERROR copying AutoRun.vbs: {e}\n')
    try:
        stop_button.config(state=tk.DISABLED)
    except Exception:
        pass


def lock_button():
    start_button.config(state=tk.DISABLED)
    start_button.config(bg='yellow')
    end_button.config(state=tk.DISABLED)
    return


def update_button_color(color):
    start_button.config(bg=color, fg='white')
    unlock_button()


def install_connecter_process():
    global warning_blink_enabled
    src = r'.\0\SetupUtility\data\Connecter'
    dst = r'C:\Connecter'

    lock_button()
    abort_event.clear()
    try:
        stop_button.config(state=tk.NORMAL)
    except:
        pass

    try:
        if os.path.exists(dst):
            shutil.rmtree(dst)

        total_files = sum([len(files) for r, d, files in os.walk(src)])
        copied_files = 0

        os.makedirs(dst, exist_ok=True)

        for dirpath, dirnames, filenames in os.walk(src):
            rel_dir = os.path.relpath(dirpath, src)
            dst_dir = os.path.join(dst, rel_dir)
            os.makedirs(dst_dir, exist_ok=True)

            for filename in filenames:
                if abort_event.is_set():
                    raise Exception('USER_ABORT')

                src_file = os.path.join(dirpath, filename)
                dst_file = os.path.join(dst_dir, filename)
                shutil.copy2(src_file, dst_file)

                copied_files += 1
                pct = (copied_files / max(1, total_files)) * 100.0
                try:
                    root.after(0, lambda v=pct: progress_var.set(v))
                except:
                    pass

        flush_to_disk_with_ui([dst])
        update_button_color("green")
        try:
            root.after(0, mark_option_success)
        except Exception:
            pass

        # 安裝完成後先更新選項（會依 C:\\Connecter 是否存在決定是否顯示「解除安裝Connecter」）
        try:
            root.after(0, update_connecter_options)
        except Exception:
            pass

        # Prompt
        # askokcancel returns True for OK, False for Cancel
        ans = messagebox.askokcancel("完成", "安裝完成是否啟動Connecter_Launcher")
        if ans:  # OK -> Execute and wait for Connecter_Launcher to close, then恢復紅藍閃爍
            exe_path = r'C:\Connecter\Connecter_Launcher.exe'
            if os.path.exists(exe_path):
                # 啟動 Connecter_Launcher 前先暫停紅藍閃爍，以降低資源佔用
                warning_blink_enabled = False
                # Connecter_Launcher 開啟期間，停用「開始執行」與「結束程序」按鈕
                try:
                    start_button.config(state=tk.DISABLED)
                    end_button.config(state=tk.DISABLED)
                except Exception:
                    pass
                proc = subprocess.Popen(exe_path, cwd=os.path.dirname(exe_path))

                def _wait_launcher_and_close():
                    global warning_blink_enabled
                    try:
                        if proc.poll() is None:
                            # 還沒關，1 秒後再檢查
                            root.after(1000, _wait_launcher_and_close)
                        else:
                            # Connecter_Launcher 已經關閉，恢復紅藍閃爍並重新啟用按鈕
                            warning_blink_enabled = True
                            try:
                                warning_font_color()
                            except Exception:
                                pass
                            try:
                                unlock_button()
                            except Exception:
                                pass
                    except Exception:
                        # 若檢查過程中有任何問題，仍嘗試恢復紅藍閃爍與按鈕狀態
                        warning_blink_enabled = True
                        try:
                            warning_font_color()
                        except Exception:
                            pass
                        try:
                            unlock_button()
                        except Exception:
                            pass

                # 1 秒後開始輪詢 Connecter_Launcher 狀態
                try:
                    root.after(1000, _wait_launcher_and_close)
                except Exception:
                    # 如果 GUI 已經被關掉，就直接嘗試恢復紅藍閃爍
                    warning_blink_enabled = True
                    try:
                        warning_font_color()
                    except Exception:
                        pass
            else:
                messagebox.showerror("錯誤", f"找不到 {exe_path}")
                unlock_button()
        else:  # Cancel -> Unlock
            unlock_button()

    except Exception as e:
        if 'USER_ABORT' in str(e):
            messagebox.showinfo("已終止", "安裝已被使用者終止")
        else:
            messagebox.showerror("錯誤", f"安裝失敗: {e}")
        unlock_button()
        try:
            root.after(0, update_connecter_options)
        except Exception:
            pass


# 新增：Connecter 解除安裝流程
def uninstall_connecter_process():
    dst = r'C:\Connecter'

    lock_button()
    abort_event.clear()
    try:
        stop_button.config(state=tk.NORMAL)
    except Exception:
        pass

    try:
        # 啟動不定量進度條
        root.after(0, lambda: progress_bar.config(mode='indeterminate'))
        root.after(0, lambda: progress_bar.start(20))

        if os.path.exists(dst):
            shutil.rmtree(dst)
            flush_to_disk([])
            root.after(0, lambda: progress_bar.stop())
            root.after(0, lambda: progress_bar.config(mode='determinate'))
            root.after(0, lambda: progress_var.set(100))
            update_button_color("green")
            root.after(0, mark_option_success)
            messagebox.showinfo("完成", "Connecter 已解除安裝")
        else:
            root.after(0, lambda: progress_bar.stop())
            root.after(0, lambda: progress_bar.config(mode='determinate'))
            root.after(0, lambda: progress_var.set(0))
            update_button_color("red")
            messagebox.showinfo("提示", "找不到 C:\\Connecter，可能已經解除安裝")
        try:
            root.after(0, update_connecter_options)
        except Exception:
            pass
    except Exception as e:
        root.after(0, lambda: progress_bar.stop())
        root.after(0, lambda: progress_bar.config(mode='determinate'))
        root.after(0, lambda: progress_var.set(0))
        update_button_color("red")
        messagebox.showerror("錯誤", f"解除安裝失敗: {e}")
    finally:
        unlock_button()


# 新增：根據實際路徑狀態更新 Listbox 選項
def update_connecter_options():
    """
    根據實際路徑狀態更新 Listbox 選項：
    - 有來源資料夾 .\\0\\SetupUtility\\data\\Connecter 時顯示「安裝Connecter」
    - 有 C:\\Connecter 目錄時顯示「解除安裝Connecter」
    """
    try:
        items = listbox.get(0, tk.END)
    except Exception:
        return

    # 先移除舊的 Connecter 相關選項
    base_items = [it for it in items if it not in ("安裝Connecter", "解除安裝Connecter")]

    connecter_src = r'.\0\SetupUtility\data\\Connecter'
    has_connecter = os.path.exists(connecter_src)
    connecter_installed = os.path.exists(r'C:\Connecter')

    if has_connecter:
        base_items.append("安裝Connecter")
    if connecter_installed:
        base_items.append("解除安裝Connecter")

    listbox.delete(0, tk.END)
    for it in base_items:
        listbox.insert(tk.END, it)


def _has_existing_files():
    """檢查 C:/Storage Card/ 是否有 AutoRun.vbs 以外的檔案，或 C:/Storage Card2/ 是否有任何檔案"""
    card1 = 'C:\\Storage Card'
    card2 = 'C:\\Storage Card2'
    if os.path.isdir(card1):
        for name in os.listdir(card1):
            full = os.path.join(card1, name)
            if os.path.isfile(full) and name.lower() != 'autorun.vbs':
                return True
            if os.path.isdir(full):
                return True
    if os.path.isdir(card2):
        if os.listdir(card2):
            return True
    return False


def mark_option_success():
    """將選單中剛剛成功執行的項目底色改為綠色"""
    global selected_index
    try:
        if selected_index is not None:
            listbox.itemconfig(selected_index, {'bg': 'lightgreen', 'fg': 'black'})
    except Exception:
        pass


def start_copy(paths_dict):
    lock_button()
    abort_event.clear()
    try:
        stop_button.config(state=tk.NORMAL)
    except Exception:
        pass
    try:
        global selected_option, selected_index
        selected_index = listbox.curselection()[0]
        selected_option = listbox.get(selected_index)
        dst_base_folder = 'C:\\'
    except (tk.TclError, IndexError):
        messagebox.showwarning("錯誤", "請選擇一個選項")
        unlock_button()
        return

    # 二次確認：一律彈出確認
    if not messagebox.askokcancel("確認", f"確定要執行「{selected_option}」嗎？"):
        unlock_button()
        return

    # 強制刷新 UI，確保對話框完全關閉後才繼續
    root.update()

    # 停止現有倒數（若有），等操作完成後再重新開始
    stop_restart_countdown()

    # 紀錄執行動作：以 MAC 為 Key，記錄時間與項目（使用背景執行緒避免卡住主線程 UI）
    def _log_action():
        try:
            os.makedirs('.\\log', exist_ok=True)
            mac_address = get_mac_address_by_name()
            with open('.\\log\\SetupUtility_action_log.txt', 'a', encoding='utf-8') as log_f:
                log_f.write(f'{datetime.now().strftime("%Y%m%d:%H%M%S")}: {mac_address} 執行: {selected_option}\n')
        except Exception:
            pass
    threading.Thread(target=_log_action, daemon=True).start()

    if selected_option == "清除Card1, Card2":
        storage_card_folder = os.path.join(dst_base_folder, "Storage Card")
        storage_card2_folder = os.path.join(dst_base_folder, "Storage Card2")
        keep = keep_parame_var.get() if 'keep_parame_var' in globals() else False
        clear_directory(storage_card_folder, keep_parame=keep)
        clear_directory(storage_card2_folder, keep_parame=keep)
        os.makedirs(storage_card_folder, exist_ok=True)
        os.makedirs(storage_card2_folder, exist_ok=True)
        # 新增清除 C:\Connecter
        connecter_dst_folder = 'C:\\Connecter'
        if os.path.exists(connecter_dst_folder):
            try:
                shutil.rmtree(connecter_dst_folder)
            except Exception as e:
                messagebox.showinfo("錯誤", f"C:\\Connecter 刪除失敗：{e}")
        # 新增清除 C:\IPPS
        ipps_dst_folder = 'C:\\IPPS'
        if os.path.exists(ipps_dst_folder):
            try:
                shutil.rmtree(ipps_dst_folder)
            except Exception as e:
                messagebox.showinfo("錯誤", f"C:\\IPPS 刪除失敗：{e}")
        # 刪除結果（NTFS 中繼資料）寫入磁碟後才回報完成
        flush_to_disk_with_ui([storage_card_folder, storage_card2_folder])
        enable_restart_countdown()
        messagebox.showinfo("完成", f"Card, Card2 已清除")
        update_button_color("green")
        root.after(0, mark_option_success)
        try:
            update_connecter_options()
        except Exception:
            pass
    elif selected_option == "安裝Connecter":
        threading.Thread(target=install_connecter_process).start()
    elif selected_option == "解除安裝Connecter":
        threading.Thread(target=uninstall_connecter_process).start()
    elif selected_option in ("更改開機畫面 NO LOGO", "更改開機畫面 default"):
        subfolder = 'NOLOGO' if 'NO LOGO' in selected_option else 'default'

        def _run_logo_change():
            combined = f'''
                            cd 0;
                            cd SetupUtility;
                            cd a;
                            cd {subfolder};
                            .\\setup.exe batch install enable-entry
                        '''
            try:
                root.after(0, lambda: progress_bar.config(mode='indeterminate'))
                root.after(0, lambda: progress_bar.start(20))

                subprocess.run(['powershell', '-Command', combined], capture_output=True, text=True, check=True)
                # 開機畫面寫在 EFI 系統分割區（FAT32、無磁碟代號），需 flush 所有磁碟區
                if not flush_all_volumes():
                    messagebox.showwarning("警告", "開機畫面寫入磁碟未完全確認，請勿直接斷電，請使用「重新啟動」")

                root.after(0, lambda: progress_bar.stop())
                root.after(0, lambda: progress_bar.config(mode='determinate'))
                root.after(0, lambda: progress_var.set(100))
                root.after(0, enable_restart_countdown)
                messagebox.showinfo("完成", "開機底圖更換成功")
                update_button_color("green")
                root.after(0, mark_option_success)
            except subprocess.CalledProcessError as e:
                root.after(0, lambda: progress_bar.stop())
                root.after(0, lambda: progress_bar.config(mode='determinate'))
                root.after(0, lambda: progress_var.set(0))
                messagebox.showinfo("錯誤", f"開機底圖設定失敗，請重試")
                update_button_color("red")

        threading.Thread(target=_run_logo_change, daemon=True).start()
    else:
        src_folder = paths_dict.get(selected_option)
        if src_folder:
            storage_card_folder = os.path.join(dst_base_folder, "Storage Card")
            storage_card2_folder = os.path.join(dst_base_folder, "Storage Card2")

            # 在主線程上啟動不定量進度條，確保立即顯示
            progress_bar.config(mode='indeterminate')
            progress_bar.start(20)
            root.update()  # 強制刷新，確保進度條動畫立即顯示

            def _clear_and_copy():
                keep = keep_parame_var.get() if 'keep_parame_var' in globals() else False
                clear_directory(storage_card_folder, keep_parame=keep)
                clear_directory(storage_card2_folder, keep_parame=keep)
                os.makedirs(storage_card_folder, exist_ok=True)
                os.makedirs(storage_card2_folder, exist_ok=True)
                # 清除完成，切回定量進度條並開始複製
                root.after(0, lambda: progress_bar.stop())
                root.after(0, lambda: progress_bar.config(mode='determinate'))
                root.after(0, lambda: progress_var.set(0))
                copy_tree_with_progress(src_folder, storage_card_folder)

            threading.Thread(target=_clear_and_copy).start()


def close_app():
    root.destroy()


# --- 重新啟動倒數計時 ---
_restart_after_id = None
_countdown_label = None


def _do_restart():
    """執行重新啟動"""
    global _restart_after_id
    _restart_after_id = None
    try:
        subprocess.Popen(['powershell', '-NoProfile', '-NonInteractive', '-WindowStyle', 'Hidden',
                          '-Command', 'shutdown /r /t 0'], creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except Exception:
        messagebox.showinfo("錯誤", "重新啟動執行錯誤，請從系統左下角手動點擊關機")
    root.destroy()


def enable_restart_countdown(seconds=20):
    """將「結束程序」按鈕變更為「重新啟動」並開始倒數"""
    global _restart_after_id, _countdown_label

    # 取消之前的倒數（若有）
    if _restart_after_id is not None:
        try:
            root.after_cancel(_restart_after_id)
        except Exception:
            pass
        _restart_after_id = None

    end_button.config(text="重新啟動", command=_do_restart)

    # 建立或更新倒數提示 Label（小字）
    if _countdown_label is None:
        _countdown_label = tk.Label(root, text="", font=("Arial", 10))
        _countdown_label.pack(after=end_button.master, pady=0)

    remaining = [seconds]

    def _tick():
        global _restart_after_id
        if remaining[0] <= 0:
            _do_restart()
            return
        try:
            _countdown_label.config(text=f"{remaining[0]}秒無動作將自動重新啟動")
        except Exception:
            pass
        remaining[0] -= 1
        _restart_after_id = root.after(1000, _tick)

    _tick()


def stop_restart_countdown():
    """停止倒數計時並將按鈕恢復為「結束程序」"""
    global _restart_after_id, _countdown_label
    if _restart_after_id is not None:
        try:
            root.after_cancel(_restart_after_id)
        except Exception:
            pass
        _restart_after_id = None
    try:
        end_button.config(text="結束程序", command=close_app)
    except Exception:
        pass
    if _countdown_label is not None:
        try:
            _countdown_label.config(text="")
        except Exception:
            pass



def addition_command():
    if os.path.exists('.\\0\\SetupUtility\\addition_command.txt'):
        try:
            with open('.\\0\\SetupUtility\\addition_command.txt', 'r', encoding='UTF-8') as file:
                for line in file:
                    command = line.strip()  # 移除空白與換行符
                    if command:  # 如果不是空行，執行指令
                        result = subprocess.run(['powershell', '-Command', command], capture_output=True, text=True,
                                                check=True)
                        print('插件執行成功')
        except subprocess.CalledProcessError as e:
            messagebox.showinfo("錯誤", f"插件執行失敗，請重試")
            return False, '插件執行'
    return True, 'None'


def warning_font_color():
    def _tick():
        global warning_blink_enabled
        if not warning_blink_enabled:
            return
        try:
            current = warning_label.cget('fg')
            warning_label.config(fg='red' if current != 'red' else 'blue')
        except Exception:
            pass
        finally:
            if warning_blink_enabled:
                root.after(1000, _tick)
    root.after(0, _tick)




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


# --- 併行批次建立防火牆規則用 helper ---
def _run_hidden(args, **kwargs):
    """Run subprocess without flashing a console window."""
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0  # SW_HIDE
    kwargs.setdefault('startupinfo', si)
    kwargs.setdefault('creationflags', getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return subprocess.run(args, **kwargs)

def _ps_encoded_command(script: str):
    """Return a PowerShell -EncodedCommand argv for reliable multiline execution."""
    encoded = base64.b64encode(script.encode('utf-16le')).decode('ascii')
    return ['powershell', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-EncodedCommand', encoded]

def ensure_program_fw_rules_batch(program_paths):
    """
    一次性（單一 PowerShell 行程）為多個程式建立入/出站放行規則。
    將同名規則先移除再新增，以確保內容一致。
    """
    try:
        os.makedirs('.\\log', exist_ok=True)
        log_path = '.\\log\\SetupUtility_FW_log.txt'
    except Exception:
        log_path = None

    mac_address = get_mac_address_by_name()
    ts = datetime.now().strftime("%Y%m%d:%H%M%S")

    if not _is_admin():
        if log_path:
            with open(log_path, 'a', encoding='utf-8') as f:
                for p in program_paths:
                    f.write(f'{ts}: {mac_address} SKIP: not running as Administrator, program rule not applied for {p}\n')
        return

    # 去重並維持順序
    seen = set()
    paths = []
    for p in program_paths:
        if p and p not in seen:
            seen.add(p)
            paths.append(p)

    if not paths:
        return

    # 建立 PowerShell 批次腳本：移除舊規則、建立新規則（in/out）
    lines = [
        '$ErrorActionPreference = "Stop";',
        'function Apply-ProgramRule([string]$Program) {',
        '  $base = [System.IO.Path]::GetFileName($Program);',
        '  foreach ($dir in @("Inbound","Outbound")) {',
        '    $suffix = if ($dir -eq "Inbound") { "in" } else { "out" };',
        '    $name = ("SetupUtility_Allow_{0}_{1}" -f $base, $suffix);',
        '    try { Remove-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue } catch {}',
        '    New-NetFirewallRule -DisplayName $name -Direction $dir -Action Allow -Program $Program -Enabled True -Profile Any | Out-Null',
        '  }',
        '}'
    ]
    for p in paths:
        # 單引號內再以單引號跳脫
        pp = p.replace("'", "''")
        lines.append(f"Apply-ProgramRule('{pp}');")

    script = '\n'.join(lines)
    argv = _ps_encoded_command(script)
    res = _run_hidden(argv, capture_output=True, text=True)
    # 規則寫入登錄檔後強制 flush，避免過早斷電造成規則遺失
    flush_registry()

    # 統一寫入結果（以整批為單位），並維持舊版每條規則的紀錄格式
    ok = (res.returncode == 0)
    for p in paths:
        for direction in ('in', 'out'):
            name = f"SetupUtility_Allow_{os.path.basename(p)}_{direction}"
            status = 'Success' if ok else 'Failed'
            if log_path:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(f'{ts}: {mac_address} Program FW {name}: {status}\n')
    # 追加 stdout/stderr 以利除錯
    if log_path and (res.stdout or res.stderr):
        with open(log_path, 'a', encoding='utf-8') as f:
            if (res.stdout or '').strip():
                f.write(f'    stdout: {res.stdout.strip()}\n')
            if (res.stderr or '').strip():
                f.write(f'    stderr: {res.stderr.strip()}\n')



def _add_fw_rule_program(program_path: str, direction: str = "in", profiles: str = "any"):
    """
    新增針對「程式」的防火牆規則（direction: in/out）。
    回傳 (ok:boolean, rule_name:str, stdout:str, stderr:str)。
    """
    rule_name = f'SetupUtility_Allow_{os.path.basename(program_path)}_{direction}'
    # 先刪除同名規則，確保規則內容一致
    subprocess.run(
        f'netsh advfirewall firewall delete rule name="{rule_name}"',
        capture_output=True, text=True, shell=True
    )
    cmd = (
        f'netsh advfirewall firewall add rule name="{rule_name}" '
        f'dir={direction} action=allow program="{program_path}" enable=yes profile={profiles}'
    )
    res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return (res.returncode == 0), rule_name, (res.stdout or ''), (res.stderr or '')


def ensure_program_fw_rules(program_path: str):
    """
    依指定程式建立入/出站放行；一律先刪除舊規則再寫入。
    不處理任何以埠為單位的規則（例如 502/5001）。
    """
    try:
        os.makedirs('.\\log', exist_ok=True)
        log_path = '.\\log\\SetupUtility_FW_log.txt'
    except Exception:
        log_path = None

    mac_address = get_mac_address_by_name()
    ts = datetime.now().strftime("%Y%m%d:%H%M%S")

    if not _is_admin():
        if log_path:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f'{ts}: {mac_address} SKIP: not running as Administrator, program rule not applied for {program_path}\n')
        return

    for direction in ('in', 'out'):
        name = f"SetupUtility_Allow_{os.path.basename(program_path)}_{direction}"
        ok, _, out, err = _add_fw_rule_program(program_path, direction, 'any')
        status = 'Success' if ok else 'Failed'
        if log_path:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f'{ts}: {mac_address} Program FW {name}: {status}\n')
                if out.strip():
                    f.write(f'    stdout: {out.strip()}\n')
                if err.strip():
                    f.write(f'    stderr: {err.strip()}\n')




def create_gui():
    global root, progress_var, progress_bar, combo, start_button, end_button, entry, listbox, launch_photo_button
    global warning_label, stop_button
    result, detail = addition_command()
    if result is False:
        return False, detail
    global install_ipps_var, keep_parame_var
    root = tk.Tk()
    root.title("SetupUtility")
    root.attributes('-fullscreen', True)
    font = ('Arial', 20)

    install_ipps_var = tk.BooleanVar(value=True)
    keep_parame_var = tk.BooleanVar(value=False)

    top_frame = tk.Frame(root)
    top_frame.pack(fill='x', side='top', pady=10, padx=20)
    
    small_font = ('Arial', 14)
    keep_parame_cb = tk.Checkbutton(top_frame, text="保留PARAME\nGRP、PRG", variable=keep_parame_var, font=small_font)
    # 最初不顯示
    
    label = tk.Label(top_frame, text="請選擇執行項目:", font=font)
    label.pack(side='left', expand=True)
    
    install_ipps_cb = tk.Checkbutton(top_frame, text="安裝IPPS", variable=install_ipps_var, font=font)

    folder_names, paths = read_paths_from_file(".\\0\\SetupUtility\\data\\path.txt")

    # Check for Connecter folder
    connecter_src = r'.\0\SetupUtility\data\\Connecter'
    has_connecter = os.path.exists(connecter_src)
    connecter_installed = os.path.exists(r'C:\Connecter')

    formatted_names = [f'清除Card1, Card2,  安裝{name}' for name in folder_names]
    paths_dict = dict(zip(formatted_names, paths))  # Map normal items

    formatted_names.append("清除Card1, Card2")
    if has_connecter:
        formatted_names.append("安裝Connecter")
    if connecter_installed:
        formatted_names.append("解除安裝Connecter")
    if os.path.exists('.\\0\\SetupUtility\\a\\NOLOGO'):
        formatted_names.append("更改開機畫面 NO LOGO")
    if os.path.exists('.\\0\\SetupUtility\\a\\default'):
        formatted_names.append("更改開機畫面 default")

    # label is now in top_frame

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
        try:
            selection = listbox.get(listbox.curselection())
        except tk.TclError:
            return
        entry.insert(0, selection)
        
        keep_parame_cb.pack_forget()
        label.pack_forget()
        install_ipps_cb.pack_forget()
        
        if selection in paths_dict:
            keep_parame_cb.pack(side='left')
            label.pack(side='left', expand=True)
            install_ipps_cb.pack(side='right')
        else:
            label.pack(side='left', expand=True)

    listbox.bind('<ButtonRelease-1>', on_select)

    button_frame = tk.Frame(root)
    button_frame.pack(pady=10, fill='x')

    start_button = tk.Button(button_frame, text="開始執行", command=lambda: start_copy(paths_dict), font=font)
    start_button.pack(side='right', padx=5, expand=True, fill='x')

    end_button = tk.Button(button_frame, text="結束程序", command=close_app, font=font)
    end_button.pack(side='left', padx=5, expand=True, fill='x')

    # 停止安裝按鈕（起初禁用；按下開始後才啟用）
    stop_frame = tk.Frame(root)
    stop_frame.pack(pady=5, padx=20, fill='x')
    stop_button = tk.Button(stop_frame, text="終止安裝", command=abort_install, font=font, state=tk.DISABLED)
    stop_button.pack(side='right', padx=5, expand=True, fill='x')


    progress_frame = tk.Frame(root)
    progress_frame.pack(pady=5, padx=20, fill='x')

    progress_var = tk.DoubleVar()
    progress_bar = Progressbar(progress_frame, variable=progress_var, maximum=100)
    progress_bar.pack(side='left', fill='x', expand=True)

    warning_frame = tk.Frame(root)
    warning_frame.pack(pady=5, padx=20, fill='x')

    warning_label = tk.Label(warning_frame, text='執行完成會自動重新啓動\n請勿直接斷電', font=font)
    warning_label.pack()
    warning_font_color()

    root.mainloop()


if __name__ == "__main__":
    # 未以系統管理員執行時自動提權（磁碟區 flush、防火牆規則皆需要管理員權限）
    if not ensure_admin():
        raise SystemExit(0)
    try:
        subprocess.run(['powershell', '-Command', 'Stop-Process -Name "WebServerUDP" -Force'], capture_output=True, text=True, check=True)
        subprocess.run(['powershell', '-Command', 'Stop-Process -Name "IP_Provisioning_System_Client" -Force'], capture_output=True, text=True, check=False)
    except:
        pass
    res = create_gui()
    if isinstance(res, tuple) and res and res[0] is False:
        try:
            os.makedirs('.\\log', exist_ok=True)
            with open('.\\log\\SetupUtility_ERROR_report.txt', 'a', encoding='utf-8') as errfile:
                errfile.write(f'SetupUtility: {res[1]} Failed\n')
        except:
            pass
