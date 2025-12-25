#!/usr/bin/env bash

# --- 脚本配置 ---
SCRIPT_VERSION="v2025.12.25_0526" # 自动替换
download_dir="/storage/emulated/0/0网站/下载专用/影视安装包更新"

# --- 应用版本号 (将被自动化脚本替换) ---
OK_VER_MOBILE="OK-3.5.7"
OK_VER_TV="OK-3.5.7"
OK_VER_PRO="OK-3.8.8-pro"
OK_VER_4X="OK-2.5.0"
FM_VER_MOBILE="FM-5.0.4"
FM_VER_TV="FM-5.0.4"

# --- APK 下载链接 (将被自动化脚本替换) ---
declare -A APK_PATHS=(
    ["OK版手机_32"]="lystv/fmapp/54dbf376f4fca72e12061e13fb689db87f99235b/apk/release/mobile-armeabi_v7a.apk"
    ["OK版电视_32"]="lystv/fmapp/54dbf376f4fca72e12061e13fb689db87f99235b/apk/release/leanback-armeabi_v7a.apk"
    ["OK安卓4版本_APK"]="lystv/fmapp/93fd99c68e7bddc4b903a2fe12fdbd372630610b/apk/kitkat/leanback.apk"
    ["OK版Pro_手机Pro"]="lystv/fmapp/08b161ad2417393aca9141ad63956c917e5fbd65/apk/pro/mobile-pro.apk"
    ["OK版Pro_电视Pro"]="lystv/fmapp/08b161ad2417393aca9141ad63956c917e5fbd65/apk/pro/leanback-pro.apk"
    ["蜜蜂版手机_32"]="fongmi/release/38ecab09fba63ecf10ef5eb92951b9554bb9f803/apk/mobile-armeabi_v7a.apk"
    ["蜜蜂版电视_32"]="fongmi/release/38ecab09fba63ecf10ef5eb92951b9554bb9f803/apk/leanback-armeabi_v7a.apk"
)

# --- 辅助函数 ---
random_color() { echo $((31 + RANDOM % 7)); }
print_color() { local color_code=$(random_color); echo -e "\e[${color_code}m\e[1m$1\e[0m"; echo ""; }

check_mt_extension() {
    print_color "🔍 检测运行环境..."
    if [ -n "$TERMUX_VERSION" ] || [ -d "/data/data/com.termux" ] || pm list packages 2>/dev/null | grep -q "bin.mt.termex"; then
        print_color "✅ 环境检测通过"
    else
        print_color "⚠️ 建议在 MT管理器 拓展包中运行"
    fi
}

download_apk() {
    local key="$1"
    local desc="$2"
    local rel_path="${APK_PATHS[$key]}"
    
    if [ -z "$rel_path" ]; then
        print_color "❌ 配置缺失: $key"
        return
    fi
    
    local url="https://raw.githubusercontent.com/${rel_path}"
    local filename="${key/_APK/}.apk"
    local filepath="$download_dir/$filename"
    
    print_color "⬇️ 正在下载: $desc ($filename)"
    # 已删除打印源链接的代码
    
    wget -q --show-progress -O "$filepath" "$url"
    
    if [ -s "$filepath" ]; then
        print_color "✅ 下载成功"
    else
        print_color "❌ 下载失败"
    fi
}

print_summary() {
    echo ""
    print_color "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_color "📊 内置版本信息 (自动同步)"
    print_color "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_color "🔹 OK版手机: $OK_VER_MOBILE"
    print_color "🔹 OK版电视: $OK_VER_TV"
    print_color "🔹 OK版Pro : $OK_VER_PRO"
    print_color "🔸 蜜蜂手机: $FM_VER_MOBILE"
    print_color "🔸 蜜蜂电视: $FM_VER_TV"
    print_color "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_color "📢 欢迎关注公众号：阿博可行笔记 | 阿博AI"
    echo ""
}

# --- 主流程 ---
check_mt_extension
print_color "🌟 脚本版本: $SCRIPT_VERSION"
print_summary

print_color "🚀 开始批量下载..."
mkdir -p "$download_dir"

download_apk "OK版手机_32" "OK手机版 (32位)"
download_apk "OK版电视_32" "OK电视版 (32位)"
download_apk "OK版Pro_手机Pro" "OKPro 手机版"
download_apk "OK版Pro_电视Pro" "OKPro 电视版"
download_apk "蜜蜂版手机_32" "蜜蜂手机版 (32位)"
download_apk "蜜蜂版电视_32" "蜜蜂电视版 (32位)"

print_color "🎉 所有任务执行完毕！"
