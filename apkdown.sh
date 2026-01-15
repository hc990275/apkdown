#!/bin/sh

# =======================================================
# Fongmi 影视更新检测 - 安卓 Shell 版
# 运行环境：MT管理器 / Termux
# 功能：自动对比版本，下载更新 APK 到本地
# =======================================================

# --- 配置区 ---
# 远程源地址
URL_JSON="https://raw.githubusercontent.com/lystv/fmapp/app/yysd-zl.json"
# 隐私加速前缀 (用于下载 GitHub 资源)
ACCEL_PREFIX="https://js.2017.de5.net/"

# --- 目录设置 ---
# 获取脚本当前所在目录
BASE_DIR=$(dirname "$0")
# 版本记录文件夹
REPO_DIR="$BASE_DIR/版本库"
# APK下载文件夹
APP_DIR="$BASE_DIR/APP库"
# 临时文件
TEMP_JSON="$BASE_DIR/temp_data.json"
TEMP_PARSED="$BASE_DIR/temp_parsed.txt"

# --- 颜色定义 ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- 初始化 ---
echo -e "${BLUE}=== 影视更新检测工具 Shell版 ===${NC}"
echo -e "${BLUE}正在初始化目录...${NC}"

if [ ! -d "$REPO_DIR" ]; then
    mkdir -p "$REPO_DIR"
    echo -e "创建目录: $REPO_DIR"
fi

if [ ! -d "$APP_DIR" ]; then
    mkdir -p "$APP_DIR"
    echo -e "创建目录: $APP_DIR"
fi

# --- 步骤1: 下载配置 ---
echo -e "${YELLOW}正在获取远程配置...${NC}"
# 使用 curl 下载，-k 跳过 SSL 检查(防止老旧安卓报错)，-s 静默模式
curl -k -s -L "$URL_JSON" -o "$TEMP_JSON"

if [ ! -s "$TEMP_JSON" ]; then
    echo -e "${RED}错误: 无法获取配置文件或文件为空！${NC}"
    exit 1
fi

echo -e "${GREEN}配置获取成功！正在解析...${NC}"

# --- 步骤2: 解析 JSON (使用 awk) ---
# 这是一个核心难点，因为安卓没有 jq，我们用 awk 模拟解析
# 目标格式: 分组名|APP名|版本号|下载地址
awk -F'"' '
BEGIN {
    current_group = "未知"
}
# 匹配 Group 的 name (层级较浅)
/^[ \t]*"name":/ {
    # 简单的层级判断，如果后面紧跟着 "list"，说明这是组名
    if ($0 ~ /"list"/) { next } # 忽略 list 行
    # 这是一个比较粗糙但有效的判断：如果是在 list 数组外
    # 但由于 awk 是流式处理，我们利用 list 里的结构特征
}

# 遇到 name
/"name":/ {
    val = $4
    # 如果这一行缩进较少（假设），或者是组名
    # 这里我们采用一种更流式的逻辑：
    # 在 JSON 中，Group 的 name 后面通常跟着 list [
    line = $0
}

# 重新编写解析逻辑，适应 yysd-zl.json 的特定格式
{
    # 移除首尾空白
    gsub(/^[ \t]+|[ \t]+$/, "", $0)
}

# 识别组名：包含 "name" 且不包含 "url" 或 "icon"，且下一行通常是 list
/"name":/ && !/"url":/ && !/"icon":/ {
    current_group = $4
}

# 识别 APP：如果在 list 内部
/"name":/ && (/"url":/ || /"icon":/ || /"version":/ || length($0) > 0) {
    # 这里通过状态机来捕获一个 item
}
' "$TEMP_JSON" > /dev/null

# === 更加暴力的解析方案 (适配 Shell) ===
# 将 JSON 转换为单行流，然后用特定的标识符切割
# 1. 提取所有关键字段
# 逻辑：利用 sed 将 json 格式化为易读的行块

# 清空解析文件
: > "$TEMP_PARSED"

# 使用 sed 和 awk 提取数据
# 格式化策略：找到 Group，然后遍历 List
# 由于 Shell 处理复杂 JSON 很累，我们采用基于行特征的提取
# 假设文件格式比较规范

current_group=""
current_name=""
current_ver=""
current_url=""

