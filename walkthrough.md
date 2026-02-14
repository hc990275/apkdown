# apkdown.sh 代码审查 - 变更总结

## 修复清单

| # | 修复项 | 类型 |
|---|--------|------|
| 1 | 添加缺失的 `RED` 颜色变量定义 | Bug |
| 2 | 所有 `echo -e` 替换为 `printf`（POSIX sh 兼容） | Bug |
| 3 | JSON key/value 提取改用 `sed` 替代 `cut`，正确处理 URL 中的冒号 | Bug |
| 4 | 版本记录文件使用 `printf '%s'` 而非 `echo`，避免末尾换行干扰对比 | Bug |
| 5 | 添加 `trap cleanup EXIT INT TERM`，确保中断时清理临时文件 | 健壮性 |
| 6 | 添加 `curl`/`sed`/`cut` 依赖检查 | 健壮性 |
| 7 | 下载新版本前自动删除同应用旧版本 APK | 健壮性 |
| 8 | `echo` 输出 `$ver` 到记录文件改为 `printf '%s'` 避免换行问题 | 健壮性 |
