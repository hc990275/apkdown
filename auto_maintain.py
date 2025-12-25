import requests
import json
import re
import datetime
import os

# --- 配置区域 ---
SOURCE_JSON = "https://raw.githubusercontent.com/lystv/fmapp/app/yysd-zl.json"
SH_FILE = "apkdown.sh"
PY_FILE = "PY版本.PY"
LOG_FILE = "CHANGELOG.md"

def get_new_version():
    """生成带时间戳的版本号，确保每次运行强制变更"""
    return datetime.datetime.now().strftime("v%Y.%m.%d_%H%M")

def fetch_data():
    """获取源 JSON 数据"""
    print(f"Downloading {SOURCE_JSON}...")
    try:
        resp = requests.get(SOURCE_JSON, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        # 提取“推薦”列表
        for category in data:
            if category.get("name") == "推薦":
                print("Found '推薦' list.")
                return category.get("list", [])
        return []
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

def extract_paths(rec_list):
    """
    仅提取推荐列表中的7个关键路径 (去掉了 64位 和 emu-pro)
    """
    mapping = {}
    
    # 辅助：获取相对路径 (去掉 https://raw.githubusercontent.com/)
    def get_rel_path(url):
        return url.replace("https://raw.githubusercontent.com/", "")

    for item in rec_list:
        name = item.get("name", "")
        url = item.get("url", "")
        version = item.get("version", "")
        
        if not url: continue
        
        path = get_rel_path(url)

        # --- OK 版匹配逻辑 ---
        if "OK" in version:
            # OK 手机 32位
            if "手機-32" in name:
                mapping["OK_MOBILE_32"] = path
            # OK 电视 32位
            elif "電視-32" in name:
                mapping["OK_TV_32"] = path
            # OK 4.x (KitKat)
            elif "4.x" in name:
                mapping["OK_KITKAT"] = path
            # OK Pro 手机 (排除 emu)
            elif "手機pro" in name.lower() and "emu" not in name.lower():
                mapping["OK_PRO_MOBILE"] = path
            # OK Pro 电视
            elif "電視pro" in name.lower():
                mapping["OK_PRO_TV"] = path

        # --- 蜜蜂版 (FM) 匹配逻辑 ---
        elif "FM" in version:
            # 蜜蜂 手机 32位
            if "手機-32" in name:
                mapping["FM_MOBILE_32"] = path
            # 蜜蜂 电视 32位
            elif "電視-32" in name:
                mapping["FM_TV_32"] = path
            
    return mapping

def update_sh_file(mapping, new_version):
    """更新 Shell 脚本"""
    if not os.path.exists(SH_FILE):
        return False

    with open(SH_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. 强制更新版本号
    content = re.sub(r'SCRIPT_VERSION="v[^"]+"', f'SCRIPT_VERSION="{new_version}"', content)
    
    # 2. 精准更新链接 (只更新映射中存在的)
    # 格式: (Shell中的Key正则, Mapping中的Key)
    updates = [
        # OK版
        (r'\["OK版手机_32"\]', "OK_MOBILE_32"),
        (r'\["OK版电视_32"\]', "OK_TV_32"),
        (r'\["OK安卓4版本_APK"\]', "OK_KITKAT"),
        (r'\["OK版Pro_手机Pro"\]', "OK_PRO_MOBILE"),
        (r'\["OK版Pro_电视Pro"\]', "OK_PRO_TV"),
        # 蜜蜂版 (只更32位)
        (r'\["蜜蜂版手机_32"\]', "FM_MOBILE_32"),
        (r'\["蜜蜂版电视_32"\]', "FM_TV_32"),
    ]

    for regex_start, map_key in updates:
        if map_key in mapping:
            new_path = mapping[map_key]
            # 替换 ["KEY"]="VALUE" 中的 VALUE
            pattern = rf'({regex_start}=")([^"]+)(")'
            content = re.sub(pattern, rf'\1{new_path}\3', content)

    # 写入文件 (强制 LF 换行符)
    with open(SH_FILE, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"Updated {SH_FILE} to version {new_version}")
    return True

def update_py_file(mapping):
    """更新 Python 脚本"""
    if not os.path.exists(PY_FILE):
        return False

    with open(PY_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
        
    updates = [
        # OK版
        (r'"OK版手机_32"', "OK_MOBILE_32"),
        (r'"OK版电视_32"', "OK_TV_32"),
        (r'"OK安卓4版本_APK"', "OK_KITKAT"),
        (r'"OK版Pro_手机Pro"', "OK_PRO_MOBILE"),
        (r'"OK版Pro_电视Pro"', "OK_PRO_TV"),
        
        # 蜜蜂版
        # 无论 PY版本 里的 Key 叫什么 (PY32 还是 JAVA32)，都指向推荐列表里的 FM 32位链接
        (r'"蜜蜂版手机_PY32"', "FM_MOBILE_32"),
        (r'"蜜蜂版手机_JAVA32"', "FM_MOBILE_32"), # 如果有Java键值也一并更新
        (r'"蜜蜂版电视_PY32"', "FM_TV_32"),
        (r'"蜜蜂版电视_JAVA32"', "FM_TV_32"),
    ]

    for regex_key, map_key in updates:
        if map_key in mapping:
            new_path = mapping[map_key]
            # 替换 "KEY": "VALUE" 中的 VALUE
            pattern = rf'({regex_key}:\s*")([^"]+)(")'
            content = re.sub(pattern, rf'\1{new_path}\3', content)

    with open(PY_FILE, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"Updated {PY_FILE}")
    return True

def update_changelog(version):
    """倒叙写入日志"""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = f"""## [{version}] - {now_str}
- 🚀 自动同步 "推薦" 列表
- 📦 已更新 OK版(32位/Pro/4.x) 和 蜜蜂版(32位)
- ✂️ 移除了 64位 和 emu-pro 的更新逻辑

"""
    old_content = ""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            old_content = f.read()
            
    with open(LOG_FILE, 'w', encoding='utf-8', newline='\n') as f:
        f.write(new_entry + old_content)
    print(f"Log appended to start of {LOG_FILE}")

if __name__ == "__main__":
    try:
        new_ver = get_new_version()
        print(f"::set-output name=new_version::{new_ver}")
        
        rec_list = fetch_data()
        if not rec_list:
            print("Fetching data failed or empty.")
            # 即使没数据，因为要强制运行(改版本号)，我们继续，但不更新链接
            # mapping 将为空
        
        mapping = extract_paths(rec_list)
        
        # 打印一下抓到的路径，方便调试
        print("Extracted Mapping:", json.dumps(mapping, indent=2, ensure_ascii=False))

        # 执行更新
        update_sh_file(mapping, new_ver)
        update_py_file(mapping)
        update_changelog(new_ver)

    except Exception as e:
        print(f"Error: {e}")
        exit(1)
