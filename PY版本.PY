import os
# import random # 此脚本中已不再使用 random_color，可移除
import requests
import subprocess # 导入 subprocess
import sys # 导入 sys
import shutil
import tkinter as tk
from tkinter import ttk
# import re # 此脚本中已不再使用 remove_ansi_escape，可移除
import json
import threading  # 导入 threading

# 设置 APK 版本号 JSON 文件所在目录
# 确保此目录存在或处理创建
VERSION_DIR = "F:/Program Files/Git/storage/SH下载文件/版本文件夹"
os.makedirs(VERSION_DIR, exist_ok=True) # 确保目录存在

# 设置 GitHub 用户代理
USER_AGENT = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36 EdgA/121.0.0.0"

# 设置 GitHub 仓库地址 (仅作为信息，不直接用于构建URL)
# REPO = "hc990275/apkdown" # 此变量未直接使用

# Random color function (未在GUI日志中使用，可移除)
# def random_color():
#     return random.randint(31, 37) # 从 31 到 37 的颜色代码

# Remove ANSI escape characters (未在GUI日志中使用，可移除)
# def remove_ansi_escape(text):
#     ansi_escape = re.compile(r'(?:\x1b[^m]*m)|(?:\x1b[^m]*\[.*?m)')
#     return ansi_escape.sub('', text)

# APK JSON 下载地址 (raw content URL)
urls = {
    "OK版手机": "https://raw.githubusercontent.com/lystv/fmapp/main/apk/release/mobile.json",  # OK版手机 JSON 地址 (未变更)
    "OK版电视": "https://raw.githubusercontent.com/lystv/fmapp/main/apk/release/leanback.json", # OK版电视 JSON 地址 (未变更)
    "蜜蜂版手机": "https://raw.githubusercontent.com/FongMi/Release/fongmi/apk/release/mobile.json", # 未变更
    "蜜蜂版电视": "https://raw.githubusercontent.com/FongMi/Release/fongmi/apk/release/leanback.json", # 未变更
    "OK版Pro": "https://raw.githubusercontent.com/lystv/fmapp/ok/apk/pro/v.txt"  # !!! 更新 OK版Pro JSON 地址 !!!
}

# APK 下载链接 (存储的是 relative path from raw.githubusercontent.com/)
# Base URL 是 https://raw.githubusercontent.com/
apk_links = {
    # OK版 (使用 lystv/fmapp 仓库, 不区分 Java/Python) - 未变更
    "OK版手机_32": "lystv/fmapp/main/apk/release/mobile-armeabi_v7a.apk",
    "OK版手机_64": "lystv/fmapp/main/apk/release/mobile-arm64_v8a.apk",

    "OK版电视_32": "lystv/fmapp/main/apk/release/leanback-armeabi_v7a.apk",
    "OK版电视_64": "lystv/fmapp/main/apk/release/leanback-arm64_v8a.apk",

    # OK海信专版 (与OK版手机版本号一致) - 未变更
    "OK海信专版_APK": "lystv/fmapp/main/apk/release/%E6%B5%B7%E4%BF%A1%E4%B8%93%E7%89%88.apk", # (%E6%B5%B7%E4%BF%A1%E4%B8%93%E7%89%88 是 "海信专版" 的 URL 编码)

    # OK安卓4版本 (KitKat), 独立下载 - 未变更
    "OK安卓4版本_APK": "lystv/fmapp/main/apk/kitkat/leanback.apk",

    # OK版Pro (使用 lystv/fmapp 仓库, ok 分支) - !!! 更新 OK版Pro APK 路径 !!!
    "OK版Pro_手机Pro": "lystv/fmapp/ok/apk/pro/mobile-pro.apk",
    "OK版Pro_手机emu-Pro": "lystv/fmapp/ok/apk/pro/mobile-emu-pro.apk",
    "OK版Pro_电视Pro": "lystv/fmapp/ok/apk/pro/leanback-pro.apk",


    # 蜜蜂版 (使用 FongMi/Release 仓库, 区分 Java/Python) - 未变更
    "蜜蜂版手机_PY32": "fongmi/apk/release/mobile-python-armeabi_v7a.apk",
    "蜜蜂版手机_PY64": "fongmi/apk/release/mobile-python-arm64_v8a.apk",
    "蜜蜂版手机_JAVA32": "fongmi/apk/release/mobile-java-armeabi_v7a.apk",
    "蜜蜂版手机_JAVA64": "fongmi/apk/release/mobile-java-arm64_v8a.apk",

    "蜜蜂版电视_PY32": "fongmi/apk/release/leanback-python-armeabi_v7a.apk",
    "蜜蜂版电视_PY64": "fongmi/apk/release/leanback-python-arm64_v8a.apk",
    "蜜蜂版电视_JAVA32": "fongmi/apk/release/leanback-java-armeabi_v7a.apk",
    "蜜蜂版电视_JAVA64": "fongmi/apk/release/leanback-java-arm64_v8a.apk",
}

