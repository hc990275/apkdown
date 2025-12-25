import os
import sys
import threading
import shutil
import json
import requests
import tkinter as tk
from tkinter import ttk

# --- 路径配置 (自动获取当前目录，兼容 EXE 和 脚本运行) ---
if getattr(sys, 'frozen', False):
    # 如果是打包后的 exe，使用 exe 所在目录
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # 如果是脚本运行，使用脚本所在目录
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 设置下载目录为当前目录下的 "Download" 文件夹
download_dir = os.path.join(BASE_DIR, "Download")
version_folder = os.path.join(download_dir, "VersionInfo")

# 确保目录存在
os.makedirs(download_dir, exist_ok=True)
os.makedirs(version_folder, exist_ok=True)

# 设置 GitHub 用户代理
USER_AGENT = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36 EdgA/121.0.0.0"

# --- 版本信息 URL (将被自动化脚本替换) ---
urls = {
    "OK版手机": "https://raw.githubusercontent.com/lystv/fmapp/ok/apk/release/mobile.json",
    "OK版电视": "https://raw.githubusercontent.com/lystv/fmapp/ok/apk/release/leanback.json",
    "OK版Pro": "https://raw.githubusercontent.com/lystv/fmapp/ok/apk/pro/v.txt",
    "蜜蜂版手机": "https://raw.githubusercontent.com/FongMi/Release/fongmi/apk/mobile.json",
    "蜜蜂版电视": "https://raw.githubusercontent.com/FongMi/Release/fongmi/apk/leanback.json"
}

# --- APK 下载链接映射 (将被自动化脚本替换，仅保留推荐版本) ---
apk_links = {
    # OK版 (仅保留 32位)
    "OK版手机_32": "lystv/fmapp/ok/apk/release/mobile-armeabi_v7a.apk",
    "OK版电视_32": "lystv/fmapp/ok/apk/release/leanback-armeabi_v7a.apk",
    
    # OK 4.x
    "OK安卓4版本_APK": "lystv/fmapp/ok/apk/kitkat/leanback.apk",

    # OK Pro (仅保留标准版)
    "OK版Pro_手机Pro": "lystv/fmapp/ok/apk/pro/mobile-pro.apk",
    "OK版Pro_电视Pro": "lystv/fmapp/ok/apk/pro/leanback-pro.apk",

    # 蜜蜂版 (仅保留 32位，统一映射)
    "蜜蜂版手机_PY32": "FongMi/Release/fongmi/apk/mobile-armeabi_v7a.apk",
    "蜜蜂版手机_JAVA32": "FongMi/Release/fongmi/apk/mobile-armeabi_v7a.apk",
    "蜜蜂版电视_PY32": "FongMi/Release/fongmi/apk/leanback-armeabi_v7a.apk",
    "蜜蜂版电视_JAVA32": "FongMi/Release/fongmi/apk/leanback-armeabi_v7a.apk",
}

# --- GUI 辅助函数 ---
def append_log_safe(message):
    root.after(0, _append_log_gui, message)

def _append_log_gui(message):
    log_text.insert(tk.END, message + "\n")
    log_text.yview(tk.END)

def update_progress_safe(value):
    root.after(0, _update_progress_gui, value)

def _update_progress_gui(value):
    progress_bar['value'] = value

def set_all_buttons_state(state):
    root.after(0, _set_all_buttons_gui, state)

def _set_all_buttons_gui(state):
    if 'start_button' in globals() and start_button.winfo_exists():
         start_button.config(state=state)
    if 'open_dir_button' in globals() and open_dir_button.winfo_exists():
         open_dir_button.config(state=state)
    if 'kitkat_button' in globals() and kitkat_button.winfo_exists():
         kitkat_button.config(state=state)

# --- 操作系统交互 ---
def open_download_directory():
    target_dir = os.path.realpath(download_dir)
    append_log_safe(f"打开目录: {target_dir}")
    try:
        os.startfile(target_dir) # Windows Only
    except Exception as e:
        append_log_safe(f"❌ 打开目录失败: {e}")

