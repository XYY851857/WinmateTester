import subprocess
import os


def write(path, size_in_bytes):
    chunk_size = 1024  # 每次寫入的塊大小（以字節為單位）
    data = '0' * chunk_size  # 填充檔案的資料
    total_written = 0

    with open(path, 'w') as file:
        while total_written < size_in_bytes:
            remaining_bytes = size_in_bytes - total_written
            if remaining_bytes >= chunk_size:
                file.write(data)
                total_written += chunk_size
            else:
                file.write('0' * remaining_bytes)
                total_written += remaining_bytes

    print(f'已成功創建 {path}，大小為 {total_written} 字節。')

    # 驗證檔案大小
    actual_size = os.path.getsize(path)
    if actual_size == size_in_bytes:
        print(f'檔案 {path} 實際大小為 {actual_size} 字節，大小驗證成功！')
    else:
        print(f'錯誤：檔案 {path} 實際大小為 {actual_size} 字節，與預期的 {size_in_bytes} 字節不符！')
        return False

    # 驗證檔案內容
    with open(path, 'r') as file:
        content = file.read()
        expected_content = '0' * size_in_bytes
        if content == expected_content:
            print('檔案內容驗證成功！')
        else:
            print('錯誤：檔案內容不符！')
            return False

    return True


if __name__ == "__main__":
    # 指定檔案大小，例如 10 KB
    file_size = int(input("input write size(MB):")) * 1024 * 1024 # 10 KB = 10 * 1024 字節
    write(f'.\\test_file_{file_size/1024/1024:.0f}MB.txt', file_size)