# 逐行读取
while IFS= read -r line; do
    # 去除两端空格
    trim_line=$(echo "$line" | sed 's/^[ \t]*//;s/[ \t]*$//')
    
    # 1. 检测分组名 (特征: "name": "XXX", 且不在对象内部)
    # 实际上 yysd-zl.json 的格式是: { "name": "推荐", "list": [ ...
    if echo "$trim_line" | grep -q '"name":'; then
        # 提取值
        val=$(echo "$trim_line" | cut -d'"' -f4)
        
        # 如果下一行包含 "list" 或者当前行后面有 [，则它是组名
        # 但在流中很难看下一行。
        # 此时利用变量置空法。
        # 每次遇到新的 APP 属性，如果 current_url 等为空，说明这个 name 是新的。
        # 但组名和APP名都叫 "name"。
        
        # 修正策略：利用 list 结构。
        # 这是一个临时变量，先存着。
        temp_name="$val"
    fi

    # 检测 list 开始
    if echo "$trim_line" | grep -q '"list":'; then
        current_group="$temp_name"
    fi

    # 检测 APP 属性
    if echo "$trim_line" | grep -q '"url":'; then
        current_url=$(echo "$trim_line" | cut -d'"' -f4)
        # 如果这行有 url，说明刚才的 temp_name 其实是 app_name
        current_name="$temp_name"
    fi
    
    if echo "$trim_line" | grep -q '"version":'; then
        current_ver=$(echo "$trim_line" | cut -d'"' -f4)
        
        # 此时一个 APP 信息收集完毕，写入文件
        if [ -n "$current_group" ] && [ -n "$current_name" ] && [ -n "$current_url" ]; then
            echo "${current_group}|${current_name}|${current_ver}|${current_url}" >> "$TEMP_PARSED"
        fi
        
        # 重置 APP 变量 (组名保留)
        current_name=""
        current_ver=""
        current_url=""
    fi

done < "$TEMP_JSON"

# --- 步骤3: 循环对比与下载 ---
echo -e "${BLUE}开始检测更新...${BLUE}"
echo "----------------------------------------"

COUNT=0
UPDATE_COUNT=0

while IFS='|' read -r group name ver url; do
    # 过滤空行
    [ -z "$name" ] && continue
    
    # 1. 处理下载链接隐私/加速
    final_url="$url"
    if echo "$url" | grep -q "github" && ! echo "$url" | grep -q "$ACCEL_PREFIX"; then
        final_url="${ACCEL_PREFIX}${url}"
    fi

    # 2. 提取作者 (OK 或 FM)
    author="UNK"
    if echo "$ver" | grep -q "-"; then
        author=$(echo "$ver" | cut -d'-' -f1)
    fi

    # 3. 生成唯一标识 ID (用于文件名和记录)
    # 文件名格式: [分组]应用名_作者_版本.apk
    # 记录文件名: 分组_应用名_作者.txt
    
    # 清洗文件名中的非法字符
    safe_group=$(echo "$group" | tr -d '/\?%*:|"<>')
    safe_name=$(echo "$name" | tr -d '/\?%*:|"<>')
    
    # 唯一ID (用于记录版本)
    uid="${safe_group}_${safe_name}_${author}"
    record_file="$REPO_DIR/${uid}.txt"
    
    # 读取本地旧版本
    local_ver=""
    if [ -f "$record_file" ]; then
        local_ver=$(cat "$record_file")
    fi

    # 4. 对比版本
    if [ "$local_ver" != "$ver" ]; then
        echo -e "发现更新: [${group}] ${name}"
        echo -e "  - 旧版本: ${RED}${local_ver:-无}${NC}"
        echo -e "  - 新版本: ${GREEN}${ver}${NC}"
        
        # 5. 下载文件
        # 文件名: [推荐]手机-32_OK_v3.6.0.apk
        apk_name="[${safe_group}]${safe_name}_${author}_${ver}.apk"
        save_path="$APP_DIR/$apk_name"
        
        echo -e "  - 正在下载..."
        curl -k -L "$final_url" -o "$save_path" --progress-bar
        
        if [ $? -eq 0 ]; then
            echo -e "  - ${GREEN}下载完成: $apk_name${NC}"
            # 更新本地记录
            echo "$ver" > "$record_file"
            UPDATE_COUNT=$((UPDATE_COUNT+1))
        else
            echo -e "  - ${RED}下载失败!${NC}"
        fi
        echo "----------------------------------------"
    else
        # 没更新时不刷屏，或者可以输出一个点
        # echo -e "跳过: $name ($ver)"
        :
    fi
    
    COUNT=$((COUNT+1))

done < "$TEMP_PARSED"

# --- 结束 ---
echo -e "${BLUE}检测完成!${NC}"
echo -e "共扫描: $COUNT 个应用"
echo -e "已更新: $UPDATE_COUNT 个应用"
echo -e "APK存放位置: ${YELLOW}$APP_DIR${NC}"

# 清理临时文件
rm -f "$TEMP_JSON" "$TEMP_PARSED"
