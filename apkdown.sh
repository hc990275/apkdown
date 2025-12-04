#!/bin/bash

# --- 脚本配置 ---
SCRIPT_VERSION="v12.01"
DEBUG="false"
VERSION_DIR="/storage/emulated/0/0网站/下载专用/影视安装包更新/版本文件夹"
user_agent="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36 EdgA/121.0.0.0"
REPO="hc990275/apkdown"

declare -A TVBOX_INTERFACES=()

# --- 版本信息 URL ---
declare -A VERSION_URLS=(
    ["OK版手机"]="https://raw.githubusercontent.com/lystv/fmapp/ok/apk/release/mobile.json"
    ["OK版电视"]="https://raw.githubusercontent.com/lystv/fmapp/ok/apk/release/leanback.json"
    ["蜜蜂版手机"]="https://raw.githubusercontent.com/FongMi/Release/fongmi/apk/mobile.json"
    ["蜜蜂版电视"]="https://raw.githubusercontent.com/FongMi/Release/fongmi/apk/leanback.json"
    ["OK版Pro"]="https://raw.githubusercontent.com/lystv/fmapp/ok/apk/pro/v.txt"
)

# --- APK 下载链接映射 ---
declare -A APK_PATHS=(
    ["OK版手机_32"]="lystv/fmapp/ok/apk/release/mobile-armeabi_v7a.apk"
    ["OK版手机_64"]="lystv/fmapp/ok/apk/release/mobile-arm64_v8a.apk"
    ["OK版电视_32"]="lystv/fmapp/ok/apk/release/leanback-armeabi_v7a.apk"
    ["OK版电视_64"]="lystv/fmapp/ok/apk/release/leanback-arm64_v8a.apk"
    ["OK海信专版_APK"]="lystv/fmapp/ok/apk/release/%E6%B5%B7%E4%BF%A1%E4%B8%93%E7%89%88.apk"
    ["OK安卓4版本_APK"]="lystv/fmapp/ok/apk/kitkat/leanback.apk"
    ["OK版Pro_手机Pro"]="lystv/fmapp/ok/apk/pro/mobile-pro.apk"
    ["OK版Pro_手机emu-Pro"]="lystv/fmapp/ok/apk/pro/mobile-emu-pro.apk"
    ["OK版Pro_电视Pro"]="lystv/fmapp/ok/apk/pro/leanback-pro.apk"
    ["蜜蜂版手机_32"]="FongMi/Release/fongmi/apk/mobile-armeabi_v7a.apk"
    ["蜜蜂版手机_64"]="FongMi/Release/fongmi/apk/mobile-arm64_v8a.apk"
    ["蜜蜂版电视_32"]="FongMi/Release/fongmi/apk/leanback-armeabi_v7a.apk"
    ["蜜蜂版电视_64"]="FongMi/Release/fongmi/apk/leanback-arm64_v8a.apk"
)

download_dir="/storage/emulated/0/0网站/下载专用/影视安装包更新"
version_folder="$download_dir/版本文件夹"
mkdir -p "$version_folder"

# --- 版本信息存储 ---
declare -A OLD_VERSIONS=()
declare -A NEW_VERSIONS=()
declare -A VERSION_CHANGED=()

# --- 函数定义 ---
random_color() { echo $((31 + RANDOM % 7)); }
print_color() { local color_code=$(random_color); echo -e "\e[${color_code}m\e[1m$1\e[0m"; echo ""; }

check_mt_extension() {
    print_color "🔍 正在检测 MT 管理器拓展包..."
    if pm list packages | grep -q "bin.mt.termex"; then
        print_color "✅ MT 管理器拓展包已安装"
    else
        print_color "❌ 未检测到 MT 管理器拓展包"
        print_color "⚠️ 请先安装 MT 管理器拓展包以确保脚本正常运行"
    fi
    print_color "请使用拓展包环境运行，不要使用系统环境运行。"
    echo ""
}

print_script_version() {
    print_color "🌟 当前脚本版本: $SCRIPT_VERSION"
}

check_and_update_script() {
    print_color "🔍 正在检查脚本更新..."
    local response_file
    response_file=$(mktemp)
    wget -q -O "$response_file" "https://api.github.com/repos/$REPO/releases/latest"
    local response
    response=$(cat "$response_file")
    rm -f "$response_file"

    local latest_version
    latest_version=$(echo "$response" | grep -o '"tag_name": *"[^"]*"' | cut -d '"' -f 4)
    local download_url
    download_url=$(echo "$response" | grep -o '"browser_download_url": *"[^"]*\.sh"' | cut -d '"' -f 4)

    if [ -z "$latest_version" ] || [ -z "$download_url" ]; then
        print_color "❌ 无法获取最新版本信息，跳过更新。"
        return 1
    fi

    if [ "$latest_version" != "$SCRIPT_VERSION" ]; then
        print_color "⬇️ 发现新版本：$SCRIPT_VERSION -> $latest_version，正在更新..."
        local new_script_name="软件更新脚本_$latest_version.sh"
        local old_script_name="$0"
        wget -q -O "$new_script_name" "$download_url"
        if [ -f "$new_script_name" ]; then
            chmod +x "$new_script_name"
            print_color "✅ 更新完成，新的脚本已下载为: $new_script_name"
            rm -f "$old_script_name"
            print_color "🧹 旧脚本已删除: $old_script_name"
            print_color "🔁 请运行新脚本并退出当前脚本。"
            exit 0
        else
            print_color "❌ 脚本下载失败，保持当前版本。"
            return 1
        fi
    else
        print_color "✅ 脚本已是最新版本（$SCRIPT_VERSION）"
        return 0
    fi
}

