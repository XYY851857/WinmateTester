import os
import shutil
import tkinter as tk
from tkinter import messagebox
from tkinter.ttk import Progressbar
import threading


def read_paths_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        paths = [line.strip() for line in f if line.strip()]

    folder_names = [os.path.basename(path) for path in paths]
    return folder_names, paths


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


def copy_tree_with_progress(src_folder, dst_folder):
    total_files = sum([len(files) for r, d, files in os.walk(src_folder)])
    copied_files = 0

    def copy_file(src_file, dst_file):
        nonlocal copied_files
        with open(src_file, 'rb') as src, open(dst_file, 'wb') as dst:
            buffer = src.read(1024 * 1024)
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


def update_button_color(color):
    start_button.config(bg=color, fg='white')


def start_copy(paths_dict):
    try:
        selected_option = listbox.get(listbox.curselection())
        dst_base_folder = 'C:\\'
    except tk.TclError:
        messagebox.showwarning("錯誤", "請選擇一個選項")
        return

    if selected_option == "清除Card1, Card2":
        storage_card_folder = os.path.join(dst_base_folder, "Storage Card")
        storage_card2_folder = os.path.join(dst_base_folder, "Storage Card2")
        clear_directory(storage_card_folder)
        clear_directory(storage_card2_folder)
        os.makedirs(storage_card_folder, exist_ok=True)
        os.makedirs(storage_card2_folder, exist_ok=True)
        messagebox.showinfo("完成", f"Card, Card2 已清除")
        update_button_color("green")
    else:
        src_folder = paths_dict.get(selected_option)
        if src_folder:
            storage_card_folder = os.path.join(dst_base_folder, "Storage Card")
            storage_card2_folder = os.path.join(dst_base_folder, "Storage Card2")
            clear_directory(storage_card_folder)
            clear_directory(storage_card2_folder)
            os.makedirs(storage_card_folder, exist_ok=True)
            os.makedirs(storage_card2_folder, exist_ok=True)

            threading.Thread(target=copy_tree_with_progress, args=(src_folder, storage_card_folder)).start()


def close_app():
    root.destroy()


def create_gui():
    global root, progress_var, combo, start_button, entry, listbox

    root = tk.Tk()
    root.title("SetupUtility")
    root.state('zoom')
    font = ('Arial', 20)

    folder_names, paths = read_paths_from_file(".\\data\\path.txt")
    formatted_names = [f'清除Card1, Card2,  安裝{name}' for name in folder_names]
    formatted_names.append("清除Card1, Card2")
    paths_dict = dict(zip(formatted_names[:-1], paths))
    label = tk.Label(root, text="請選擇執行項目:", font=font)
    label.pack(pady=10)

    entry = tk.Entry(root, font=font, width=0)
    entry.forget()

    listbox_frame = tk.Frame(root)
    listbox_frame.pack(pady=5, fill='x')
    listbox = tk.Listbox(listbox_frame, font=font, height=0)
    for item in formatted_names:
        listbox.insert(tk.END, item)
    listbox.pack(side='left', fill='x', expand=True)

    def on_select(event):
        entry.delete(0, tk.END)
        selection = listbox.get(listbox.curselection())
        entry.insert(0, selection)

    listbox.bind('<ButtonRelease-1>', on_select)

    button_frame = tk.Frame(root)
    button_frame.pack(pady=10, fill='x')

    start_button = tk.Button(button_frame, text="開始", command=lambda: start_copy(paths_dict), font=font)
    start_button.pack(side='right', padx=5, expand=True, fill='x')

    end_button = tk.Button(button_frame, text="結束", command=close_app, font=font)
    end_button.pack(side='left', padx=5, expand=True, fill='x')

    progress_var = tk.DoubleVar()
    progress_bar = Progressbar(root, variable=progress_var, maximum=100)
    progress_bar.pack(pady=20, padx=20, fill='x')

    root.mainloop()


if __name__ == "__main__":
    create_gui()