# 下载目录
download_dir = "F:/Program Files/Git/storage/SH下载文件"
version_folder = os.path.join(download_dir, "版本文件夹")
os.makedirs(download_dir, exist_ok=True) # 确保下载目录存在
os.makedirs(version_folder, exist_ok=True) # 确保版本文件夹存在


# --- GUI Update Helper Functions (Thread-safe) ---
# 这些函数由后台线程调用，用于安全地在主线程中更新GUI

def append_log_safe(message):
    # 在主线程中调度向日志文本框添加消息
    root.after(0, _append_log_gui, message)

def _append_log_gui(message):
    # 实际更新GUI日志文本的函数
    log_text.insert(tk.END, message + "\n")
    log_text.yview(tk.END) # 自动滚动到底部

def update_progress_safe(value):
    # 在主线程中调度更新进度条的值
    root.after(0, _update_progress_gui, value)

def _update_progress_gui(value):
    # 实际更新GUI进度条的函数
    progress_bar['value'] = value

# def enable_button_safe(button): # 不再单独使用这些，由 set_all_buttons_state 统一管理
#     root.after(0, lambda: button.config(state=tk.NORMAL))
# def disable_button_safe(button):
#      root.after(0, lambda: button.config(state=tk.DISABLED))

def set_all_buttons_state(state):
    """安全地设置所有相关按钮的状态 (DISABLED 或 NORMAL)。"""
    # 使用 root.after 确保在主线程执行
    root.after(0, _set_all_buttons_gui, state)

def _set_all_buttons_gui(state):
     """实际设置所有相关按钮的状态。"""
     # 确保按钮控件已创建并为全局变量，并检查控件是否存在
     # 使用 globals().get() 更安全，避免 NameError 如果在按钮创建前调用
     if 'start_button' in globals() and start_button.winfo_exists():
         start_button.config(state=state)
     if 'open_dir_button' in globals() and open_dir_button.winfo_exists():
         # 打开目录按钮通常可以在任何时候使用，除非它自己正在执行任务
         # 但是为了简化状态管理，我们在任何下载/更新任务进行时禁用它
         open_dir_button.config(state=state)
     if 'kitkat_button' in globals() and kitkat_button.winfo_exists():
         kitkat_button.config(state=state)


# --- OS Interaction Functions ---

def open_download_directory():
    """在操作系统的文件管理器中打开下载目录。"""
    # 这里不禁用所有按钮，因为打开目录操作通常很快且独立
    # set_all_buttons_state(tk.DISABLED) # 可以选择在这里禁用，并在finally重新启用

    target_dir = os.path.realpath(download_dir) # 获取绝对路径
    append_log_safe(f"尝试打开目录: {target_dir}")

    try:
        if sys.platform == "win32":
            # Windows: 使用 os.startfile，这是 Windows API 调用，不会在成功时抛异常
            os.startfile(target_dir)
        elif sys.platform == "darwin":
            # macOS
            subprocess.run(['open', target_dir], check=True)
        elif sys.platform.startswith('linux'):
            # Linux (使用 xdg-open)
            subprocess.run(['xdg-open', target_dir], check=True)
        else:
            append_log_safe(f"⚠️ 警告: 不支持的操作系统 '{sys.platform}'，无法自动打开目录。")
            return

        append_log_safe("成功打开下载目录。")

    except FileNotFoundError:
         append_log_safe(f"❌ 错误: 未找到打开目录的命令或目录不存在: {target_dir}")
    except Exception as e:
        # 捕获除 FileNotFoundError 外的其他异常 (主要来自非Windows上的 subprocess.run)
        append_log_safe(f"❌ 打开目录时发生错误: {e}")
    # finally:
    #     set_all_buttons_state(tk.NORMAL) # 如果上面禁用了，在这里重新启用