check_json_update() {
    local name="$1"
    local url="${VERSION_URLS[$name]}"
    local old_json_file="$version_folder/$name.json"
    local temp_json_file="$version_folder/${name}临时.json"

    wget -q -O "$temp_json_file" "$url"

    if [ ! -f "$temp_json_file" ] || [ ! -s "$temp_json_file" ]; then
        print_color "❌ 下载失败: $name JSON 文件"
        return 1
    fi

    local old_version=""
    local new_version=""

    if [ "$name" == "OK版Pro" ]; then
        [ -f "$old_json_file" ] && old_version=$(head -n 1 "$old_json_file" | tr -d '\r')
        new_version=$(head -n 1 "$temp_json_file" | tr -d '\r')
    else
        [ -f "$old_json_file" ] && old_version=$(grep '"name"' "$old_json_file" | cut -d '"' -f 4)
        new_version=$(grep '"name"' "$temp_json_file" | cut -d '"' -f 4)
    fi

    OLD_VERSIONS["$name"]="$old_version"
    NEW_VERSIONS["$name"]="$new_version"

    print_color "$name 旧版本号: $old_version (文件时间: $(stat --format='%y' "$old_json_file" 2>/dev/null | cut -d '.' -f 1))"
    print_color "$name 新版本号: $new_version (文件时间: $(stat --format='%y' "$temp_json_file" | cut -d '.' -f 1))"

    if [ "$new_version" != "$old_version" ]; then
        print_color "🔄 发现新版本，更新 JSON 并准备下载 APK..."
        VERSION_CHANGED["$name"]="true"
        mv -f "$temp_json_file" "$old_json_file"
        return 0
    else
        print_color "✅ 版本未变更，无需更新。"
        VERSION_CHANGED["$name"]="false"
        rm -f "$temp_json_file"
        return 1
    fi
}

download_apk() {
    local apk_name="$1"
    local apk_github_path="${APK_PATHS[$apk_name]}"
    local apk_path="$download_dir/$apk_name.apk"
    local temp_apk_path="$download_dir/${apk_name}临时.apk"

    local apk_url="https://raw.githubusercontent.com/${apk_github_path}"

    print_color "⬇️ 正在下载: $apk_name.apk"
    print_color "    下载链接: $apk_url"

    wget -q --show-progress -O "$temp_apk_path" "$apk_url"

    if [ -f "$temp_apk_path" ] && [ -s "$temp_apk_path" ]; then
        print_color "✅ 下载完成: $apk_name.apk"
        mv -f "$temp_apk_path" "$apk_path"
    else
        print_color "❌ 下载失败: $apk_name.apk"
        rm -f "$temp_apk_path"
    fi
}

print_tvbox_interfaces() {
    print_color "📢 欢迎关注我的公众号："
    print_color "👉  阿博可行笔记  |  阿博AI"
    print_color "获取更多实用工具和技术分享！"
    echo ""
}

print_version_summary() {
    echo ""
    print_color "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_color "📊 版本检测汇总报告"
    print_color "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    declare -A DISPLAY_NAMES=(
        ["OK版手机"]="OK手机版"
        ["OK版电视"]="OK电视版"
        ["OK版Pro"]="OKPro版"
        ["蜜蜂版手机"]="蜜蜂手机版"
        ["蜜蜂版电视"]="蜜蜂电视版"
    )
    
    local order=("OK版手机" "OK版电视" "OK版Pro" "蜜蜂版手机" "蜜蜂版电视")
    
    for name in "${order[@]}"; do
        local display_name="${DISPLAY_NAMES[$name]}"
        local old_ver="${OLD_VERSIONS[$name]}"
        local new_ver="${NEW_VERSIONS[$name]}"
        local changed="${VERSION_CHANGED[$name]}"
        
        if [ "$changed" == "true" ]; then
            print_color "🔄 $display_name: $old_ver → $new_ver"
        else
            if [ -n "$new_ver" ]; then
                print_color "✅ $display_name: $new_ver"
            else
                print_color "❓ $display_name: 未检测到版本信息"
            fi
        fi
    done
    
    echo ""
    print_color "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# --- 主流程 ---
check_mt_extension
print_script_version
check_and_update_script

for name in "${!VERSION_URLS[@]}"; do
    if check_json_update "$name"; then
        print_color "✅ $name 检测到有更新，准备下载 APK..."
        case "$name" in
            "OK版Pro")
                download_apk "OK版Pro_手机Pro"
                download_apk "OK版Pro_手机emu-Pro"
                download_apk "OK版Pro_电视Pro"
                ;;
            "OK版电视")
                download_apk "OK版电视_32"
                download_apk "OK版电视_64"
                download_apk "OK海信专版_APK"
                download_apk "OK安卓4版本_APK"
                ;;
            *)
                download_apk "${name}_32"
                download_apk "${name}_64"
                ;;
        esac
    fi
done

print_tvbox_interfaces
print_version_summary

print_color "🎉 脚本全部操作完成！"