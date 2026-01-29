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

def write_log(status_var=None):
    """
    Writes the update log to .\log\Web_Server_Update_log.txt in JSON format.
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

    # Data to log
    log_data = {
        "MAC Address": get_mac_address(),
        "Installation Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=4)
        print(f"Log written to {log_file}")
    except Exception as e:
        msg = f"Error writing log file: {e}"
        print(msg)
        if status_var: status_var.set(msg)

def update_process(root, progress_var, status_var, on_failure):
    # 1. Stop the process
    status_var.set("正在準備更新...")
    try:
        subprocess.run(['powershell', '-Command', 'Stop-Process -Name "WebServerUDP" -Force'],  capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        pass # Process not running
    except Exception as e:
        print(f"Warning: Failed to stop WebServerUDP: {e}")

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