# --- 核心逻辑 (后台线程) ---
def check_json_update(name):
    url = urls.get(name)
    if not url: return False
    
    old_json_file = os.path.join(version_folder, f"{name}.json")
    new_json_file = os.path.join(version_folder, f"{name}临时.json")
    updated = False

    append_log_safe(f"正在检查 {name} ...")

    try:
        response = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=15)
        response.raise_for_status()
        with open(new_json_file, 'wb') as f:
            f.write(response.content)
    except Exception as e:
        append_log_safe(f"⚠️ 下载版本信息失败: {e}")
        return False

    old_version = ""
    new_version = ""

    # 解析版本号
    try:
        if name == "OK版Pro": # 纯文本
            if os.path.exists(old_json_file):
                with open(old_json_file, "r", encoding='utf-8') as f: old_version = f.readline().strip()
            with open(new_json_file, "r", encoding='utf-8') as f: new_version = f.readline().strip()
        else: # JSON
            if os.path.exists(old_json_file):
                with open(old_json_file, 'r', encoding='utf-8') as f: old_version = json.load(f).get("name", "")
            with open(new_json_file, 'r', encoding='utf-8') as f: new_version = json.load(f).get("name", "")
    except Exception:
        pass

    append_log_safe(f"{name}: {old_version} -> {new_version}")

    if new_version and new_version != old_version:
        append_log_safe(f"🚀 发现 {name} 新版本，准备更新...")
        shutil.copy(new_json_file, old_json_file)
        updated = True
    else:
        updated = False

    if os.path.exists(new_json_file): os.remove(new_json_file)
    return updated

def download_apk(apk_name):
    update_progress_safe(0)
    relative_path = apk_links.get(apk_name)
    if not relative_path:
        append_log_safe(f"⚠️ 未找到 {apk_name} 的下载链接")
        return

    apk_url = f"https://raw.githubusercontent.com/{relative_path}"
    clean_name = apk_name.replace("_APK", "")
    apk_path = os.path.join(download_dir, f"{clean_name}.apk")

    append_log_safe(f"📥 下载: {clean_name}.apk")
    
    try:
        response = requests.get(apk_url, stream=True, headers={'User-Agent': USER_AGENT}, timeout=60)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(apk_path, 'wb') as f:
            for data in response.iter_content(chunk_size=8192):
                f.write(data)
                downloaded += len(data)
                if total_size > 0:
                    update_progress_safe(int((downloaded / total_size) * 100))

        append_log_safe(f"✅ 完成: {clean_name}.apk")
        update_progress_safe(100)
    except Exception as e:
        append_log_safe(f"❌ 下载失败: {e}")
        update_progress_safe(0)

def _run_kitkat_download():
    set_all_buttons_state(tk.DISABLED)
    try:
        download_apk("OK安卓4版本_APK")
    finally:
        set_all_buttons_state(tk.NORMAL)

def run_update_logic():
    set_all_buttons_state(tk.DISABLED)
    update_progress_safe(0)
    try:
        # 1. 检查 OK版 Pro
        if check_json_update("OK版Pro"):
            download_apk("OK版Pro_手机Pro")
            download_apk("OK版Pro_电视Pro")
        
        # 2. 检查 OK版 手机
        if check_json_update("OK版手机"):
            download_apk("OK版手机_32")

        # 3. 检查 OK版 电视
        if check_json_update("OK版电视"):
            download_apk("OK版电视_32")

        # 4. 检查 蜜蜂版 手机
        if check_json_update("蜜蜂版手机"):
            download_apk("蜜蜂版手机_PY32") # 默认下载 PY32 (通用)
            download_apk("蜜蜂版手机_JAVA32")

        # 5. 检查 蜜蜂版 电视
        if check_json_update("蜜蜂版电视"):
            download_apk("蜜蜂版电视_PY32") # 默认下载 PY32 (通用)
            download_apk("蜜蜂版电视_JAVA32")

        append_log_safe("\n🏁 所有检查完成")
        update_progress_safe(100)
    except Exception as e:
        append_log_safe(f"⚠️ 发生错误: {e}")
    finally:
        set_all_buttons_state(tk.NORMAL)

# --- GUI 布局 ---
root = tk.Tk()
root.title("影视更新工具 (Windows版)")
root.geometry("600x450")

main_frame = ttk.Frame(root, padding="10")
main_frame.pack(fill=tk.BOTH, expand=True)

start_button = ttk.Button(main_frame, text="🚀 一键检查更新", command=lambda: threading.Thread(target=run_update_logic, daemon=True).start())
start_button.pack(fill=tk.X, pady=5)

open_dir_button = ttk.Button(main_frame, text="📂 打开下载目录", command=open_download_directory)
open_dir_button.pack(fill=tk.X, pady=5)

kitkat_button = ttk.Button(main_frame, text="⬇️ 下载 OK安卓4.x专用版", command=lambda: threading.Thread(target=_run_kitkat_download, daemon=True).start())
kitkat_button.pack(fill=tk.X, pady=5)

log_text = tk.Text(main_frame, height=12)
log_text.pack(fill=tk.BOTH, expand=True, pady=5)

progress_bar = ttk.Progressbar(main_frame, orient="horizontal", mode="determinate")
progress_bar.pack(fill=tk.X, pady=5)

append_log_safe("程序就绪，点击上方按钮开始工作。")
root.mainloop()
