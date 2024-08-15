import subprocess
import threading


def ping101(ip_start, ip_target):
    ping_result = subprocess.run(['powershell', '-Command', f'ping -S {ip_start} {ip_target}'], capture_output=True,
                                 text=True)  # ping -S 起點 終點
    ch_keyword = '%'
    ch_start_pos = ping_result.stdout.find(ch_keyword)
    if ch_start_pos != -1:
        ch_start_pos += len(ch_keyword)
        ping_result = ping_result.stdout[ch_start_pos - 4:ch_start_pos]
        print(f"Ping Failed, Loss Rate:{ping_result.replace('(', '')}")
        if ping_result == " (0%":  # 遺失率0%
            print(f'IP:{ip_start}  OK')
            with open("ping_report.txt", 'a') as file:
                file.write(f'IP:{ip_start}  OK\n')
            return
        print(f'IP:{ip_start}  Failed')
        with open("ping_report.txt", 'a') as file:
            file.write(f'IP:{ip_start}, Failed!\n')
        return


def ping102(ip_start, ip_target):
    ping_result = subprocess.run(['powershell', '-Command', f'ping -S {ip_start} {ip_target}'], capture_output=True,
                                 text=True)  # ping -S 起點 終點
    ch_keyword = '%'
    ch_start_pos = ping_result.stdout.find(ch_keyword)
    if ch_start_pos != -1:
        ch_start_pos += len(ch_keyword)
        ping_result = ping_result.stdout[ch_start_pos - 4:ch_start_pos]
        print(f"Ping Failed, Loss Rate:{ping_result.replace('(', '')}")
        if ping_result == " (0%":
            print(f'IP:{ip_start}  OK')
            with open("ping_report.txt", 'a') as file:
                file.write(f'IP:{ip_start}  OK\n')
            return
        print(f'IP:{ip_start}  Failed')
        with open("ping_report.txt", 'a') as file:
            file.write(f'IP:{ip_start}, Failed!\n')
        return


def ping103(ip_start, ip_target):
    ping_result = subprocess.run(['powershell', '-Command', f'ping -S {ip_start} {ip_target}'], capture_output=True,
                                 text=True)  # ping -S 起點 終點
    ch_keyword = '%'
    ch_start_pos = ping_result.stdout.find(ch_keyword)
    if ch_start_pos != -1:
        ch_start_pos += len(ch_keyword)
        ping_result = ping_result.stdout[ch_start_pos - 4:ch_start_pos]
        print(f"Result, Loss Rate:{ping_result.replace('(', '')}")
        if ping_result == " (0%":
            print(f'IP:{ip_start}  OK')
            with open("ping_report.txt", 'a') as file:
                file.write(f'IP:{ip_start}  OK\n')
            return
        print(f'IP:{ip_start}  Failed')
        with open("ping_report.txt", 'a') as file:
            file.write(f'IP:{ip_start}, Failed!\n')
            return


if __name__ == "__main__":
    thread1 = threading.Thread(target=ping101, args=('192.168.1.101', '192.168.1.1'))
    thread2 = threading.Thread(target=ping102, args=('192.168.2.102', '192.168.2.1'))
    thread3 = threading.Thread(target=ping103, args=('192.168.2.103', '192.168.2.1'))

    thread1.start()
    thread2.start()
    thread3.start()
    thread1.join()
    thread2.join()
    thread3.join()
    # ping(ip_start, ip_target)
