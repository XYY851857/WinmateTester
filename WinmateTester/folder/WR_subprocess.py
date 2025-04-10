import os
import threading

def write_and_verify(path, size_in_bytes, disk_num):
    """
    寫入指定大小的檔案並進行讀取驗證。
    如果檔案大小或內容不正確，則記錄錯誤並輸出相應訊息。
    """
    chunk_size = 1024 * 1024  # 每次寫入的區塊大小（1 MB）
    data = '0' * chunk_size
    total_written = 0

    # 寫檔區段
    try:
        with open(path, 'w') as f:
            while total_written < size_in_bytes:
                remaining_bytes = size_in_bytes - total_written
                if remaining_bytes >= chunk_size:
                    f.write(data)
                    total_written += chunk_size
                else:
                    f.write('0' * remaining_bytes)
                    total_written += remaining_bytes
    except Exception as e:
        print(f'USB: 磁碟 {disk_num} 在寫入檔案時發生錯誤：{e}')
        with open('ERROR_report.txt', 'a', encoding='utf-8') as errfile:
            errfile.write(f'\nWR_subprocess: {path} 寫入檔案時發生錯誤：{e}\n')
        return

    # 驗證檔案大小
    actual_size = os.path.getsize(path)
    if actual_size != size_in_bytes:
        print(f'USB: 磁碟 {disk_num} 寫入/讀取大小不正確。')
        with open('ERROR_report.txt', 'a', encoding='utf-8') as errfile:
            errfile.write(f'\nWR_subprocess: {path} 寫入/讀取大小不正確。\n')
        return

    # 讀檔區段（一次性讀取檔案用於驗證）
    try:
        with open(path, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f'USB: 磁碟 {disk_num} 在讀取檔案時發生錯誤：{e}')
        with open('ERROR_report.txt', 'a', encoding='utf-8') as errfile:
            errfile.write(f'\nWR_subprocess: {path} 讀取檔案時發生錯誤：{e}\n')
        return

    # 檢查內容是否正確
    # 這裡直接用大小相符的 '0' * size_in_bytes 來比對
    expected_content = '0' * size_in_bytes
    if content == expected_content:
        print(f'USB: Disk {disk_num} Write/Read PASS.')
    else:
        print(f'USB: 磁碟 {disk_num} 寫入/讀取內容不正確。')
        with open('ERROR_report.txt', 'a', encoding='utf-8') as errfile:
            errfile.write(f'\nWR_subprocess: {path} 寫入/讀取內容不正確。\n')

if __name__ == "__main__":
    file_size = 10 * 1024 * 1024  # 測試檔案大小（10 MB）
    disk_list = ["D", "E"]        # 測試磁碟清單
    file_name = f":\\WR_test_file_{file_size // (1024 * 1024)}MB.txt"

    threads = []
    for disk in disk_list:
        # 檢查磁碟是否存在
        if os.path.exists(f"{disk}:\\"):
            file_path = f"{disk}{file_name}"
            try:
                thread = threading.Thread(target=write_and_verify,
                                          args=(file_path, file_size, disk))
                threads.append(thread)
                thread.start()
            except Exception as e:
                print(f'USB: 磁碟 {disk} 發生例外：{e}')
        else:
            print(f'USB: {disk}:\\ 不存在或無法存取。')

    # 等待所有寫入/讀取測試執行完畢
    for thread in threads:
        thread.join()

    # 清理測試檔案
    for disk in disk_list:
        file_path = f"{disk}{file_name}"
        if os.path.exists(file_path):
            os.remove(file_path)