# --- Core Logic Functions (在后台线程中运行) ---

# 下载 JSON 并比较版本号 (兼容 OK版Pro 的 v.txt 纯文本版本号)
def check_json_update(name):
    url = urls[name]
    old_json_file = os.path.join(version_folder, f"{name}.json")
    new_json_file = os.path.join(version_folder, f"{name}临时.json")
    updated = False

    append_log_safe(f"正在检查 {name} 的版本...")

    try:
        # 增加超时设置，并使用 headers
        response = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=10)
        response.raise_for_status() # 检查HTTP请求是否成功 (例如404, 500错误)
        with open(new_json_file, 'wb') as f:
            f.write(response.content)
        append_log_safe(f"成功下载 {name} 的新版本信息.")
    except requests.exceptions.RequestException as e:
        # 捕获所有requests相关的异常 (连接错误, HTTP错误, 超时等)
        append_log_safe(f"⚠️ 下载 {name} 版本信息失败，错误：{e}")
        # 下载失败后删除临时文件
        if os.path.exists(new_json_file):
             try:
                 os.remove(new_json_file)
             except Exception as rm_e:
                 append_log_safe(f"⚠️ 删除临时文件失败: {new_json_file} - {rm_e}")
        return False # JSON 下载失败返回 False
    except Exception as e:
        # 捕获其他可能的异常
        append_log_safe(f"⚠️ 处理 {name} 版本信息时发生未知错误：{e}")
        if os.path.exists(new_json_file):
             try:
                 os.remove(new_json_file)
             except Exception as rm_e:
                 append_log_safe(f"⚠️ 删除临时文件失败: {new_json_file} - {rm_e}")
        return False # 其他错误也返回 False


    old_version = ""
    new_version = ""

    # 判断是否为 OK版Pro (v.txt 纯文本版本号)
    if name == "OK版Pro":
        # OK版Pro JSON (v.txt) 处理逻辑 (纯文本版本号)
        if os.path.exists(old_json_file):
            try:
                # 使用 with...as 确保文件被关闭
                with open(old_json_file, "r", encoding='utf-8') as f:
                    old_version = f.readline().strip() # 读取第一行并去掉空白符
            except Exception as file_e:
                append_log_safe(f"⚠️ 读取旧版本文件 {old_json_file} 失败: {file_e}")
                old_version = "Error reading old file" # 标记读取失败
        try:
            # 使用 with...as 确保文件被关闭
            with open(new_json_file, "r", encoding='utf-8') as f:
                new_version = f.readline().strip() # 读取第一行并去掉空白符
        except Exception as file_e:
             append_log_safe(f"⚠️ 读取新版本文件 {new_json_file} 失败: {file_e}")
             new_version = "Error reading new file" # 标记读取失败
    else:
        # 其他 JSON 处理逻辑 (JSON 格式版本号)
        if os.path.isfile(old_json_file):
            try:
                # 使用 with...as 确保文件被关闭
                with open(old_json_file, 'r', encoding='utf-8') as f:
                    old_json_data = json.load(f)
                    old_version = old_json_data.get("name", "")
            except (json.JSONDecodeError, Exception) as e:
                append_log_safe(f"⚠️ 解析旧版本 JSON 文件失败: {old_json_file} - {e}")
                old_version = "Error parsing old JSON" # 标记解析失败

        try:
            # 使用 with...as 确保文件被关闭
            with open(new_json_file, 'r', encoding='utf-8') as f:
                new_json_data = json.load(f)
                new_version = new_json_data.get("name", "")
        except (json.JSONDecodeError, Exception) as e:
            append_log_safe(f"⚠️ 解析新版本 JSON 文件失败: {new_json_file} - {e}")
            new_version = "Error parsing new JSON" # 标记解析失败


    append_log_safe(f"{name} 旧版本号: {old_version if old_version else '未找到'}")
    append_log_safe(f"{name} 新版本号: {new_version if new_version else '未找到'}")

    # 如果成功获取到新版本号，并且新版本号不为空且与旧版本号不同
    if new_version and new_version != old_version:
        append_log_safe(f"🚀 发现 {name} 新版本，更新本地版本信息并准备下载 APK...")
        try:
            shutil.copy(new_json_file, old_json_file)
            updated = True
        except Exception as copy_e:
             append_log_safe(f"⚠️ 复制新版本文件失败: {copy_e}")
             updated = False # 复制失败，标记为未更新，不进行下载
    else:
        append_log_safe(f"{name} 版本未变更或无法获取新版本信息，无需更新。")
        updated = False # 未更新

    # 在函数末尾，无论是否更新，都删除临时 JSON 文件
    try:
        if os.path.exists(new_json_file):
           os.remove(new_json_file)
    except Exception as e:
        append_log_safe(f"⚠️ 删除临时文件失败: {new_json_file} - {e}")

    return updated # 返回 updated 标记

