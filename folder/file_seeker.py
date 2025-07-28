import os
import time
import hashlib
import difflib

file_hashes = {}
file_snapshots = {}

def get_file_hash(path):
    try:
        with open(path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

def get_file_content(path):
    try:
        with open(path, 'rb') as f:
            return f.read()
    except:
        return None

def is_text(data):
    try:
        data.decode('utf-8')
        return True
    except:
        return False

def scan_folder(folder_path):
    paths = {}
    for root, dirs, files in os.walk(folder_path):
        for fname in files:
            path = os.path.join(root, fname)
            paths[path] = True
    return paths

def monitor_folder_polling(folder_path, interval=2):
    print(f"✨ 開始監控：{folder_path}")
    # 初始快照
    paths = scan_folder(folder_path)
    for path in paths:
        file_hashes[path] = get_file_hash(path)
        file_snapshots[path] = get_file_content(path)
    while True:
        time.sleep(interval)
        current_paths = scan_folder(folder_path)
        # 新增檔案
        for path in current_paths:
            if path not in file_hashes:
                file_hashes[path] = get_file_hash(path)
                file_snapshots[path] = get_file_content(path)
                print(f"💚 新增：{path}")
        # 刪除檔案
        for path in list(file_hashes):
            if path not in current_paths:
                print(f"❤️‍🔥 刪除：{path}")
                file_hashes.pop(path)
                file_snapshots.pop(path)
        # 修改檔案
        for path in current_paths:
            new_hash = get_file_hash(path)
            old_hash = file_hashes.get(path)
            if old_hash and new_hash != old_hash:
                print(f"💛 修改：{path}")
                old_content = file_snapshots.get(path, b"")
                new_content = get_file_content(path)
                if is_text(old_content) and is_text(new_content):
                    diff = difflib.unified_diff(
                        old_content.decode('utf-8', 'ignore').splitlines(),
                        new_content.decode('utf-8', 'ignore').splitlines(),
                        fromfile='before',
                        tofile='after',
                        lineterm=''
                    )
                    print("🔎 差異內容：")
                    for line in diff:
                        print(line)
                else:
                    print("🔎 二進位異動片段（前32 bytes）：")
                    for i in range(min(32, len(new_content or b""))):
                        before = old_content[i] if i < len(old_content) else None
                        after = new_content[i]
                        if before != after:
                            print(f"位置{i}: {before} -> {after}")
                file_hashes[path] = new_hash
                file_snapshots[path] = new_content

if __name__ == "__main__":
    folder = input("請輸入要監控的資料夾路徑：").strip()
    monitor_folder_polling(folder)