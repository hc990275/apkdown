#!/usr/bin/env bash

# --- 脚本配置 ---
SCRIPT_VERSION="v12.01" # 此版本号会被 auto_maintain.py 自动替换
DEBUG="false"
# 默认下载目录
download_dir="/storage/emulated/0/0网站/下载专用/影视安装包更新"
VERSION_DIR="$download_dir/版本文件夹"
user_agent="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36 EdgA/121.0.0.0"
REPO="hc990275/apkdown"

# --- 版本信息 URL (将被自动化脚本替换) ---
declare -A VERSION_URLS=(
    ["OK版手机"]="https://raw.githubusercontent.com/lystv/fmapp/ok/apk/release/mobile.json"
    ["OK版电视"]="https://raw.githubusercontent.com/lystv/fmapp/ok/apk/release/leanback.json"
    ["蜜蜂版手机"]="https://raw.githubusercontent.com/FongMi/Release/fongmi/apk/mobile.json"
    ["蜜蜂版电视"]="https://raw.githubusercontent.com/FongMi/Release/fongmi/apk/leanback.json"
    ["OK版Pro"]="https://raw.githubusercontent.com/lystv/fmapp/ok/apk/pro/v.txt"
)

# --- APK 下载链接映射 (将被自动化脚本替换) ---
declare -A APK_PATHS=(
    ["OK版手机_32"]="lystv/fmapp/ok/apk/release/mobile-armeabi_v7a.apk"
    ["OK版电视_32"]="lystv/fmapp/ok/apk/release/leanback-armeabi_v7a.apk"
    ["OK安卓4版本_APK"]="lystv/fmapp/ok/apk/kitkat/leanback.apk"
    ["OK版Pro_手机Pro"]="lystv/fmapp/ok/apk/pro/mobile-pro.apk"
    ["OK版Pro_电视Pro"]="lystv/fmapp/ok/apk/pro/leanback-pro.apk"
    ["蜜蜂版手机_32"]="FongMi/Release/fongmi/apk/mobile-armeabi_v7a.apk"
    ["蜜蜂版电视_32"]="FongMi/Release/fongmi/apk/leanback-armeabi_v7a.apk"
)

mkdir -p "$VERSION_DIR"

# --- 状态记录变量 ---
declare -A OLD_VERSIONS=()
declare -A NEW_VERSIONS=()
declare -A VERSION_CHANGED=()

# --- 函数定义 ---
random_color() { echo $((31 + RANDOM % 7)); }
print_color() { local color_code=$(random_color); echo -e "\e[${color_code}m\e[1m$1\e[0m"; echo ""; }

check_mt_extension() {
    print_color "🔍 检测运行环境..."
    if [ -n "$TERMUX_VERSION" ] || [ -d "/data/data/com.termux" ] || pm list packages 2>/dev/null | grep -q "bin.mt.termex"; then
        print_color "✅ 环境检测通过"
    else
        print_color "⚠️ 建议在 MT管理器 拓展包中运行以获得最佳体验"
    fi
}

check_and_update_script() {
    print_color "🔍 检查脚本更新..."
    local latest_url="https://api.github.com/repos/$REPO/releases/latest"
    # 设置超时，防止卡住
    local response=$(wget -q --timeout=5 -O- "$latest_url")
    local latest_version=$(echo "$response" | grep -o '"tag_name": *"[^"]*"' | cut -d '"' -f 4)
    
    if [ -n "$latest_version" ] && [ "$latest_version" != "$SCRIPT_VERSION" ]; then
        print_color "⬇️ 发现新版本：$latest_version (当前: $SCRIPT_VERSION)"
        print_color "💡 请前往 GitHub 下载最新脚本，或等待自动更新推送。"
    else
        print_color "✅ 当前已是最新版 ($SCRIPT_VERSION)"
    fi
}

check_json_update() {
    local name="$1"
    local url="${VERSION_URLS[$name]}"
    local old_json="$VERSION_DIR/$name.json"
    local temp_json="$VERSION_DIR/${name}_temp.json"

    wget -q -O "$temp_json" "$url"
    if [ ! -s "$temp_json" ]; then
        print_color "❌ 获取 $name 版本信息失败"
        return 1
    fi

    local old_ver=""
    local new_ver=""

    # 简单提取版本号用于显示
    if [ "$name" == "OK版Pro" ]; then
        [ -f "$old_json" ] && old_ver=$(head -n 1 "$old_json")
        new_ver=$(head -n 1 "$temp_json")
    else
        [ -f "$old_json" ] && old_ver=$(grep '"name"' "$old_json" | cut -d '"' -f 4)
        new_ver=$(grep '"name"' "$temp_json" | cut -d '"' -f 4)
    fi

    OLD_VERSIONS["$name"]="$old_ver"
    NEW_VERSIONS["$name"]="$new_ver"

    if cmp -s "$temp_json" "$old_json"; then
        rm "$temp_json"
        VERSION_CHANGED["$name"]="false"
        print_color "✅ $name 无需更新 ($new_ver)"
        return 1
    else
        mv "$temp_json" "$old_json"
        VERSION_CHANGED["$name"]="true"
        print_color "🔄 $name 发现更新: $old_ver -> $new_ver"
        return 0
    fi
}

download_apk() {
    local key="$1"
    local rel_path="${APK_PATHS[$key]}"
    [ -z "$rel_path" ] && return
    
    local url="https://raw.githubusercontent.com/${rel_path}"
    local filename="${key/_APK/}.apk" # 去掉 _APK 后缀
    local filepath="$download_dir/$filename"
    
    print_color "⬇️ 正在下载: $filename"
    wget -q --show-progress -O "$filepath" "$url"
    
    if [ -s "$filepath" ]; then
        print_color "✅ 下载成功"
    else
        print_color "❌ 下载失败"
    fi
}

print_version_summary() {
    echo ""
    print_color "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_color "📊 版本检测汇总报告"
    print_color "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    for name in "OK版手机" "OK版电视" "OK版Pro" "蜜蜂版手机" "蜜蜂版电视"; do
        local old_ver="${OLD_VERSIONS[$name]}"
        local new_ver="${NEW_VERSIONS[$name]}"
        local changed="${VERSION_CHANGED[$name]}"
        
        if [ "$changed" == "true" ]; then
            print_color "🔄 $name: $old_ver → $new_ver (已更新)"
        else
            print_color "✅ $name: $new_ver (最新)"
        fi
    done
    echo ""
    print_color "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

print_tvbox_interfaces() {
    print_color "📢 欢迎关注公众号："
    print_color "👉  阿博可行笔记  |  阿博AI"
    echo ""
}

# --- 主流程 ---
check_mt_extension
print_color "🌟 脚本版本: $SCRIPT_VERSION"
check_and_update_script

mkdir -p "$download_dir"

for name in "OK版Pro" "OK版手机" "OK版电视" "蜜蜂版手机" "蜜蜂版电视"; do
    if check_json_update "$name"; then
        case "$name" in
            "OK版Pro")
                download_apk "OK版Pro_手机Pro"
                download_apk "OK版Pro_电视Pro"
                ;;
            "OK版手机")
                download_apk "OK版手机_32"
                ;;
            "OK版电视")
                download_apk "OK版电视_32"
                ;;
            "蜜蜂版手机")
                download_apk "蜜蜂版手机_32"
                ;;
            "蜜蜂版电视")
                download_apk "蜜蜂版电视_32"
                ;;
        esac
    fi
done

print_tvbox_interfaces
print_version_summary

print_color "🎉 所有任务完成！"