# 下载 APK
def download_apk(apk_name):
    # 重置进度条为当前 APK 的下载准备
    update_progress_safe(0)

    # 构建完整的 APK 下载 URL
    # apk_links 中存储的是从 raw.githubusercontent.com/ 开始的路径
    # 例如: 'lystv/fmapp/main/apk/release/mobile-armeabi_v7a.apk'
    try:
        relative_path = apk_links[apk_name]
        apk_url = f"https://raw.githubusercontent.com/{relative_path}"
    except KeyError:
        append_log_safe(f"错误：在 apk_links 中未找到名称为 '{apk_name}' 的条目，无法构建下载 URL。")
        update_progress_safe(0)
        return

    # 将 APK 名称中的特殊字符转换为文件名安全的格式（例如移除 "_APK" 后缀，处理中文等）
    # 这里简单处理，只移除 "_APK" 后缀
    clean_apk_name = apk_name.replace("_APK", "")
    # 构建完整的本地保存路径
    apk_path = os.path.join(download_dir, f"{clean_apk_name}.apk")


    append_log_safe(f"📥 正在下载: {clean_apk_name}.apk") # 日志中显示干净的名称

    try:
        # 使用 stream=True 进行分块下载，增加超时设置和 headers
        response = requests.get(apk_url, stream=True, headers={'User-Agent': USER_AGENT}, timeout=60)
        response.raise_for_status() # 检查HTTP请求是否成功 (例如404, 500等错误)

        # 获取文件总大小，如果 Content-Length 不可用，设为0
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        # 分块写入文件并更新进度条
        with open(apk_path, 'wb') as f:
            # 遍历响应内容，按块读取
            for data in response.iter_content(chunk_size=8192): # 可以调整块大小
                f.write(data)
                downloaded += len(data)
                # 更新进度条 (如果已知总大小)
                if total_size > 0:
                    # 计算当前进度百分比
                    progress = int((downloaded / total_size) * 100)
                    # 安全地更新GUI上的进度条
                    update_progress_safe(progress)
                # else:
                    # 如果总大小未知，当前 mode="determinate" 不支持平滑更新

        append_log_safe(f"✅ 下载完成: {clean_apk_name}.apk") # 日志中显示干净的名称
        update_progress_safe(100) # 确保下载完成后进度条显示100%

    except requests.exceptions.RequestException as e:
        # 捕获所有requests相关的异常 (连接错误, HTTP错误, 超时等)
        append_log_safe(f"❌ APK 下载失败，错误：{e}")
        # 下载失败时重置进度条
        update_progress_safe(0)
        # 可选：如果下载失败，删除不完整的临时文件
        if os.path.exists(apk_path):
            try:
                os.remove(apk_path)
                append_log_safe(f"已删除不完整的下载文件: {apk_path}")
            except Exception as rm_e:
                append_log_safe(f"⚠️ 删除不完整文件失败: {apk_path} - {rm_e}")

    except Exception as e:
        # 捕获其他可能的异常 (文件写入错误等)
        append_log_safe(f"❌ 下载过程中发生未知错误：{e}")
        # 发生错误时重置进度条
        update_progress_safe(0)
        # 同上，删除不完整的临时文件
        if os.path.exists(apk_path):
            try:
                os.remove(apk_path)
                append_log_safe(f"已删除不完整的下载文件: {apk_path}")
            except Exception as rm_e:
                append_log_safe(f"⚠️ 删除不完整文件失败: {apk_path} - {rm_e}")


