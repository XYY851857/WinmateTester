import os
import threading


def write(path, size_in_bytes, disk_num):
    chunk_size = 1024  # 每次寫入的大小（以字節為單位）
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

    actual_size = os.path.getsize(path)
    if actual_size != size_in_bytes:  # size incorrect
        print(f'USB: Disk {disk_num} Write/Read Size Incorrect.')
        with open('ERROR_report.txt', 'a') as errfile:
            errfile.write(f'\nWR_subprocess: {path} Write/Read Size Incorrect.\n')
        return

    with open(path, 'r') as file:
        content = file.read()
        expected_content = '0' * size_in_bytes
        if content == expected_content:  # PASS
            print(f'USB: Disk {disk_num} Write/Read PASS.')
            return
        else:  # content incorrect
            print(f'USB: Disk {disk_num} Write/Read Content Incorrect.')
            with open('ERROR_report.txt', 'a') as errfile:
                errfile.write(f'\nWR_subprocess: {path} Write/Read Content Incorrect.\n')
            return


if __name__ == "__main__":
    file_size = 10 * 1024 * 1024  # 10 MB

    disk_list = ["D", "E"]
    state = 'Failed'
    file_name = f':\\WR_test_file_{file_size // 1024 // 1024:.0f}MB.txt'

    threads = []
    for i in range(0, 2):
        if os.path.exists(f'{disk_list[i]}:\\'):
            file_path = f'{disk_list[i]}{file_name}'
            try:
                thread = threading.Thread(target=write, args=(file_path, file_size, disk_list[i]))
                threads.append(thread)
                thread.start()

            except Exception as e:
                print(f'USB: {disk_list[i]}: {e}')
        else:
            print(f'USB: {disk_list[i]}:\\ Not Exist')

    for thread in threads:
        thread.join()

    for i in range(0, 2):
        if os.path.exists(f'{disk_list[i]}{file_name}'):
            os.remove(f'{disk_list[i]}{file_name}')
