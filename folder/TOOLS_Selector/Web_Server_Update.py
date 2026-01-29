import os
import shutil
import time
import sys
import json
import uuid
import datetime
import subprocess
import threading
import tkinter as tk
from tkinter import ttk

def get_mac_address():
    """
    Returns the MAC address of the machine.
    """
    mac = uuid.getnode()
    return ':'.join(('%012X' % mac)[i:i+2] for i in range(0, 12, 2))

def get_model():
    global model
    model = ''
    try:
        with open('C:/Storage Card/PARAME/Flag.txt', 'r', encoding='utf-16le') as f:
            lines = f.readlines()
            if len(lines) >= 2:
                second_line = lines[1].strip()
                if second_line.startswith('Limit '):
                    parts = second_line.split(',')
                    last_part = parts[-1].strip() if parts else ''
                    if last_part.isdigit():
                        model = last_part
                    else:
                        model = ''
                else:
                    model = ''
            else:
                model = ''
    except Exception:
        pass
    try:
        with open('C:/Storage Card/Parameter/machinedatas.txt', 'r', encoding='utf-8-sig') as f2:
            lines2 = f2.readlines()
            if len(lines2) >= 2:
                line1 = lines2[0].strip()
                line2 = lines2[1].strip()
                model = f"{line1} {line2}"
    except Exception:
        pass
    return model

def backup_parame(status_var):
    global model_name
    """
    Backups C:\Storage Card\PARAME or Parameter to a local PARAME_Backup directory named after the model.
    """
    status_var.set("正在備份 PARAME...")
    try:
        model_name = get_model()
        # Fallback if model name is empty or invalid
        if not model_name or not model_name.strip():
            model_folder_name = "Unknown_Model"
        else:
            # Sanitize filename just in case
            model_folder_name = "".join([c for c in model_name if c.isalnum() or c in (' ', '-', '_')]).strip()
            if not model_folder_name:
                model_folder_name = "Unknown_Model"
        
        # Source Detection
        src_dir = r'C:\Storage Card\PARAME'
        if not os.path.exists(src_dir):
            src_dir_alt = r'C:\Storage Card\Parameter'
            if os.path.exists(src_dir_alt):
                src_dir = src_dir_alt
            else:
                print(f"Backup skipped: neither PARAME nor Parameter exist.")
                return 

        # Destination
        backup_root = os.path.join(os.getcwd(), "PARAME_Backup")
        dst_dir = os.path.join(backup_root, model_folder_name)
        
        if not os.path.exists(backup_root):
            os.makedirs(backup_root)

        # If destination exists, remove it to ensure fresh backup
        if os.path.exists(dst_dir):
            shutil.rmtree(dst_dir)
            
        shutil.copytree(src_dir, dst_dir)
        print(f"Backed up {src_dir} to {dst_dir}")
        status_var.set(f"備份完成: {model_folder_name}")
        time.sleep(1)
        
    except Exception as e:
        msg = f"Backup failed: {e}"
        print(msg)
        status_var.set(msg)
        time.sleep(2) # Let user see error


def write_log(status_var=None):
    """
    Writes the update log to .\log\Web_Server_Update_log.txt in JSON format.
    Structure: {Model: {MAC: {"Installation Date": [dates]}}}
    """
    log_dir = r'.\log'
    log_file = os.path.join(log_dir, 'Web_Server_Update_log.txt')
    
    # Ensure log directory exists
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except OSError as e:
            msg = f"Error creating log directory {log_dir}: {e}"
            print(msg)
            if status_var: status_var.set(msg)
            return

    # Read existing log or start new
    log_data = {}
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if content:
                    log_data = json.loads(content)
        except Exception as e:
            print(f"Warning: Failed to read existing log: {e}")
            # Continue with empty data if read fails

    # Prepare new data
    model_name = get_model()
    if not model_name or not model_name.strip():
        model_name = "Unknown"
        
    current_mac = get_mac_address()
    current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Update structure: Model -> MAC -> Installation Date list
    if model_name not in log_data:
        log_data[model_name] = {}
    
    if current_mac not in log_data[model_name]:
        log_data[model_name][current_mac] = {"Installation Date": []}
    
    # Ensure it's a list (handle legacy format if needed, though we overwrite structure here)
    if not isinstance(log_data[model_name][current_mac], dict):
         # Reset if structure is completely wrong for this MAC
         log_data[model_name][current_mac] = {"Installation Date": []}
    
    if "Installation Date" not in log_data[model_name][current_mac]:
        log_data[model_name][current_mac]["Installation Date"] = []
        
    # Append new date
    log_data[model_name][current_mac]["Installation Date"].append(current_date)
    
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=4)
        print(f"Log written to {log_file}")
    except Exception as e:
        msg = f"Error writing log file: {e}"
        print(msg)
        if status_var: status_var.set(msg)

