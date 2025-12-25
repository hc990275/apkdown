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
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

download_dir = os.path.join(BASE_DIR, "Download")
version_folder = os.path.join(download_dir, "VersionInfo")
os.makedirs(download_dir, exist_ok=True)
os.makedirs(version_folder, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36 EdgA/121.0.0.0"

# --- 版本信息 URL (将被自动化脚本替换) ---
urls = {
    "OK版手机": "https://raw.githubusercontent.com/lystv/fmapp/ok/apk/release/mobile.json",
    "OK版电视": "https://raw.githubusercontent.com/lystv/fmapp/ok/apk/release/leanback.json",
    "OK版Pro": "https://raw.githubusercontent.com/lystv/fmapp/ok/apk/pro/v.txt",
    "蜜蜂版手机": "https://raw.githubusercontent.com/FongMi/Release/fongmi/apk/mobile.json",
    "蜜蜂版电视": "https://raw.githubusercontent.com/FongMi/Release/fongmi/apk/leanback.json"
}

# --- APK 下载链接映射 (仅保留32位/Pro/4.x) ---
apk_links = {
    "OK版手机_32": "lystv/fmapp/ok/apk/release/mobile-armeabi_v7a.apk",
    "OK版电视_32": "lystv/fmapp/ok/apk/release/leanback-armeabi_v7a.apk",
    "OK安卓4版本_APK": "lystv/fmapp/ok/apk/kitkat/leanback.apk",
    "OK版Pro_手机Pro": "lystv/fmapp/ok/apk/pro/mobile-pro.apk",
    "OK版Pro_电视Pro": "lystv/fmapp/ok/apk/pro/leanback-pro.apk",
    # 蜜蜂版 (通用32位)
    "蜜蜂版手机_PY32": "FongMi/Release/fongmi/apk/mobile-armeabi_v7a.apk",
    "蜜蜂版手机_JAVA32": "FongMi/Release/fongmi/apk/mobile-armeabi_v7a.apk",
    "蜜蜂版电视_PY32": "FongMi/Release/fongmi/apk/leanback-armeabi_v7a.apk",
    "蜜蜂版电视_JAVA32": "FongMi/Release/fongmi/apk/leanback-armeabi_v7a.apk",
}

# --- GUI 辅助 ---
def append_log_safe(message):
    root.after(0, _append_log_gui, message)
def _append_log_gui(message):
    log_text.insert(tk.END, message + "\n")
    log_text.yview(tk.END)
def update_progress_safe(value):
    root.after(0, lambda: progress_bar.config(value=value))
def set_all_buttons_state(state):
    root.after(0, lambda: [btn.config(state=state) for btn in [start_button, open_dir_button, kitkat_button]])

def open_download_directory():
    target_dir = os.path.realpath(download_dir)
    append_log_safe(f"打开目录: {target_dir}")
    try:
        os.startfile(target_dir)
    except Exception as e:
        append_log_safe(f"❌ 无法打开目录: {e}")

# --- 核心逻辑 ---
def check_json_update(name):
    url = urls.get(name)
    if not url: return False
    
    old_json = os.path.join(version_folder, f"{name}.json")
    new_json = os.path.join(version_folder, f"{name}临时.json")
    
    try:
        append_log_safe(f"🔎 正在检查: {name} ...")
        resp = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=15)
        resp.raise_for_status()
        with open(new_json, 'wb') as f: f.write(resp.content)
    except Exception as e:
        append_log_safe(f"⚠️ 检查失败 ({name}): {e}")
        return False

    old_ver = ""
    new_ver = ""
    try:
        if name == "OK版Pro":
            if os.path.exists(old_json): old_ver = open(old_json, "r", encoding='utf-8').read().strip()
            new_ver = open(new_json, "r", encoding='utf-8').read().strip()
        else:
            if os.path.exists(old_json): old_ver = json.load(open(old_json, 'r', encoding='utf-8')).get("name", "")
            new_ver = json.load(open(new_json, 'r', encoding='utf-8')).get("name", "")
    except: pass

    updated = False
    if new_ver and new_ver != old_ver:
        append_log_safe(f"🚀 {name} 发现新版本: {new_ver} (旧: {old_ver})")
        shutil.copy(new_json, old_json)
        updated = True
    else:
        append_log_safe(f"✅ {name} 已是最新 ({new_ver})")

    if os.path.exists(new_json): os.remove(new_json)
    return updated

def download_apk(apk_name):
    rel_path = apk_links.get(apk_name)
    if not rel_path: return
    
    url = f"https://raw.githubusercontent.com/{rel_path}"
    fname = apk_name.replace("_APK", "") + ".apk"
    fpath = os.path.join(download_dir, fname)
    
    append_log_safe(f"⬇️ 正在下载: {fname}")
    try:
        r = requests.get(url, stream=True, headers={'User-Agent': USER_AGENT}, timeout=60)
        total = int(r.headers.get('content-length', 0))
        done = 0
        with open(fpath, 'wb') as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
                done += len(chunk)
                if total: update_progress_safe(int(done/total*100))
        append_log_safe(f"✅ 下载完成: {fname}")
    except Exception as e:
        append_log_safe(f"❌ 下载出错: {e}")

def run_update_logic():
    set_all_buttons_state(tk.DISABLED)
    update_progress_safe(0)
    
    try:
        if check_json_update("OK版Pro"):
            download_apk("OK版Pro_手机Pro")
            download_apk("OK版Pro_电视Pro")
        
        if check_json_update("OK版手机"):
            download_apk("OK版手机_32")

        if check_json_update("OK版电视"):
            download_apk("OK版电视_32")

        if check_json_update("蜜蜂版手机"):
            download_apk("蜜蜂版手机_PY32") # 下载32位
            download_apk("蜜蜂版手机_JAVA32") # 保持兼容性

        if check_json_update("蜜蜂版电视"):
            download_apk("蜜蜂版电视_PY32") # 下载32位
            download_apk("蜜蜂版电视_JAVA32") # 保持兼容性

        append_log_safe("\n🏁 所有操作执行完毕！")
        update_progress_safe(100)
    except Exception as e:
        append_log_safe(f"⚠️ 全局错误: {e}")
    finally:
        set_all_buttons_state(tk.NORMAL)

def _run_kitkat():
    set_all_buttons_state(tk.DISABLED)
    download_apk("OK安卓4版本_APK")
    set_all_buttons_state(tk.NORMAL)

# --- GUI ---
root = tk.Tk()
root.title("影视更新工具 (精简版)")
root.geometry("600x480")

frame = ttk.Frame(root, padding=10)
frame.pack(fill=tk.BOTH, expand=True)

start_button = ttk.Button(frame, text="🚀 一键检查更新 (32位/Pro)", command=lambda: threading.Thread(target=run_update_logic, daemon=True).start())
start_button.pack(fill=tk.X, pady=5)

open_dir_button = ttk.Button(frame, text="📂 打开下载文件夹", command=open_download_directory)
open_dir_button.pack(fill=tk.X, pady=5)

kitkat_button = ttk.Button(frame, text="⬇️ 下载 OK安卓4.x (旧机专用)", command=lambda: threading.Thread(target=_run_kitkat, daemon=True).start())
kitkat_button.pack(fill=tk.X, pady=5)

log_text = tk.Text(frame, height=15)
log_text.pack(fill=tk.BOTH, expand=True, pady=5)

progress_bar = ttk.Progressbar(frame, orient="horizontal", mode="determinate")
progress_bar.pack(fill=tk.X, pady=5)

append_log_safe("欢迎使用！点击上方按钮开始更新。")
root.mainloop()
