import os
import sys
import threading
import requests
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox

# --- 路径配置 ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

download_dir = os.path.join(BASE_DIR, "Download")
os.makedirs(download_dir, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
REPO = "hc990275/apkdown" # 您的仓库

# --- 工具自身版本号 (自动替换) ---
TOOL_VERSION = "v2025.12.28_1151" 

# --- 应用版本号 (自动替换) ---
OK_VER_MOBILE = "OK-3.5.7"
OK_VER_TV = "OK-3.5.7"
OK_VER_PRO = "OK-3.8.8-pro"
OK_VER_4X = "OK-2.5.0"
FM_VER_MOBILE = "FM-5.0.4"
FM_VER_TV = "FM-5.0.4"

# --- APK 下载链接映射 ---
apk_links = {
    "OK版手机_32": "lystv/fmapp/54dbf376f4fca72e12061e13fb689db87f99235b/apk/release/mobile-armeabi_v7a.apk",
    "OK版电视_32": "lystv/fmapp/54dbf376f4fca72e12061e13fb689db87f99235b/apk/release/leanback-armeabi_v7a.apk",
    "OK安卓4版本_APK": "lystv/fmapp/93fd99c68e7bddc4b903a2fe12fdbd372630610b/apk/kitkat/leanback.apk",
    "OK版Pro_手机Pro": "lystv/fmapp/08b161ad2417393aca9141ad63956c917e5fbd65/apk/pro/mobile-pro.apk",
    "OK版Pro_电视Pro": "lystv/fmapp/08b161ad2417393aca9141ad63956c917e5fbd65/apk/pro/leanback-pro.apk",
    "蜜蜂版手机_PY32": "fongmi/release/38ecab09fba63ecf10ef5eb92951b9554bb9f803/apk/mobile-armeabi_v7a.apk",
    "蜜蜂版手机_JAVA32": "fongmi/release/38ecab09fba63ecf10ef5eb92951b9554bb9f803/apk/mobile-armeabi_v7a.apk",
    "蜜蜂版电视_PY32": "fongmi/release/38ecab09fba63ecf10ef5eb92951b9554bb9f803/apk/leanback-armeabi_v7a.apk",
    "蜜蜂版电视_JAVA32": "fongmi/release/38ecab09fba63ecf10ef5eb92951b9554bb9f803/apk/leanback-armeabi_v7a.apk",
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
    try:
        os.startfile(os.path.realpath(download_dir))
    except Exception as e:
        append_log_safe(f"❌ 无法打开目录: {e}")

# --- 自我更新逻辑 ---
def check_tool_update():
    try:
        append_log_safe(f"📡 检查工具更新 (当前: {TOOL_VERSION})...")
        api_url = f"https://api.github.com/repos/{REPO}/releases/latest"
        resp = requests.get(api_url, headers={'User-Agent': USER_AGENT}, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        
        latest_tag = data.get("tag_name", "")
        if latest_tag and latest_tag != TOOL_VERSION:
            append_log_safe(f"🚀 发现新版本工具: {latest_tag}")
            
            # 寻找 EXE 下载链接
            exe_url = ""
            for asset in data.get("assets", []):
                if asset.get("name", "").endswith(".exe"):
                    exe_url = asset.get("browser_download_url")
                    break
            
            # 弹窗提示
            msg = f"发现新版本 {latest_tag}！\n\n当前版本: {TOOL_VERSION}\n\n是否立即前往下载新版 EXE？"
            if exe_url and messagebox.askyesno("发现更新", msg):
                webbrowser.open(exe_url)
        else:
            append_log_safe(f"✅ 工具已是最新版")
    except Exception as e:
        append_log_safe(f"⚠️ 检查工具更新失败: {e}")

# --- 核心逻辑 ---
def download_apk(apk_name, desc=""):
    rel_path = apk_links.get(apk_name)
    if not rel_path: return
    
    url = f"https://raw.githubusercontent.com/{rel_path}"
    fname = apk_name.replace("_APK", "") + ".apk"
    fpath = os.path.join(download_dir, fname)
    
    append_log_safe(f"⬇️ 下载 {desc}: {fname}")
    try:
        r = requests.get(url, stream=True, headers={'User-Agent': USER_AGENT}, timeout=60)
        total = int(r.headers.get('content-length', 0))
        done = 0
        with open(fpath, 'wb') as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
                done += len(chunk)
                if total: update_progress_safe(int(done/total*100))
        append_log_safe(f"✅ 完成")
    except Exception as e:
        append_log_safe(f"❌ 失败: {e}")

def run_download_all():
    set_all_buttons_state(tk.DISABLED)
    update_progress_safe(0)
    append_log_safe("🚀 开始批量下载任务...")
    
    try:
        download_apk("OK版Pro_手机Pro", f"OKPro手机({OK_VER_PRO})")
        download_apk("OK版Pro_电视Pro", f"OKPro电视({OK_VER_PRO})")
        download_apk("OK版手机_32", f"OK手机({OK_VER_MOBILE})")
        download_apk("OK版电视_32", f"OK电视({OK_VER_TV})")
        download_apk("蜜蜂版手机_PY32", f"蜜蜂手机({FM_VER_MOBILE})")
        download_apk("蜜蜂版电视_PY32", f"蜜蜂电视({FM_VER_TV})")
        
        append_log_safe("\n🏁 所有下载任务完成！")
        update_progress_safe(100)
    finally:
        set_all_buttons_state(tk.NORMAL)

def _run_kitkat():
    set_all_buttons_state(tk.DISABLED)
    download_apk("OK安卓4版本_APK", f"OK安卓4.x({OK_VER_4X})")
    set_all_buttons_state(tk.NORMAL)

# --- GUI ---
root = tk.Tk()
root.title(f"影视更新工具 {TOOL_VERSION}")
root.geometry("600x520")

# 信息面板
info_frame = ttk.LabelFrame(root, text="当前内置版本信息", padding=10)
info_frame.pack(fill=tk.X, padx=10, pady=5)
info_label = ttk.Label(info_frame, text=f"OK版: {OK_VER_MOBILE} | Pro: {OK_VER_PRO}\n蜜蜂版: {FM_VER_MOBILE}", justify=tk.CENTER)
info_label.pack()

# 按钮区域
btn_frame = ttk.Frame(root, padding=10)
btn_frame.pack(fill=tk.X)

start_button = ttk.Button(btn_frame, text="🚀 一键下载所有最新版", command=lambda: threading.Thread(target=run_download_all, daemon=True).start())
start_button.pack(fill=tk.X, pady=5)

open_dir_button = ttk.Button(btn_frame, text="📂 打开下载文件夹", command=open_download_directory)
open_dir_button.pack(fill=tk.X, pady=5)

kitkat_button = ttk.Button(btn_frame, text="⬇️ 下载 OK安卓4.x (旧机专用)", command=lambda: threading.Thread(target=_run_kitkat, daemon=True).start())
kitkat_button.pack(fill=tk.X, pady=5)

# 日志
log_text = tk.Text(root, height=12)
log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

progress_bar = ttk.Progressbar(root, orient="horizontal", mode="determinate")
progress_bar.pack(fill=tk.X, padx=10, pady=10)

append_log_safe(f"程序启动，版本: {TOOL_VERSION}")

# 启动后自动检查自身更新
root.after(1000, lambda: threading.Thread(target=check_tool_update, daemon=True).start())

root.mainloop()
