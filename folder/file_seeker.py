import os
import time
import hashlib
import difflib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 記錄每個檔案的內容hash與快照
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

class Analyzer(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory: return
        file_hashes[event.src_path] = get_file_hash(event.src_path)
        file_snapshots[event.src_path] = get_file_content(event.src_path)
        print(f"💚 新增：{event.src_path}")

    def on_deleted(self, event):
        if event.is_directory: return
        print(f"❤️‍🔥 刪除：{event.src_path}")
        file_hashes.pop(event.src_path, None)
        file_snapshots.pop(event.src_path, None)

    def on_modified(self, event):
        if event.is_directory: return
        old_hash = file_hashes.get(event.src_path)
        new_hash = get_file_hash(event.src_path)
        if old_hash != new_hash:
            print(f"💛 修改：{event.src_path}")
            old_content = file_snapshots.get(event.src_path, b"")
            new_content = get_file_content(event.src_path)
            # 嘗試文字diff
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
                # 二進位顯示不同bytes位置
                print("🔎 二進位異動片段（前32 bytes）：")
                for i in range(min(32, len(new_content or b""))):
                    before = old_content[i] if i < len(old_content) else None
                    after = new_content[i]
                    if before != after:
                        print(f"位置{i}: {before} -> {after}")
            # 更新snapshot
            file_hashes[event.src_path] = new_hash
            file_snapshots[event.src_path] = new_content

def monitor_folder(folder_path):
    print(f"✨ 開始監控：{folder_path}")
    # 初始快照
    for root, dirs, files in os.walk(folder_path):
        for fname in files:
            path = os.path.join(root, fname)
            file_hashes[path] = get_file_hash(path)
            file_snapshots[path] = get_file_content(path)

    event_handler = Analyzer()
    observer = Observer()
    observer.schedule(event_handler, folder_path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    folder = input("請輸入要監控的資料夾路徑：").strip()
    monitor_folder(folder)