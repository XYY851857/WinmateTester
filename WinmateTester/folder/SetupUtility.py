import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar, Combobox
import threading


# 讀取 txt 檔案中的路徑
def read_paths_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            paths = [line.strip() for line in f if line.strip()]
    except UnicodeDecodeError:
        # 如果 UTF-8 失敗，可以嘗試使用其他編碼
        with open(file_path, 'r', encoding='cp950') as f:
            paths = [line.strip() for line in f if line.strip()]

    # 只顯示資料夾名稱
    folder_names = [os.path.basename(path) for path in paths]
    return folder_names, paths


# 清除資料夾中的所有內容
def clear_directory(directory):
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except PermissionError:
                messagebox.showinfo("錯誤", f"{file_path}無法存取或刪除'")
            except Exception as e:
                messagebox.showinfo("錯誤", f"刪除{file_path}發生錯誤")


# 複製資料夾中的檔案和資料夾
def copy_tree_with_progress(src_folder, dst_folder):
    total_files = sum([len(files) for r, d, files in os.walk(src_folder)])
    copied_files = 0

    def copy_file(src_file, dst_file):
        nonlocal copied_files
        with open(src_file, 'rb') as src, open(dst_file, 'wb') as dst:
            buffer = src.read(1024 * 1024)  # 1 MB buffer
            while buffer:
                dst.write(buffer)
                buffer = src.read(1024 * 1024)
        copied_files += 1
        progress_var.set(copied_files / total_files * 100)
        root.update_idletasks()

    try:
        for dirpath, dirnames, filenames in os.walk(src_folder):
            dst_dirpath = os.path.join(dst_folder, os.path.relpath(dirpath, src_folder))
            os.makedirs(dst_dirpath, exist_ok=True)
            for filename in filenames:
                src_file = os.path.join(dirpath, filename)
                dst_file = os.path.join(dst_dirpath, filename)
                copy_file(src_file, dst_file)
        update_button_color("green")
        messagebox.showinfo("完成", f"資料夾已複製到 '{dst_folder}'")
    except Exception as e:
        update_button_color("red")
        messagebox.showerror("錯誤", f"複製資料夾時發生錯誤: {e}")


# 更新按鈕顏色
def update_button_color(color):
    start_button.config(bg=color)


# 在新線程中執行複製操作
def start_copy(paths_dict):
    selected_option = combo.get()
    dst_base_folder = 'C:\\a\\'

    if selected_option == "清除Card1, Card2":
        # 固定的目標資料夾路徑
        # target_folder = 'C:\\新增資料夾2'  # test path
        storage_card_folder = os.path.join(dst_base_folder, "storage Card")
        storage_card2_folder = os.path.join(dst_base_folder, "storage Card2")
        clear_directory(storage_card_folder)
        clear_directory(storage_card2_folder)
        os.makedirs(storage_card_folder, exist_ok=True)
        os.makedirs(storage_card2_folder, exist_ok=True)
        messagebox.showinfo("完成", f"Card, Card2 已清除")
    else:
        src_folder = paths_dict.get(selected_option)
        if src_folder:
            # 創建或清除 storage Card 和 storage Card2 資料夾
            storage_card_folder = os.path.join(dst_base_folder, "storage Card")
            storage_card2_folder = os.path.join(dst_base_folder, "storage Card2")
            clear_directory(storage_card_folder)
            clear_directory(storage_card2_folder)
            os.makedirs(storage_card_folder, exist_ok=True)
            os.makedirs(storage_card2_folder, exist_ok=True)

            # 複製所選 source file 到 storage Card
            threading.Thread(target=copy_tree_with_progress, args=(src_folder, storage_card_folder)).start()


def close_app():
    root.destroy()


# 建立 GUI 界面
def create_gui():
    global root, progress_var, combo, start_button

    root = tk.Tk()
    root.title("SetupUtility")
    root.state('zoom')
    # root.geometry("600x400")

    # 讀取路徑並填充下拉式選單
    folder_names, paths = read_paths_from_file("C:\\Users\\cheng\\OneDrive\\桌面\\SetupUtility_Backup\\path.txt")  #TEST path
    # folder_names, paths = read_paths_from_file(".\\data\\path.txt")
    formatted_names = [f'清除Card1, Card2 安裝{name}' for name in folder_names]
    formatted_names.append("清除Card1, Card2")
    paths_dict = dict(zip(formatted_names[:-1], paths))
    label = tk.Label(root, text="請選擇執行項目:", font=('Arial', 20))
    label.pack(pady=10)

    combo = Combobox(root, values=formatted_names, width=40, font=('Arial', 20))
    combo.pack(pady=5)

    button_frame = tk.Frame(root)
    button_frame.pack(pady=10, fill='x')

    start_button = tk.Button(button_frame, text="開始", command=lambda: start_copy(paths_dict), font=('Arial', 20))
    start_button.pack(side='right', padx=5, expand=True, fill='x')

    end_button = tk.Button(button_frame, text="結束", command=close_app, font=('Arial', 20))
    end_button.pack(side='left', padx=5, expand=True, fill='x')


    progress_var = tk.DoubleVar()
    progress_bar = Progressbar(root, variable=progress_var, maximum=100)
    progress_bar.pack(pady=20, padx=20, fill='x')

    root.mainloop()


# 啟動 GUI
if __name__ == "__main__":
    create_gui()
