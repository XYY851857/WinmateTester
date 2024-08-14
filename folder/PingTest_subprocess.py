import subprocess


if __name__ == "__main__":
    ping_result = subprocess.run(['powershell', '-Command', 'ping -S 192.168.2.101 192.168.2.1'], capture_output=True,text=True)
    ch_keyword = '%'
    ch_start_pos = ping_result.stdout.find(ch_keyword)
    if ch_start_pos != -1:
        ch_start_pos += len(ch_keyword)
        ping_result = ping_result.stdout[ch_start_pos-4:ch_start_pos]
        print(f"Ping Failed, Loss Rate:{ping_result.replace('(','')}")
        if ping_result == " (0%":
            print(f"success ping")
