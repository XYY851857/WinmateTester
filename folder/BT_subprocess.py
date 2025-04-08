import subprocess

def pair(device_name, pin_code):
    executable_path = '.\\0\\Winmate_Test_GUI\\exes\\btpair.exe'
    try:
        result = subprocess.run(
            [executable_path, '-n', device_name, '-p', pin_code],
            capture_output=True,
            text=True,
            check=True
        )
        print('藍牙: Bluetooth Connect Success')  # 供 TEST_GUI 讀取
        if result.stderr:
            print(f'ERROR: \n {result.stderr}')
    except subprocess.CalledProcessError as e:
        keyword = 'Code: '
        start_pos = e.stderr.find(keyword)
        if start_pos != -1:
            start_pos += len(keyword)
            code = e.stderr[start_pos:start_pos + 4]
            if code == '1244':
                print('藍牙: PASS')
                return 'PASS'
            elif code.startswith('258'):
                print('藍牙: Connect Timeout')
                return 'Failed'
            elif code.startswith('31'):
                print('藍牙: PASS')
                return 'PASS'
            else:
                print(f"藍牙: Error:\n {e.stderr}")
        else:
            print(f"藍牙: ERROR\n{e.stderr}")

        # 寫入錯誤檔案 (維持原功能)
        # with open('.\\log\\ERROR_report.txt', 'a', encoding='utf-8') as errfile:
        #     errfile.write(f'BT_subprocess.py:  {e.stderr}\n')

        return f'ERROR\n{e.stderr}'

def main():
    device_name = 'BT3.0 Mouse'
    pin_code = ''  # 若不需要可留空
    return pair(device_name, pin_code)

if __name__ == "__main__":
    result = main()
