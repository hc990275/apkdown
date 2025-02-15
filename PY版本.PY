import os
import random
import requests
import subprocess
import sys
import shutil
import tkinter as tk
from tkinter import ttk
import re
import json  # 导入 json 库

# 设置 APK 版本号 JSON 文件所在目录
VERSION_DIR = "F:/Program Files/Git/storage/SH下载文件/版本文件夹"

# 设置 GitHub 用户代理
USER_AGENT = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36 EdgA/121.0.0.0"

# 设置 GitHub 仓库地址
REPO = "hc990275/apkdown"

# 随机颜色函数
def random_color():
    return random.randint(31, 37)  # 从 31 到 37 的颜色代码

# 带颜色的打印函数（加高亮和空格）
def print_color(text, text_widget=None):
    # 去除无效的控制字符
    clean_text = remove_ansi_escape(text)
    if text_widget:
        text_widget.insert(tk.END, clean_text + "\n")
        text_widget.yview(tk.END)  # 自动滚动到底部
    else:
        print(clean_text)

# 去除 ANSI 控制字符（比如颜色控制）
def remove_ansi_escape(text):
    ansi_escape = re.compile(r'(?:\x1b[^m]*m)|(?:\x1b[^m]*\[.*?m)')
    return ansi_escape.sub('', text)


# APK JSON 下载地址
urls = {
    "OK版手机": "https://raw.githubusercontent.com/FongMi/Release/okjack/apk/release/mobile.json",
    "OK版电视": "https://raw.githubusercontent.com/FongMi/Release/okjack/apk/release/leanback.json",
    "蜜蜂版手机": "https://raw.githubusercontent.com/FongMi/Release/fongmi/apk/release/mobile.json",
    "蜜蜂版电视": "https://raw.githubusercontent.com/FongMi/Release/fongmi/apk/release/leanback.json",
    "OK版Pro": "https://raw.githubusercontent.com/FongMi/Release/okjack/apk/pro/v.txt"  # 新增 OK版Pro JSON 地址
}

# APK 下载链接
apk_links = {
    "OK版手机_PY32": "okjack/apk/release/mobile-python-armeabi_v7a.apk",
    "OK版手机_PY64": "okjack/apk/release/mobile-python-arm64_v8a.apk",
    "OK版手机_JAVA32": "okjack/apk/release/mobile-java-armeabi_v7a.apk",
    "OK版手机_JAVA64": "okjack/apk/release/mobile-java-arm64_v8a.apk",

    "OK版电视_PY32": "okjack/apk/release/leanback-python-armeabi_v7a.apk",
    "OK版电视_PY64": "okjack/apk/release/leanback-python-arm64_v8a.apk",
    "OK版电视_JAVA32": "okjack/apk/release/leanback-java-armeabi_v7a.apk",
    "OK版电视_JAVA64": "okjack/apk/release/leanback-java-arm64_v8a.apk",

    "蜜蜂版手机_PY32": "fongmi/apk/release/mobile-python-armeabi_v7a.apk",
    "蜜蜂版手机_PY64": "fongmi/apk/release/mobile-python-arm64_v8a.apk",
    "蜜蜂版手机_JAVA32": "fongmi/apk/release/mobile-java-armeabi_v7a.apk",
    "蜜蜂版手机_JAVA64": "fongmi/apk/release/mobile-java-arm64_v8a.apk",

    "蜜蜂版电视_PY32": "fongmi/apk/release/leanback-python-armeabi_v7a.apk",
    "蜜蜂版电视_PY64": "fongmi/apk/release/leanback-python-arm64_v8a.apk",
    "蜜蜂版电视_JAVA32": "fongmi/apk/release/leanback-java-armeabi_v7a.apk",
    "蜜蜂版电视_JAVA64": "fongmi/apk/release/leanback-java-arm64_v8a.apk",

    "OK版Pro_手机Pro": "okjack/apk/pro/mobile-pro.apk",  # 新增 OK版Pro APK 下载链接
    "OK版Pro_手机emu-Pro": "okjack/apk/pro/mobile-emu-pro.apk",  # 新增 OK版Pro APK 下载链接
    "OK版Pro_电视Pro": "okjack/apk/pro/leanback-pro.apk",  # 新增 OK版Pro APK 下载链接
}

# 下载目录
download_dir = "F:/Program Files/Git/storage/SH下载文件"
version_folder = os.path.join(download_dir, "版本文件夹")
os.makedirs(version_folder, exist_ok=True)

