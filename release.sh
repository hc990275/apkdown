#!/usr/bin/env bash
# 一键超级发布脚本：
# - 自动修改 apkdown.sh 中的 SCRIPT_VERSION
# - 自动生成/更新 CHANGELOG.md
# - git add .
# - git commit
# - git tag
# - git push main + tag

set -euo pipefail

SCRIPT_FILE="apkdown.sh"

if [ $# -lt 1 ]; then
  echo "用法: $0 <版本号(例如 v11.02)> [提交说明]"
  exit 1
fi

NEW_VERSION="$1"                            # 例如 v11.02
COMMIT_MESSAGE="${2:-"chore: release $NEW_VERSION"}"

echo "==============================="
echo "  🔥 apkdown 一键超级发布脚本"
echo "==============================="
echo ""
echo "📦 目标版本号: $NEW_VERSION"
echo "📝 提交说明:   $COMMIT_MESSAGE"
echo ""

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

# 兼容 Linux / macOS 的 sed -i
sed_inplace() {
  if sed --version >/dev/null 2>&1; then
    # GNU sed (Linux / Termux 通常是这个)
    sed -i "$@"
  else
    # BSD sed (macOS)
    local file="${!#}"
    local expr=("${@:1:$(($#-1))}")
    sed -i "" "${expr[@]}" "$file"
  fi
}

echo "🔧 正在更新 $SCRIPT_FILE 中的 SCRIPT_VERSION 为: $NEW_VERSION"

# 修改脚本中的版本号行：SCRIPT_VERSION="xxx"
if grep -q '^SCRIPT_VERSION="' "$SCRIPT_FILE"; then
  sed_inplace "s/^SCRIPT_VERSION=\"[^\"]*\"/SCRIPT_VERSION=\"$NEW_VERSION\"/" "$SCRIPT_FILE"
else
  echo "⚠️ 未找到 SCRIPT_VERSION 行，追加一行到脚本顶部。"
  # 在文件开头插入一行
  tmp_file="$(mktemp)"
  echo "SCRIPT_VERSION=\"$NEW_VERSION\"" > "$tmp_file"
  cat "$SCRIPT_FILE" >> "$tmp_file"
  mv "$tmp_file" "$SCRIPT_FILE"
fi

echo "✅ SCRIPT_VERSION 已更新。"
echo ""

############################################
# 生成 / 更新 CHANGELOG.md（自动插入新版本）
############################################
echo "📝 正在生成/更新 CHANGELOG.md ..."

DATE="$(date +%Y-%m-%d)"
LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [ -z "$LAST_TAG" ]; then
  echo "ℹ️ 未找到历史 tag，将使用所有提交记录生成变更列表。"
  LOG_RANGE=""
else
  echo "ℹ️ 上一个版本 tag: $LAST_TAG"
  LOG_RANGE="$LAST_TAG..HEAD"
fi

TEMP_CHANGELOG="$(mktemp)"

{
  echo "# 更新日志"
  echo ""
  echo "## $NEW_VERSION ($DATE)"
  echo ""

  if [ -z "$LOG_RANGE" ]; then
    git log --pretty=format:'- %s'
  else
    git log "$LOG_RANGE" --pretty=format:'- %s'
  fi

  echo ""

  # 如果已有 CHANGELOG.md，把旧内容（去掉原来的第一行标题）接在后面
  if [ -f CHANGELOG.md ]; then
    sed '1d' CHANGELOG.md || true
  fi
} > "$TEMP_CHANGELOG"

mv "$TEMP_CHANGELOG" CHANGELOG.md

echo "✅ CHANGELOG.md 已更新。"
echo ""

############################################
# Git 提交 + 打标签 + 推送
############################################

echo "🔍 当前 Git 状态："
git status
echo ""

read -p "❓ 确认要继续发布并推送到远程吗？(y/N): " CONFIRM
CONFIRM="${CONFIRM:-N}"

if [[ ! "$CONFIRM" =~ ^[yY]$ ]]; then
  echo "⚠️ 已取消发布。"
  exit 0
fi

echo "🔧 执行: git add ."
git add .

echo "💾 执行: git commit -m \"$COMMIT_MESSAGE\""
git commit -m "$COMMIT_MESSAGE"

echo "🏷️ 创建标签