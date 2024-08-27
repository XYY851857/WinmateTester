import subprocess
import threading
import time

file_lock = threading.Lock()


def connect(combined):
    try:
        result = subprocess.run(['powershell', '-Command', combined], capture_output=True, text=True, check=True)
        return

    except subprocess.CalledProcessError as e:
        print('Wi-Fi Set Failed\n')
        print(e.stderr)
        with open('ERROR_report.txt', 'a') as errfile:
            errfile.write(e.stderr)
        return


def get_info():
    # ENZH = ['adapter', 'IPv4 Address']
    ENZH = ['卡', 'IPv4 位址']
    result = subprocess.run(['powershell', '-Command', 'ipconfig /all'], capture_output=True, text=True)
    output = result.stdout + "\n\n\n\n\n"
    target_interface = f"{ENZH[0]}"
    ipv4_address = None
    dict1 = {'192.168.1.101': 'None', '192.168.2.102': 'None', '192.168.2.103': 'None'}
    lines = output.splitlines()
    for i in range(len(lines)):
        line = lines[i].strip()
        adapter_name = line.split(f'{ENZH[0]}')[-1].split(':')[0].strip()
        if target_interface in line:
            for j in range(i, i + 10):
                detail_line = lines[j].strip()
                if detail_line.startswith(f"{ENZH[1]}"):
                    ipv4_address = detail_line.split(':')[-1].split('(')[0].strip()
                    dict1[f'{ipv4_address}'] = f'{adapter_name}'
                    print(f"{adapter_name} 的 IPv4 位址是: {ipv4_address}")
                    break
    return dict1


def ping(ip_start, ip_target, target_info):
    ping_result = subprocess.run(['powershell', '-Command', f'ping -S {ip_start} {ip_target}'], capture_output=True,
                                 text=True)  # ping -S 起點 終點
    ch_keyword = '%'
    ch_start_pos = ping_result.stdout.find(ch_keyword)
    if ch_start_pos != -1:
        ch_start_pos += len(ch_keyword)
        ping_result = ping_result.stdout[ch_start_pos - 4:ch_start_pos]
        if ping_result == " (0%":  # 遺失率0%
            print(f'Adapter:{target_info}, IP:{ip_start}  PASS')
            return
        print(f'IP:{ip_start}  Failed  Loss Rate:{ping_result.replace('(', '')}')
        return


if __name__ == "__main__":
    name = 'WM_Tester'
    path = f'.\\new\\\Wi-Fi-{name}.xml'

    combined = f'''
                    $currentPolicy = Get-ExecutionPolicy
                    Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

                    $profilePath = "{path}"
                    netsh wlan add profile filename=$profilePath
                    netsh wlan connect name="{name}"

                    Set-ExecutionPolicy -ExecutionPolicy $currentPolicy -Scope Process -Force
                '''

    connect(combined)
    time.sleep(5)
    info_data = get_info()
    thread1 = threading.Thread(target=ping, args=('192.168.1.101', '192.168.1.1', info_data['192.168.1.101']))
    time.sleep(0.1)
    thread2 = threading.Thread(target=ping, args=('192.168.2.102', '192.168.2.1', info_data['192.168.2.102']))
    time.sleep(0.1)
    thread3 = threading.Thread(target=ping, args=('192.168.2.103', '192.168.2.1', info_data['192.168.2.103']))

    thread1.start()
    thread2.start()
    thread3.start()
    thread1.join()
    thread2.join()
    thread3.join()
    # ping(ip_start, ip_target)
