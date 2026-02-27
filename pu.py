import os
import subprocess

def run_command(command, cwd=None):
    """
    执行 Shell 命令并捕获输出
    添加了 errors='replace'，彻底解决 Windows 下由于 Git 输出非 UTF-8 中文导致的线程崩溃问题
    """
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',  # 【关键修复点】：遇到无法解码的字节串时，替换为占位符而不抛出异常报错
        shell=False
    )

def main():
    # 获取当前脚本所在目录（即你的仓库根目录）
    base_dir = os.getcwd()
    print(f"🚀 开始遍历并强制推送当前目录下的所有 Git 仓库：\n{base_dir}\n")

    success_count = 0
    fail_count = 0

    # 遍历当前目录下的所有文件和文件夹
    for item in os.listdir(base_dir):
        repo_path = os.path.join(base_dir, item)
        
        # 严格判断：必须是一个文件夹，且内部包含 .git 目录，才是一个合法的 Git 仓库
        if os.path.isdir(repo_path) and os.path.exists(os.path.join(repo_path, ".git")):
            print("-" * 50)
            print(f"📦 正在处理仓库: {item}")
            
            # 步骤 1: 创建空提交 (Empty Commit)
            # --allow-empty 允许在没有文件更改的情况下生成一个新的 Commit ID，用于强制触发远端更新
            print("  📝 正在生成空提交...")
            commit_res = run_command(
                ["git", "commit", "--allow-empty", "-m", "chore: 强制推送以刷新远端状态"], 
                cwd=repo_path
            )
            
            # 步骤 2: 执行推送
            print("  ⬆️ 正在推送到 GitHub...")
            push_res = run_command(["git", "push"], cwd=repo_path)
            
            # 检查推送命令的退出状态码，0 表示完全成功
            if push_res.returncode == 0:
                print("  🎉 推送成功！")
                success_count += 1
            else:
                # 如果失败，打印出 stderr 中的错误信息方便排查排错
                print(f"  ❌ 推送失败: {push_res.stderr.strip()}")
                fail_count += 1

    # 打印最终统计结果，方便核对
    print("=" * 50)
    print("✨ 所有仓库强制推送执行完毕！")
    print(f"📊 统计: {success_count} 个推送成功 | {fail_count} 个推送失败")

if __name__ == "__main__":
    main()