# 下载 JSON 并比较版本号 (兼容 OK版Pro 的 v.txt 纯文本版本号)
def check_json_update(name, text_widget=None):
    url = urls[name]
    old_json_file = os.path.join(version_folder, f"{name}.json")
    new_json_file = os.path.join(version_folder, f"{name}临时.json")
    updated = False  # 添加 updated 变量，标记是否更新

    try:
        response = requests.get(url, headers={'User-Agent': USER_AGENT})  # 添加 user-agent
        response.raise_for_status()  # 异常处理
        with open(new_json_file, 'wb') as f:
            f.write(response.content)
    except requests.exceptions.RequestException as e:
        print_color(f"JSON 下载失败，错误：{str(e)}", text_widget)
        return False  # JSON 下载失败也返回 False，不进行后续操作，并删除临时文件

    old_version = ""
    new_version = ""

    # 判断是否为 OK版Pro (v.txt 纯文本版本号)
    if name == "OK版Pro":
        # OK版Pro JSON (v.txt) 处理逻辑 (纯文本版本号)
        if os.path.exists(old_json_file):
            with open(old_json_file, "r", encoding='utf-8') as f:
                old_version = f.readline().strip()  # 读取第一行并去掉空白符
        with open(new_json_file, "r", encoding='utf-8') as f:
            new_version = f.readline().strip()  # 读取第一行并去掉空白符
    else:
        # 其他 JSON 处理逻辑 (JSON 格式版本号)
        if os.path.isfile(old_json_file):
            try:
                with open(old_json_file, 'r', encoding='utf-8') as f:
                    old_json_data = json.load(f)
                    old_version = old_json_data.get("name", "")
            except json.JSONDecodeError:
                old_version = "Error parsing old JSON"

        try:
            with open(new_json_file, 'r', encoding='utf-8') as f:
                new_json_data = json.load(f)
                new_version = new_json_data.get("name", "")
        except json.JSONDecodeError:
            new_version = "Error parsing new JSON"

    print_color(f"{name} 旧版本号: {old_version if old_version else '未找到'}", text_widget)
    print_color(f"{name} 新版本号: {new_version if new_version else '未找到'}", text_widget)

    if new_version and new_version != old_version:
        print_color("发现新版本，更新 JSON 并下载 APK...", text_widget)
        shutil.copy(new_json_file, old_json_file)
        updated = True  # 标记为已更新
    else:
        print_color("版本未变更，无需更新。", text_widget)
        updated = False  # 标记为未更新

    # 在函数末尾，无论是否更新，都删除临时 JSON 文件
    try:
        os.remove(new_json_file)
    except Exception as e:  # 捕获删除文件可能出现的异常
        print_color(f"⚠️ 删除临时 JSON 文件失败: {new_json_file} - {e}", text_widget)

    return updated  # 返回 updated 标记，用于后续判断是否需要下载 APK

# 下载 APK
def download_apk(apk_name, progress_bar, text_widget=None):
    apk_url = f"https://raw.githubusercontent.com/FongMi/Release/{apk_links[apk_name]}"
    apk_path = os.path.join(download_dir, f"{apk_name}.apk")

    print_color(f"正在下载: {apk_name}.apk", text_widget)  # 添加打印 apk_name

    try:
        response = requests.get(apk_url, stream=True, headers={'User-Agent': USER_AGENT})  # 添加 user-agent
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(apk_path, 'wb') as f:
            for data in response.iter_content(chunk_size=1024):
                f.write(data)
                downloaded += len(data)
                progress = int((downloaded / total_size) * 100)
                progress_bar['value'] = progress
                progress_bar.update()
        print_color(f"下载完成: {apk_name}.apk", text_widget)
    except requests.exceptions.RequestException as e:
        print_color(f"APK 下载失败，错误：{str(e)}", text_widget)

# GUI 部分
root = tk.Tk()
root.title("APK 更新脚本")
root.geometry("500x500")

# 日志输出框
log_text = tk.Text(root, height=20, width=60)
log_text.pack(padx=10, pady=10)

# 下载进度条
progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.pack(padx=10, pady=10)


# 检查 JSON 更新并下载 APK
for name in urls.keys():
    if check_json_update(name, log_text):
        print_color(f"{name} 检测到有更新，准备下载 APK...", log_text)
        # 根据不同的 name 下载不同的 APK
        if name == "OK版Pro":
            download_apk(f"{name}_手机Pro", progress_bar, log_text)
            download_apk(f"{name}_手机emu-Pro", progress_bar, log_text)
            download_apk(f"{name}_电视Pro", progress_bar, log_text)
        else:
            download_apk(f"{name}_PY32", progress_bar, log_text)
            download_apk(f"{name}_PY64", progress_bar, log_text)
            download_apk(f"{name}_JAVA32", progress_bar, log_text)
            download_apk(f"{name}_JAVA64", progress_bar, log_text)

# 启动 GUI 窗口
root.mainloop()
