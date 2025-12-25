import requests
import json
import re
import datetime
import os

# --- 配置区域 ---
SOURCE_JSON = "https://raw.githubusercontent.com/lystv/fmapp/app/yysd-zl.json"
SH_FILE = "apkdown.sh"
PY_FILE = "PY版本.PY"

def get_new_version():
    """生成基于日期的版本号，例如 v2024.12.25"""
    return datetime.datetime.now().strftime("v%Y.%m.%d")

def fetch_data():
    """获取源 JSON 数据"""
    print(f"Downloading {SOURCE_JSON}...")
    resp = requests.get(SOURCE_JSON)
    resp.raise_for_status()
    data = resp.json()
    
    # 提取“推薦”列表
    for category in data:
        if category.get("name") == "推薦":
            return category.get("list", [])
    return []

def extract_base_paths(rec_list):
    """
    从推荐列表中提取基础路径 (Commit Hash 路径)。
    策略：找到一个文件，提取其目录，然后用于推导同类文件。
    """
    mapping = {}
    
    # 辅助：移除 https://raw.githubusercontent.com/ 和 文件名
    def get_base(url):
        clean = url.replace("https://raw.githubusercontent.com/", "")
        return clean.rsplit('/', 1)[0] + "/"
    
    # 辅助：获取完整URL (用于 OK 4.x 这种单独文件)
    def get_full_content(url):
         return url.replace("https://raw.githubusercontent.com/", "")

    for item in rec_list:
        name = item.get("name", "")
        url = item.get("url", "")
        version = item.get("version", "")
        
        if not url: continue

        # 1. OK 手机/电视/海信 (通常共享同一个 Release 目录)
        if "手機" in name and "OK" in version and "pro" not in name.lower():
            mapping["OK_RELEASE_BASE"] = get_base(url)
        
        # 2. OK Pro (手机/电视 Pro 共享)
        if "pro" in name.lower() and "OK" in version:
            mapping["OK_PRO_BASE"] = get_base(url)
            
        # 3. OK 4.x (单独文件)
        if "4.x" in name:
            mapping["OK_4X_FILE"] = get_full_content(url)
            
        # 4. 蜜蜂版 (手机/电视 共享)
        if "FM" in version:
            mapping["FM_RELEASE_BASE"] = get_base(url)
            
    return mapping