# --- 后台任务执行函数 ---

def _run_kitkat_download():
    """在后台线程中执行下载 OK 安卓4版本 APK 的任务。"""
    try:
        append_log_safe("--- 开始下载 OK 安卓4版本 ---")
        update_progress_safe(0) # 重置进度条
        download_apk("OK安卓4版本_APK") # 调用 download_apk
        append_log_safe("--- OK 安卓4版本下载完成 ---")
    except Exception as e:
        # Note: download_apk itself logs errors, this catches unexpected issues
        append_log_safe(f"⚠️ 下载 OK 安卓4版本任务异常终止: {e}")
    finally:
        # 任务完成后重新启用所有按钮
        set_all_buttons_state(tk.NORMAL)


# --- 主要更新逻辑 (在后台线程中运行) ---

def run_update_logic():
    """包含检查更新和下载APK的主要循环逻辑，在后台线程中执行。"""
    # 在开始前禁用所有按钮
    set_all_buttons_state(tk.DISABLED)
    # 清空日志区域（可选，如果不想保留上次的日志则取消注释）
    # root.after(0, log_text.delete, '1.0', tk.END)

    append_log_safe("--- 开始检查所有版本更新 ---")
    update_progress_safe(0) # 开始时重置总体进度条

    try:
        # 遍历所有定义的版本类型
        for name in urls.keys():
            # 每次检查或下载前，重置进度条到0
            update_progress_safe(0)
            # 检查当前版本是否有更新
            # 调用 check_json_update
            if check_json_update(name):
                # 如果有更新，根据版本名称下载对应的所有APK
                append_log_safe(f"\n🧩 {name} 检测到有更新，准备下载相关 APKs...")
                apks_to_download = []
                if name == "OK版Pro":
                    # OK版Pro 下载列表
                    apks_to_download = [
                        "OK版Pro_手机Pro",
                        "OK版Pro_手机emu-Pro",
                        "OK版Pro_电视Pro"
                    ]
                elif name == "OK版手机":
                    # OK版手机 (不区分 Java/Python, 只区分 32/64) 且包含海信专版
                    apks_to_download = [
                        f"{name}_32", # 注意这里是 _32 和 _64
                        f"{name}_64",
                        "OK海信专版_APK" # 添加海信专版
                    ]
                    append_log_safe("包含 OK 海信专版 APK (版本号与 OK版手机一致)...")
                elif name == "OK版电视":
                     # OK版电视 (不区分 Java/Python, 只区分 32/64)
                     apks_to_download = [
                        f"{name}_32",
                        f"{name}_64"
                    ]
                else: # 蜜蜂版手机, 蜜蜂版电视 (区分 Java/Python)
                     apks_to_download = [
                        f"{name}_PY32",
                        f"{name}_PY64",
                        f"{name}_JAVA32",
                        f"{name}_JAVA64"
                    ]


                # 遍历列表，逐个下载 APK
                for apk_name in apks_to_download:
                     # 确保 apk_links 中存在此名称，避免 KeyError
                     if apk_name in apk_links:
                         download_apk(apk_name) # 调用 download_apk
                         # 可选：在两次下载之间加入短暂延迟，让GUI有时间处理更新
                         # root.after(10)
                     else:
                         append_log_safe(f"⚠️ 警告: APK名称 '{apk_name}' 未在 apk_links 字典中找到，跳过下载。")


            # 可选：在检查完一个版本类型后加入短暂延迟
            # root.after(50)


        append_log_safe("\n--- 所有版本检查和更新完成 ---")
        update_progress_safe(100) # 所有任务完成后进度条设为100%

    except Exception as e:
        # 捕获更新过程中的意外错误
        append_log_safe(f"\n⚠️ 更新过程中发生严重错误: {e}")
        update_progress_safe(0) # 发生严重错误时重置进度条

    finally:
        # 无论成功或失败，任务结束后都重新启用所有按钮
        set_all_buttons_state(tk.NORMAL)


