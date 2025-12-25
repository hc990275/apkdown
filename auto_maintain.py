import requests
import json
import re
import datetime
import os
import sys

# ✅ 强制将标准输出设置为 UTF-8，防止 Windows 控制台打印中文报错
sys.stdout.reconfigure(encoding='utf-8')

# --- 配置区域 ---
SOURCE_JSON = "https://raw.githubusercontent.com/lystv/fmapp/app/yysd-zl.json"
SH_FILE = "apkdown.sh"
PY_FILE = "PY版本.PY"
LOG_FILE = "CHANGELOG.md"

def get_new_version():
    return datetime.datetime.now().strftime("v%Y.%m.%d_%H%M")

def fetch_data():
    print(f"Downloading {SOURCE_JSON}...")
    try:
        resp = requests.get(SOURCE_JSON, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        for category in data:
            if category.get("name") == "推薦":
                return category.get("list", [])
        return []
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

def extract_info(rec_list):
    """同时提取 URL 和 版本号"""
    info = {
        "urls": {},
        "vers": {}
    }
    
    def get_rel_path(url):
        return url.replace("https://raw.githubusercontent.com/", "")

    for item in rec_list:
        name = item.get("name", "")
        url = item.get("url", "")
        ver = item.get("version", "未知")
        
        if not url: continue
        path = get_rel_path(url)

        # OK版
        if "OK" in ver:
            if "手機-32" in name: 
                info["urls"]["OK_MOBILE_32"] = path
                info["vers"]["OK_VER_MOBILE"] = ver
            elif "電視-32" in name:
                info["urls"]["OK_TV_32"] = path
                info["vers"]["OK_VER_TV"] = ver
            elif "4.x" in name:
                info["urls"]["OK_KITKAT"] = path
                info["vers"]["OK_VER_4X"] = ver
            elif "手機pro" in name.lower() and "emu" not in name.lower():
                info["urls"]["OK_PRO_MOBILE"] = path
                info["vers"]["OK_VER_PRO"] = ver
            elif "電視pro" in name.lower():
                info["urls"]["OK_PRO_TV"] = path
        
        # 蜜蜂版
        elif "FM" in ver:
            if "手機-32" in name:
                info["urls"]["FM_MOBILE_32"] = path
                info["vers"]["FM_VER_MOBILE"] = ver
            elif "電視-32" in name:
                info["urls"]["FM_TV_32"] = path
                info["vers"]["FM_VER_TV"] = ver
                
    return info

def update_sh_file(info, new_version):
    if not os.path.exists(SH_FILE): return
    with open(SH_FILE, 'r', encoding='utf-8') as f: content = f.read()

    # 1. 更新脚本自身版本
    content = re.sub(r'SCRIPT_VERSION="v[^"]+"', f'SCRIPT_VERSION="{new_version}"', content)
    
    # 2. 更新应用版本号显示 (Shell 变量)
    for key, val in info["vers"].items():
        # 匹配 OK_VER_MOBILE="xxx"
        content = re.sub(rf'{key}="[^"]*"', f'{key}="{val}"', content)

    # 3. 更新下载链接
    mapping = info["urls"]
    updates = [
        (r'\["OK版手机_32"\]', "OK_MOBILE_32"),
        (r'\["OK版电视_32"\]', "OK_TV_32"),
        (r'\["OK安卓4版本_APK"\]', "OK_KITKAT"),
        (r'\["OK版Pro_手机Pro"\]', "OK_PRO_MOBILE"),
        (r'\["OK版Pro_电视Pro"\]', "OK_PRO_TV"),
        (r'\["蜜蜂版手机_32"\]', "FM_MOBILE_32"),
        (r'\["蜜蜂版电视_32"\]', "FM_TV_32"),
    ]
    for regex, key in updates:
        if key in mapping:
            content = re.sub(rf'({regex}=")([^"]+)(")', rf'\1{mapping[key]}\3', content)

    with open(SH_FILE, 'w', encoding='utf-8', newline='\n') as f: f.write(content)
    print(f"Updated {SH_FILE}")

def update_py_file(info):
    if not os.path.exists(PY_FILE): return
    with open(PY_FILE, 'r', encoding='utf-8') as f: content = f.read()

    # 1. 更新应用版本号显示 (Python 变量)
    for key, val in info["vers"].items():
        # 匹配 OK_VER_MOBILE = "xxx"
        content = re.sub(rf'{key}\s*=\s*"[^"]*"', f'{key} = "{val}"', content)

    # 2. 更新下载链接
    mapping = info["urls"]
    updates = [
        (r'"OK版手机_32"', "OK_MOBILE_32"),
        (r'"OK版电视_32"', "OK_TV_32"),
        (r'"OK安卓4版本_APK"', "OK_KITKAT"),
        (r'"OK版Pro_手机Pro"', "OK_PRO_MOBILE"),
        (r'"OK版Pro_电视Pro"', "OK_PRO_TV"),
        (r'"蜜蜂版手机_PY32"', "FM_MOBILE_32"),
        (r'"蜜蜂版手机_JAVA32"', "FM_MOBILE_32"),
        (r'"蜜蜂版电视_PY32"', "FM_TV_32"),
        (r'"蜜蜂版电视_JAVA32"', "FM_TV_32"),
    ]
    for regex, key in updates:
        if key in mapping:
            content = re.sub(rf'({regex}:\s*")([^"]+)(")', rf'\1{mapping[key]}\3', content)

    with open(PY_FILE, 'w', encoding='utf-8', newline='\n') as f: f.write(content)
    print(f"Updated {PY_FILE}")

def update_changelog(version, info):
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    vers = info["vers"]
    # 构造日志内容
    entry = f"## [{version}] - {now_str}\n- 🚀 自动同步最新版本:\n"
    if "OK_VER_MOBILE" in vers: entry += f"  - OK版: {vers['OK_VER_MOBILE']}\n"
    if "FM_VER_MOBILE" in vers: entry += f"  - 蜜蜂版: {vers['FM_VER_MOBILE']}\n"
    
    old = ""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f: old = f.read()
    with open(LOG_FILE, 'w', encoding='utf-8', newline='\n') as f: f.write(entry + "\n" + old)

if __name__ == "__main__":
    ver = get_new_version()
    print(f"::set-output name=new_version::{ver}")
    
    rec_list = fetch_data()
    info = extract_info(rec_list)
    
    # 打印提取到的信息用于调试
    print("Version Info:", json.dumps(info["vers"], indent=2, ensure_ascii=False))

    update_sh_file(info, ver)
    update_py_file(info)
    update_changelog(ver, info)
