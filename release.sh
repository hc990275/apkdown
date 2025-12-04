#!/usr/bin/env bash
# apkdown 一键发布脚本 v3.0
# 功能：
#  - 更新 apkdown.sh 中的 SCRIPT_VERSION
#  - 生成 CHANGELOG.md（只保留最新版本内容）
#  - 删除所有 .bak / .bak_* 备份文件
#  - git add . / commit / tag / push

set -euo pipefail

SCRIPT_FILE="apkdown.sh"

# --- 核心改动 1: 版本号处理（自动添加 'v' 前缀） ---
if [ $# -lt 1 ]; then
  # 提示用户输入时，说明只需输入数字
  read -p "请输入目标版本号（例如 11.08）：" INPUT_VERSION
  if [ -z "$INPUT_VERSION" ]; then
    echo "❌ 未输入版本号，发布取消。"
    exit 1
  fi
  # 检查是否已有 'v' 前缀，如果没有则添加
  if [[ "$INPUT_VERSION" != v* ]]; then
    VERSION="v$INPUT_VERSION"
  else
    VERSION="$INPUT_VERSION"
  fi
  MESSAGE="chore: release $VERSION"
else
  # 如果提供了参数，则按原逻辑赋值
  VERSION="$1"
  MESSAGE="${2:-chore: release $VERSION}"
  # 确保如果通过参数输入，也自动添加 'v' 前缀（可选，但更健壮）
  if [[ "$VERSION" != v* ]]; then
    VERSION="v$VERSION"
  fi
fi

echo "==============================="
echo "  apkdown 一键发布脚本 v3.0"
echo "==============================="
echo
echo "📦 目标版本号: $VERSION"
echo "📝 提交说明:   $MESSAGE"
echo

# 检查是否在 Git 仓库中
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "❌ 当前目录不是 Git 仓库，请先 cd 到 apkdown 仓库根目录再执行。"
  exit 1
fi

# 检查脚本文件是否存在
if [ ! -f "$SCRIPT_FILE" ]; then
  echo "❌ 找不到脚本文件: $SCRIPT_FILE"
  exit 1
fi

# 兼容 Linux / Termux / macOS 的 sed -i
sed_inplace() {
  if sed --version >/dev/null 2>&1; then
    # GNU sed (Termux / Linux)
    sed -i "$@"
  else
    # BSD sed (macOS)
    local file="${!#}"
    local expr=("${@:1:$(($#-1))}")
    sed -i "" "${expr[@]}" "$file"
  fi
}

echo "🔧 更新 $SCRIPT_FILE 中的 SCRIPT_VERSION 为: $VERSION"

if grep -q '^SCRIPT_VERSION="' "$SCRIPT_FILE"; then
  sed_inplace "s/^SCRIPT_VERSION=\"[^\"]*\"/SCRIPT_VERSION=\"$VERSION\"/" "$SCRIPT_FILE"
else
  echo "⚠️ 未找到 SCRIPT_VERSION 行，将追加到脚本开头。"
  tmp_file="$(mktemp)"
  echo "SCRIPT_VERSION=\"$VERSION\"" > "$tmp_file"
  cat "$SCRIPT_FILE" >> "$tmp_file"
  mv "$tmp_file" "$SCRIPT_FILE"
fi

echo "✅ SCRIPT_VERSION 已更新。"
echo

########################################
# 生成 CHANGELOG.md（只保留最新版本）
########################################
echo "📝 正在生成 CHANGELOG.md（仅保留最新版本内容）..."

CHANGELOG_FILE="CHANGELOG.md"

cat > "$CHANGELOG_FILE" <<EOF
# CHANGELOG

## $VERSION - $(date '+%Y-%m-%d %H:%M:%S')

$MESSAGE

EOF

echo "✅ 已覆盖生成 $CHANGELOG_FILE（只包含最新版本内容）"
echo

########################################
# 清理所有 .bak / .bak_* 备份文件
########################################
echo "🧹 正在清理所有 .bak / .bak_* 备份文件..."

# 删除所有 *.bak 和 *.bak_* 文件
find . -type f \( -name "*.bak" -o -name "*.bak_*" \) -print -delete || true

echo "✅ 备份文件清理完成。"
echo

########################################
# Git 状态确认
########################################
echo "🔍 当前 Git 状态:"
git status
echo

# --- 核心改动 2: 自动确认（删除 read -p 步骤） ---
echo "❓ 确认要继续提交并推送到远程吗？(y/N): y" # 模拟显示确认信息，但跳过等待
CONFIRM="y" # 直接设置为 'y'

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
  # 理论上永远不会执行，但为了脚本完整性保留
  echo "⚠️ 已取消发布。"
  exit 0
fi

########################################
# Git 提交 + 打标签 + 推送
########################################
echo "🔧 执行: git add ."
git add .

echo "💾 执行: git commit -m \"$MESSAGE\""
git commit -m "$MESSAGE"

echo "🏷️ 创建标签: $VERSION"
git tag "$VERSION"

echo "🚀 推送 main 分支到 origin ..."
git push origin main

echo "🚀 推送 tag $VERSION 到 origin ..."
git push origin "$VERSION"

echo
echo "🎉 一键发布完成！ 版本: $VERSION"
echo "👉 已更新 SCRIPT_VERSION、CHANGELOG.md，并清理所有 .bak 备份文件。"
