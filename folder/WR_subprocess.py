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

    print(f'{path}, size:{total_written} bytes created.')

    # 驗證檔案大小
    actual_size = os.path.getsize(path)
    if actual_size == size_in_bytes:
        print(f'{path}, size:{actual_size} bytes check size correct.')
    else:
        print(f'Error,  {path} actual size {actual_size} bytes, excepted {size_in_bytes} incorrect.')
        return False

    # 驗證檔案內容
    with open(path, 'r') as file:
        content = file.read()
        expected_content = '0' * size_in_bytes
        if content == expected_content:
            print(f'Disk:{path[:1]}:\\ Success')
            return True
        else:
            print('Error')
            return False


if __name__ == "__main__":
    # 指定檔案大小，例如 10 KB
    # file_size = int(input("input write size(MB):")) * 1024 * 1024
    file_size = 100 * 1024 * 1024  # 100 MB

    disk_list = ["D", "E"]
    for step in range(0, 2):
        print(f'Testing Disk: {disk_list[step]}')
        file_path = f'{disk_list[step]}:\\test_file_{file_size / 1024 / 1024:.0f}MB.txt'
        try:
            state = write(file_path, file_size)
            if os.path.exists(file_path):
                os.remove(file_path)
            print(state)
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            print(e)
        with open('WR_report.txt', 'a') as file:
            file.write(f'{disk_list[step]}:\\ Port OK\n')