# --- GUI 设置 ---
root = tk.Tk()
root.title("APK 更新脚本")
# root.geometry("750x550") # 初始大小由内容和布局管理器决定，可以设置一个最小值

# 主 Frame 用于布局所有控件
main_frame = ttk.Frame(root, padding="10")
# 使用 grid 布局主 Frame，并使其随窗口缩放而填充
main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# 配置根窗口和主 Frame 的 grid 权重，使它们可以随窗口缩放
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
main_frame.columnconfigure(0, weight=1) # 让第一列（包含按钮、日志、进度条的列）可伸缩
main_frame.columnconfigure(1, weight=0) # 第二列（中间按钮）不伸缩
main_frame.columnconfigure(2, weight=0) # 第三列（最右按钮）不伸缩
# main_frame.columnconfigure(3, weight=0) # 滚动条列不需要单独权重，它在grid中被指定了列
main_frame.rowconfigure(2, weight=1) # 让日志文本框所在的第三行可伸缩 (从0开始计数)


# 创建按钮并将其定义为全局变量，以便 set_all_buttons_state 函数可以访问它们
start_button = ttk.Button(main_frame, text="开始检查更新", command=lambda: threading.Thread(target=run_update_logic, daemon=True).start())
open_dir_button = ttk.Button(main_frame, text="打开下载目录", command=open_download_directory)
kitkat_button = ttk.Button(main_frame, text="下载 OK安卓4版本", command=lambda: threading.Thread(target=_run_kitkat_download, daemon=True).start())


# 将按钮放置在第一行
start_button.grid(row=0, column=0, padx=(0, 5), pady=10, sticky=tk.W) # padx 增加右侧填充
open_dir_button.grid(row=0, column=1, padx=5, pady=10, sticky=tk.W) # padx 增加左右填充
kitkat_button.grid(row=0, column=2, padx=(5, 0), pady=10, sticky=tk.W) # padx 增加左侧填充


# 日志标签
log_label = ttk.Label(main_frame, text="日志输出:")
# 将标签放置在第二行第一列
log_label.grid(row=1, column=0, sticky=tk.W)

# 日志文本框
log_text = tk.Text(main_frame, height=15, width=70, wrap=tk.WORD) # wrap=tk.WORD 按单词换行
# 将文本框放置在第三行，跨越按钮列，并使其随单元格伸缩
log_text.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))

# 为日志文本框添加垂直滚动条
# 滚动条放置在第三行最右侧的列
log_scrollbar = ttk.Scrollbar(main_frame, command=log_text.yview)
log_scrollbar.grid(row=2, column=3, sticky=(tk.N, tk.S)) # 放在第3列
# 将滚动条关联到文本框
log_text['yscrollcommand'] = log_scrollbar.set

# 进度标签
progress_label = ttk.Label(main_frame, text="当前任务进度:")
# 将标签放置在第四行第一列
progress_label.grid(row=3, column=0, sticky=tk.W)

# 下载进度条
progress_bar = ttk.Progressbar(main_frame, orient="horizontal", mode="determinate") # mode="determinate" 表示已知总进度的进度条
# 将进度条放置在第五行，跨越所有按钮列，并使其随单元格水平伸缩
progress_bar.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky=(tk.W, tk.E))


# 初始消息在日志中
append_log_safe("请点击按钮启动程序。")

# 启动 GUI 事件循环
root.mainloop()