def update_process(root, progress_var, status_var, on_failure):
    # 0. Backup
    backup_parame(status_var)

    # 1. Stop the process
    status_var.set("正在準備更新...")
    try:
        subprocess.run(['powershell', '-Command', 'Stop-Process -Name "WebServerUDP" -Force'],  capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        pass # Process not running
    except Exception as e:
        print(f"Warning: Failed to stop WebServerUDP: {e}")

    # 1.5 Check for local Storage Card folder and copy if exists
    local_storage_src = os.path.abspath(r'.\Storage Card')
    target_storage_dst = r'C:\Storage Card'
    if os.path.exists(local_storage_src):
        status_var.set("偵測到 Storage Card, 執行替換...")
        print(f"Found local {local_storage_src}, copying to {target_storage_dst}...")
        try:
            # Walk and copy to allow overwrite and merging
            for root, dirs, files in os.walk(local_storage_src):
                # Construct relative path
                rel_path = os.path.relpath(root, local_storage_src)
                
                # Determine destination folder
                dest_root = target_storage_dst
                if rel_path != '.':
                    dest_root = os.path.join(target_storage_dst, rel_path)
                
                if not os.path.exists(dest_root):
                    os.makedirs(dest_root)
                
                for f in files:
                    src_file = os.path.join(root, f)
                    dst_file = os.path.join(dest_root, f)
                    status_var.set(f"複製: {f}")
                    shutil.copy2(src_file, dst_file)
                    
        except Exception as e:
            print(f"Error copying local Storage Card: {e}")
            status_var.set(f"Error copying Storage Card: {e}")
            time.sleep(2)

    # 2. Define files
    files_to_copy = [
        (r'.\WebServer\Newtonsoft.Json.Compact.dll', r'C:\Storage Card'),
        (r'.\WebServer\nModbusCE.dll',              r'C:\Storage Card'),
        (r'.\WebServer\WebserverCe.dll',            r'C:\Storage Card'),
        (r'.\WebServer\WebServerUDP.exe',           r'C:\Storage Card'),
        (r'.\WebServer\AutoRun.vbs',                r'C:\Storage Card')
    ]
    total_files = len(files_to_copy)
    
    # 3. Copy Loop
    success_count = 0
    time.sleep(1) # Short pause to render GUI before starting heavy IO
    
    for i, (src, dst_dir) in enumerate(files_to_copy):
        try:
            src_path = os.path.abspath(src)
            filename = os.path.basename(src_path)
            status_var.set(f"正在複製 {filename}...")
            
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir, exist_ok=True)
            
            dst_file = os.path.join(dst_dir, filename)
            shutil.copy2(src_path, dst_file)
            
            # Update progress
            success_count += 1
            progress_val = (i + 1) / total_files * 100
            progress_var.set(progress_val)
            
            # Simulate slight delay for visibility if needed, or just let it fly
            time.sleep(0.5)
            
        except Exception as e:
            status_var.set(f"Error: {e}")
            time.sleep(2) # Show error

    # 4. Finalize
    if success_count == total_files:
        status_var.set("Writing log...")
        write_log(status_var)
        status_var.set("更新完成 重啟中...")
        # Close GUI after command issue (though shutdown kills it)
        root.quit()
    else:
        status_var.set("更新失敗. 請點擊確定繼續...")
        # Invoke UI change on main thread
        root.after(0, on_failure)

def main():
    root = tk.Tk()
    
    # Remove title bar (no close button)
    root.overrideredirect(True)
    
    # Always on top
    root.attributes('-topmost', True)
    
    # Set window size and position (centered)
    window_width = 400
    window_height = 100
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_cordinate = int((screen_width/2) - (window_width/2))
    y_cordinate = int((screen_height/2) - (window_height/2))
    root.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))
    
    # Styles
    style = ttk.Style()
    style.theme_use('default')
    style.configure("TProgressbar", thickness=30)
    
    # UI Elements
    frame = tk.Frame(root, padx=20, pady=20, bg='#f0f0f0') # Simple bg color
    frame.pack(fill=tk.BOTH, expand=True)
    root.configure(bg='#f0f0f0')
    
    status_var = tk.StringVar(value="Initializing...")
    label = tk.Label(frame, textvariable=status_var, bg='#f0f0f0', font=('Arial', 16))
    label.pack(pady=(0, 10))
    
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(frame, variable=progress_var, maximum=100, style="TProgressbar")
    progress_bar.pack(fill=tk.X)
    
    # UI Elements (Callback needs access to frame, so defining logic here)
    def on_failure():
        def on_confirm():
            os.system("shutdown /r /t 0")
            root.quit()
            
        btn = tk.Button(frame, text="確定 (Confirm)", command=on_confirm, font=('Arial', 16), bg='red', fg='white')
        btn.pack(pady=5)

    # Start thread
    t = threading.Thread(target=update_process, args=(root, progress_var, status_var, on_failure))
    t.daemon = True # Ensure thread dies with app
    t.start()
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
