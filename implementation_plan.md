# apkdown.sh 代码审查与修复

对 `apkdown.sh` 脚本进行全面代码审查，识别 bug、健壮性问题、可移植性问题，并逐一修复。

## 发现的问题

### 🔴 Bug（会导致逻辑错误）

| # | 问题 | 行号 | 说明 |
|---|------|------|------|
| 1 | **`RED` 颜色变量未定义** | L155 | 使用了 `${RED}` 但从未定义，导致输出乱码 |
| 2 | **管道子 Shell 变量丢失** | L52-82 | `cat \| sed \| while` 构成管道，`while` 在子 Shell 中执行，内部写入 `$TEMP_LIST` 虽然不受影响（因为是文件写入），但变量 `temp_name`/`current_group` 等无法在管道外访问。当前逻辑恰好只依赖文件，所以是"隐性风险"而非立即崩溃 |
| 3 | **JSON 解析不可靠** | L52 | 用 `sed` 替换 `{}[],` 来解析 JSON 极其脆弱——URL 中的 `/` 不受影响，但如果 JSON 值中包含 `:` 符号（如 URL `https://...`），`cut -d':' -f1` / `cut -d':' -f2-` 会错误截断 key/value |
| 4 | **URL 中的冒号被错误分割** | L56-57 | `cut -d':' -f1` 提取 key 时，对于 `url:https://example.com`，key 会正确得到 `url`，但这依赖于 `f2-` 能取到剩余部分。实际问题在于：去掉引号后如果行是 `url: https://raw.githubusercontent.com/...`，`cut -d':' -f2-` 会得到 ` https` 后面完整 URL。这里勉强能工作但不够健壮 |

### 🟡 健壮性 & 可维护性问题

| # | 问题 | 行号 | 说明 |
|---|------|------|------|
| 5 | **Shebang 与 `echo -e` 不兼容** | L1 | `#!/bin/sh` 是 POSIX sh，但 `echo -e` 不是 POSIX 标准。在 dash 等 Shell 中 `echo -e` 会原样输出 `-e`。应改用 `printf` |
| 6 | **`count_total`/`count_update` 在管道外为 0** | L85-86, L159 | 因为第二个 `while` 使用 `< "$TEMP_LIST"` 重定向而非管道，所以此处实际上没问题。但如果 `TEMP_LIST` 为空，`count_total` 保持 0 |
| 7 | **缺少 `curl` 等工具的依赖检查** | 全局 | 没有检查 `curl`、`sed`、`cut` 等关键命令是否存在 |
| 8 | **临时文件无 trap 清理** | 全局 | 如果脚本中途被 Ctrl+C 中断，临时文件 `temp.json` 和 `list.txt` 不会被清理 |
| 9 | **旧版本 APK 文件未清理** | 全局 | 下载新版本时，旧版本的 APK 文件仍然留在 `APP库` 中，会越积越多 |
| 10 | **`-k` 忽略 SSL 证书验证** | L40, L148 | `curl -k` 会跳过 SSL 验证，存在安全风险 |

## 修复方案

### [MODIFY] apkdown.sh

1. **添加 `RED` 颜色定义**（L24 后新增）
2. **将 `echo -e` 全部替换为 `printf`**，确保 POSIX sh 兼容
3. **添加 `trap` 清理临时文件**，确保中断时也能清理
4. **添加 `curl` 依赖检查**
5. **下载新版本前删除同名应用旧版本文件**
6. **改进 URL key/value 提取逻辑**，使用 `sed` 替代 `cut` 来正确处理含 `:` 的 value

## 验证计划

### 手动验证
- 用户在终端中执行 `sh apkdown.sh`，确认：
  1. 无报错输出
  2. 颜色正常显示
  3. 能正常下载 APK（如有更新）
  4. Ctrl+C 中断后检查临时文件是否被清理
