#!/usr/bin/env bash
# 一键超级发布脚本（精简稳定版）

set -euo pipefail

SCRIPT_FILE="apkdown.sh"

if [ $# -lt 1 ]; then
  echo "用法: $0 <版本号(例如 v11.02)> [提交说明]"
  exit 1
fi

NEW_VERSION="$1"                   # 例如 v11.02
COMMIT_MESSAGE="${2:-chore: release $NEW_VERSION}"

echo "==============================="
echo "  apkdown 一键超级发布脚本"
echo "==============================="
echo
echo "目标版本号: $NEW_VERSION"
echo "提交说明:   $COMMIT_MESSAGE"
echo

# 检查是否在 Git 仓库
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
    # GNU sed (Termux 一般是这个)
    sed -i "$@"
  else
    # BSD sed (macOS)
    local file="${!#}"
    local expr=("${@:1:$(($#-1))}")
    sed -i "" "${expr[@]}" "$file"
  fi
}

echo "更新 $SCRIPT_FILE 中的 SCRIPT_VERSION 为: $NEW_VERSION"

if grep -q '^SCRIPT_VERSION="' "$SCRIPT_FILE"; then
  sed_inplace "s/^SCRIPT_VERSION=\"[^\"]*\"/SCRIPT_VERSION=\"$NEW_VERSION\"/" "$SCRIPT_FILE"
else
  echo "未找到 SCRIPT_VERSION 行，将追加到文件开头。"
  tmp_file="$(mktemp)"
  echo "SCRIPT_VERSION=\"$NEW_VERSION\"" > "$tmp_file"
  cat "$SCRIPT_FILE" >> "$tmp_file"
  mv "$tmp_file" "$SCRIPT_FILE"
fi

echo "SCRIPT_VERSION 已更新。"
echo

##############################
# 生成 / 更新 CHANGELOG.md
##############################
echo "生成/更新 CHANGELOG.md ..."

DATE="$(date +%Y-%m-%d)"
LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [ -z "$LAST_TAG" ]; then
  echo "未找到历史 tag，将使用所有提交记录。"
  LOG_RANGE=""
else
  echo "上一个版本 tag: $LAST_TAG"
  LOG_RANGE="$LAST_TAG..HEAD"
fi

TEMP_CHANGELOG="$(mktemp)"

{
  echo "# 更新日志"
  echo
  echo "## $NEW_VERSION ($DATE)"
  echo

  if [ -z "$LOG_RANGE" ]; then
    git log --pretty=format:'- %s'
  else
    git log "$LOG_RANGE" --pretty=format:'- %s'
  fi

  echo

  if [ -f CHANGELOG.md ]; then
    sed '1d' CHANGELOG.md || true
  fi
} > "$TEMP_CHANGELOG"

mv "$TEMP_CHANGELOG" CHANGELOG.md

echo "CHANGELOG.md 已更新。"
echo

##############################
# Git 提交 + 打标签 + 推送
##############################
echo "当前 Git 状态:"
git status
echo

printf "确认要继续发布并推送到远程吗？(y/N): "
read CONFIRM
CONFIRM="${CONFIRM:-N}"

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
  echo "已取消发布。"
  exit 0
fi

echo "执行: git add ."
git add .

echo "执行: git commit -m $COMMIT_MESSAGE"
git commit -m "$COMMIT_MESSAGE"

echo "创建标签: $NEW_VERSION"
git tag "$NEW_VERSION"

echo "推送 main 分支到 origin ..."
git push origin main

echo "推送 tag $NEW_VERSION 到 origin ..."
git push origin "$NEW_VERSION"

echo
echo "🎉 一键发布完成！ 版本: $NEW_VERSION"