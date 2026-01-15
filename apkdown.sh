#!/bin/sh

# =======================================================
# Fongmi 推荐源更新 - 最终修正版
# 特性：仅下载推荐组 + 严格区分作者/设备 + 极简显示
# =======================================================

# --- 1. 配置区 ---
ACCEL_PREFIX="https://js.2017.de5.net/"
URL_JSON="https://raw.githubusercontent.com/lystv/fmapp/app/yysd-zl.json"
TARGET_JSON_URL="${ACCEL_PREFIX}${URL_JSON}"

# --- 2. 目录初始化 ---
BASE_DIR=$(dirname "$0")
REPO_DIR="$BASE_DIR/版本库"
APP_DIR="$BASE_DIR/APP库"
TEMP_JSON="$BASE_DIR/temp.json"
TEMP_LIST="$BASE_DIR/list.txt"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 创建必要目录
[ ! -d "$REPO_DIR" ] && mkdir -p "$REPO_DIR"
[ ! -d "$APP_DIR" ] && mkdir -p "$APP_DIR"

# 清屏并显示标题
clear
echo -e "${BLUE}==================================${NC}"
echo -e "${BLUE}   影视APP 推荐组 自动更新工具   ${NC}"
echo -e "${BLUE}==================================${NC}"
echo ""

# --- 3. 获取配置 ---
echo -e "正在获取最新配置..."
# -s 静默模式，不显示下载进度
curl -k -s -L "$TARGET_JSON_URL" -o "$TEMP_JSON"

if [ ! -s "$TEMP_JSON" ]; then
    echo -e "${YELLOW}错误：配置文件下载失败，请检查网络。${NC}"
    exit 1
fi

# --- 4. 解析数据 (核心逻辑) ---
# 使用 sed 将 JSON 格式化为流，逐行提取
# 仅提取 "name": "推薦" 所在列表的内容
: > "$TEMP_LIST"

cat "$TEMP_JSON" | sed 's/[{}[],]/\n/g' | sed 's/^[ \t]*//g' | sed 's/"//g' | while read -r line; do
    [ -z "$line" ] && continue
    
    # 提取 Key 和 Value
    key=$(echo "$line" | cut -d':' -f1)
    val=$(echo "$line" | cut -d':' -f2- | sed 's/^[ \t]*//')

    case "$key" in
        "name") 
            # 暂存名字，可能是组名也可能是APP名
            temp_name="$val" 
            ;;
        "list") 
            # 遇到 list，说明刚才的 name 是组名
            current_group="$temp_name" 
            ;;
        "url") 
            current_url="$val" 
            # 遇到 url，说明刚才的 temp_name 是 APP 名
            current_app_name="$temp_name"
            ;;
        "version")
            current_ver="$val"
            # === 过滤核心：只处理 "推薦" 分组 ===
            # 注意：繁体 "推薦"
            if [ "$current_group" = "推薦" ] && [ -n "$current_url" ]; then
                echo "${current_group}|${current_app_name}|${current_ver}|${current_url}" >> "$TEMP_LIST"
            fi
            ;;
    esac
done

# --- 5. 循环检测与下载 ---
count_total=0
count_update=0

# 读取解析好的列表
while IFS='|' read -r group name ver url; do
    count_total=$((count_total+1))

    # === A. 解析作者与版本号 ===
    # 默认作者未知
    author="其他"
    clean_ver="$ver"
    
    # 逻辑：如果版本号包含 "-" (如 OK-3.6.0)，则横杠前是作者
    if echo "$ver" | grep -q "-"; then
        author=$(echo "$ver" | cut -d'-' -f1)      # 提取 OK
        clean_ver=$(echo "$ver" | cut -d'-' -f2-)  # 提取 3.6.0
    fi

    # === B. 生成本地记录 ID ===
    # 清洗非法字符
    safe_name=$(echo "$name" | tr -d '/\\:*?"<>|')
    
    # 唯一ID：[推荐]手机-32_OK.txt
    # 这样就能把 OK版 和 FM版 彻底分开
    uid="${group}_${safe_name}_${author}"
    ver_record_file="$REPO_DIR/${uid}.txt"
    
    # === C. 读取本地旧版本 ===
    local_ver="无"
    if [ -f "$ver_record_file" ]; then
        local_ver=$(cat "$ver_record_file")
    fi
    
    # === D. 版本对比 ===
    if [ "$local_ver" != "$ver" ]; then
        count_update=$((count_update+1))
        
        # === E. 构造加速下载链接 ===
        download_url="$url"
        # 如果不是加速链接且是 github，则添加前缀
        case "$url" in
            *"raw.githubusercontent.com"*|*"github.com"*)
                if echo "$url" | grep -v -q "js.2017.de5.net"; then
                    download_url="${ACCEL_PREFIX}${url}"
                fi
                ;;
        esac
        
        # === F. 构造文件名 ===
        # 格式: [OK]手机-32_3.6.0.apk
        # 这样作者、设备、版本都一清二楚
        apk_filename="[${author}]${safe_name}_${clean_ver}.apk"
        save_path="$APP_DIR/$apk_filename"
        
        # === G. 界面交互 ===
        echo -e "----------------------------------"
        echo -e "发现更新：${GREEN}${name}${NC}"
        echo -e "  作者：${author}"
        echo -e "  版本：${local_ver} -> ${clean_ver}"
        echo -e "正在下载：${YELLOW}${apk_filename}${NC}"
        echo -e "请等待..."
        
        # 下载文件 (-# 显示进度条)
        curl -k -L -# "$download_url" -o "$save_path"
        
        if [ $? -eq 0 ]; then
            # 下载成功，写入新版本号到记录文件
            echo "$ver" > "$ver_record_file"
            echo -e "${GREEN}√ 下载完成${NC}"
        else
            echo -e "${RED}× 下载失败${NC}"
        fi
    fi
    
done < "$TEMP_LIST"

# --- 6. 结束清理 ---
rm -f "$TEMP_JSON" "$TEMP_LIST"

echo ""
echo -e "${BLUE}==================================${NC}"
if [ "$count_update" -eq 0 ]; then
    echo -e "${GREEN}所有应用均为最新，无需更新。${NC}"
else
    echo -e "本次共更新 ${GREEN}${count_update}${NC} 个应用"
    echo -e "文件已保存在：${YELLOW}APP库/${NC}"
fi
echo -e "${BLUE}==================================${NC}"