def update_sh_file(mapping, new_version):
    """更新 Shell 脚本"""
    with open(SH_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. 更新版本号
    # 匹配 SCRIPT_VERSION="v..."
    content = re.sub(r'SCRIPT_VERSION="v[^"]+"', f'SCRIPT_VERSION="{new_version}"', content)
    
    # 2. 更新链接 (利用正则替换 map 中的值)
    # 映射关系：(Shell变量正则特征, Mapping Key, 文件名后缀)
    updates = [
        # OK Release (手机/电视/海信)
        (r'\["OK版手机_32"\]', "OK_RELEASE_BASE", "mobile-armeabi_v7a.apk"),
        (r'\["OK版手机_64"\]', "OK_RELEASE_BASE", "mobile-arm64_v8a.apk"),
        (r'\["OK版电视_32"\]', "OK_RELEASE_BASE", "leanback-armeabi_v7a.apk"),
        (r'\["OK版电视_64"\]', "OK_RELEASE_BASE", "leanback-arm64_v8a.apk"),
        (r'\["OK海信专版_APK"\]', "OK_RELEASE_BASE", "%E6%B5%B7%E4%BF%A1%E4%B8%93%E7%89%88.apk"),
        
        # OK Pro
        (r'\["OK版Pro_手机Pro"\]', "OK_PRO_BASE", "mobile-pro.apk"),
        (r'\["OK版Pro_手机emu-Pro"\]', "OK_PRO_BASE", "mobile-emu-pro.apk"),
        (r'\["OK版Pro_电视Pro"\]', "OK_PRO_BASE", "leanback-pro.apk"),
        
        # OK 4.x
        (r'\["OK安卓4版本_APK"\]', "OK_4X_FILE", ""), # 直接替换完整路径
        
        # 蜜蜂版
        (r'\["蜜蜂版手机_32"\]', "FM_RELEASE_BASE", "mobile-armeabi_v7a.apk"),
        (r'\["蜜蜂版手机_64"\]', "FM_RELEASE_BASE", "mobile-arm64_v8a.apk"),
        (r'\["蜜蜂版电视_32"\]', "FM_RELEASE_BASE", "leanback-armeabi_v7a.apk"),
        (r'\["蜜蜂版电视_64"\]', "FM_RELEASE_BASE", "leanback-arm64_v8a.apk"),
    ]

    for regex_start, map_key, suffix in updates:
        if map_key in mapping:
            new_path = mapping[map_key] + suffix
            # 正则：找到 ["KEY"]="OLD_VALUE" 替换为 ["KEY"]="NEW_VALUE"
            pattern = rf'({regex_start}=")([^"]+)(")'
            content = re.sub(pattern, rf'\1{new_path}\3', content)

    with open(SH_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated {SH_FILE} to version {new_version}")

def update_py_file(mapping):
    """更新 Python 脚本 (仅更新链接，不涉及版本号变量)"""
    with open(PY_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
        
    updates = [
        # OK Release
        (r'"OK版手机_32"', "OK_RELEASE_BASE", "mobile-armeabi_v7a.apk"),
        (r'"OK版手机_64"', "OK_RELEASE_BASE", "mobile-arm64_v8a.apk"),
        (r'"OK版电视_32"', "OK_RELEASE_BASE", "leanback-armeabi_v7a.apk"),
        (r'"OK版电视_64"', "OK_RELEASE_BASE", "leanback-arm64_v8a.apk"),
        (r'"OK海信专版_APK"', "OK_RELEASE_BASE", "%E6%B5%B7%E4%BF%A1%E4%B8%93%E7%89%88.apk"),
        
        # OK 4.x
        (r'"OK安卓4版本_APK"', "OK_4X_FILE", ""),
        
        # OK Pro
        (r'"OK版Pro_手机Pro"', "OK_PRO_BASE", "mobile-pro.apk"),
        (r'"OK版Pro_手机emu-Pro"', "OK_PRO_BASE", "mobile-emu-pro.apk"),
        (r'"OK版Pro_电视Pro"', "OK_PRO_BASE", "leanback-pro.apk"),
        
        # 蜜蜂版 (PY版本里 key 包含 PY/JAVA，统一指向 Release Base)
        (r'"蜜蜂版手机_PY32"', "FM_RELEASE_BASE", "mobile-armeabi_v7a.apk"),
        (r'"蜜蜂版手机_PY64"', "FM_RELEASE_BASE", "mobile-arm64_v8a.apk"),
        (r'"蜜蜂版手机_JAVA32"', "FM_RELEASE_BASE", "mobile-armeabi_v7a.apk"),
        (r'"蜜蜂版手机_JAVA64"', "FM_RELEASE_BASE", "mobile-arm64_v8a.apk"),
        (r'"蜜蜂版电视_PY32"', "FM_RELEASE_BASE", "leanback-armeabi_v7a.apk"),
        (r'"蜜蜂版电视_PY64"', "FM_RELEASE_BASE", "leanback-arm64_v8a.apk"),
        (r'"蜜蜂版电视_JAVA32"', "FM_RELEASE_BASE", "leanback-armeabi_v7a.apk"),
        (r'"蜜蜂版电视_JAVA64"', "FM_RELEASE_BASE", "leanback-arm64_v8a.apk"),
    ]

    for regex_key, map_key, suffix in updates:
        if map_key in mapping:
            new_path = mapping[map_key] + suffix
            # 正则: "KEY": "OLD_VALUE"
            pattern = rf'({regex_key}:\s*")([^"]+)(")'
            content = re.sub(pattern, rf'\1{new_path}\3', content)

    with open(PY_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated {PY_FILE}")

if __name__ == "__main__":
    try:
        new_ver = get_new_version()
        # 输出版本号供 GitHub Actions 读取
        print(f"::set-output name=new_version::{new_ver}")
        
        rec_list = fetch_data()
        mapping = extract_base_paths(rec_list)
        
        update_sh_file(mapping, new_ver)
        update_py_file(mapping)
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
