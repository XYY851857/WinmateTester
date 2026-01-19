import os
import shutil
import time
import ctypes
import sys
import json
import uuid
import datetime

def disable_close_button():
    """
    Disables the Close button (X) of the Console Window on Windows.
    This prevents the user from accidentally closing the update process.
    """
    try:
        # Get handle to kernel32 and user32
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        
        # Get the handle to the current console window
        hwnd = kernel32.GetConsoleWindow()
        
        if hwnd:
            # Get the system menu for the window
            # The second argument False returns the handle to the copy of the window menu
            hmenu = user32.GetSystemMenu(hwnd, False)
            
            if hmenu:
                # SC_CLOSE is the command ID for the Close menu item (0xF060)
                # MF_BYCOMMAND indicates that we are specifying the ID (0x00000000)
                user32.DeleteMenu(hmenu, 0xF060, 0x00000000)
    except Exception as e:
        # If not on Windows or other error, just ignore
        pass

def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='█', print_end="\r"):
    """
    Call in a loop to create terminal progress bar
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=print_end)
    # Print New Line on Complete
    if iteration == total: 
        print()

def get_mac_address():
    """
    Returns the MAC address of the machine.
    """
    mac = uuid.getnode()
    return ':'.join(('%012X' % mac)[i:i+2] for i in range(0, 12, 2))

def write_log():
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
            print(f"\nError creating log directory {log_dir}: {e}")
            return

    # Data to log
    log_data = {
        "MAC Address": get_mac_address(),
        "Installation Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=4)
        print(f"\nLog written to {log_file}")
    except Exception as e:
        print(f"\nError writing log file: {e}")

def main():
    # Attempt to disable the close button upon start
    disable_close_button()
    
    # List of files to copy: (Source Path, Destination Directory)
    # Source paths are relative to the script execution directory
    files_to_copy = [
        (r'.\WebServer\Newtonsoft.Json.Compact.dll', r'C:\Storage Card'),
        (r'.\WebServer\nModbusCE.dll',              r'C:\Storage Card'),
        (r'.\WebServer\WebserverCe.dll',            r'C:\Storage Card'),
        (r'.\WebServer\WebServerUDP.exe',           r'C:\Storage Card')
    ]

    total_files = len(files_to_copy)
    
    print("Starting Update Process...")
    print_progress_bar(0, total_files, prefix='Progress:', suffix='Complete', length=50)

    for i, (src, dst_dir) in enumerate(files_to_copy):
        try:
            # Resolve absolute path for source (assuming running from script directory)
            src_path = os.path.abspath(src)
            
            # Ensure destination directory exists
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir, exist_ok=True)
            
            # Destination file path
            dst_file = os.path.join(dst_dir, os.path.basename(src_path))
            
            # Copy file (this will overwrite if exists)
            shutil.copy2(src_path, dst_file)
            
            # Optional: Simulate a small delay if files are small, to let user see progress
            time.sleep(0.5)
            
        except Exception as e:
            # Log error but continue or exit? Usually defined by requirements.
            # Here we print error to console.
            print(f"\nError copying {src} to {dst_dir}: {e}")
        
        # Update progress bar
        print_progress_bar(i + 1, total_files, prefix='Progress:', suffix='Complete', length=50)

    # Write log before reboot
    write_log()

    print("\nUpdate Complete. System will reboot...")
    
    # Execute Reboot command
    # /r = reboot, /t 0 = time 0 seconds
    os.system("shutdown /r /t 0")

if __name__ == "__main__":
    main()
