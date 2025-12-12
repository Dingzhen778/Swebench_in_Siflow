#!/usr/bin/env python3
"""
在容器内应用Agentless SEARCH/REPLACE patch

用法: python apply_agentless.py <agentless_raw_file>
"""

import sys
import re
from pathlib import Path
from collections import OrderedDict


def extract_python_blocks(text):
    """提取```python代码块"""
    pattern = r"```python\n(.*?)\n```"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches


def split_edit_multifile_commands(commands):
    """拆分多文件编辑命令"""
    file_to_commands = OrderedDict()

    for command in commands:
        file_name = None
        for subcommand in command.split(">>>>>>> REPLACE")[:-1]:
            subcommand = subcommand.strip()
            if "<<<<<<< SEARCH" in subcommand:
                fn = subcommand.split("<<<<<<< SEARCH")[0].lstrip("#").strip()
                if fn:
                    file_name = fn.strip("'\"")

            if len(subcommand.split("<<<<<<< SEARCH")) != 2:
                continue

            converted_command = (
                "<<<<<<< SEARCH"
                + subcommand.split("<<<<<<< SEARCH")[1]
                + "\n"
                + ">>>>>>> REPLACE"
            )

            if file_name not in file_to_commands or converted_command not in file_to_commands.get(file_name, []):
                file_to_commands.setdefault(file_name, []).append(converted_command)

    return file_to_commands


def apply_search_replace(file_path, commands, verbose=True):
    """应用SEARCH/REPLACE到文件"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except FileNotFoundError:
        if verbose:
            print(f"  [WARNING] File not found: {file_path}")
        return False

    original_content = content
    applied = 0

    for cmd in commands:
        if not cmd.startswith("<<<<<<< SEARCH") or not cmd.endswith(">>>>>>> REPLACE"):
            continue

        lines = cmd.splitlines()[1:-1]
        cmd_body = "\n".join(lines)

        if "\n=======\n" not in cmd_body:
            continue

        search, replace = cmd_body.split("\n=======\n", 1)

        # 尝试直接替换
        if search in content:
            content = content.replace(search, replace, 1)
            applied += 1
            if verbose:
                print(f"    [OK] Applied edit #{applied}")
        else:
            # 尝试带换行符
            search_with_nl = "\n" + search + "\n"
            replace_with_nl = "\n" + replace + "\n"
            if search_with_nl in content:
                content = content.replace(search_with_nl, replace_with_nl, 1)
                applied += 1
                if verbose:
                    print(f"    [OK] Applied edit #{applied} (with newlines)")
            else:
                if verbose:
                    print(f"    [WARNING] SEARCH block not found (edit #{applied+1})")
                    print(f"       First 80 chars: {search[:80].replace(chr(10), '<NL>')}")

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True

    return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python apply_agentless.py <agentless_raw_file>")
        sys.exit(1)

    agentless_file = sys.argv[1]

    print(f"[INFO] Reading Agentless patch: {agentless_file}")

    try:
        raw_output = Path(agentless_file).read_text()
    except Exception as e:
        print(f"[ERROR] Cannot read file: {e}")
        sys.exit(1)

    # 提取Python代码块
    code_blocks = extract_python_blocks(raw_output)
    if not code_blocks:
        print("[ERROR] No Python code blocks found")
        sys.exit(1)

    print(f"[INFO] Found {len(code_blocks)} Python code blocks")

    # 拆分多文件命令
    file_to_commands = split_edit_multifile_commands(code_blocks)
    if not file_to_commands:
        print("[ERROR] No file commands found")
        sys.exit(1)

    print(f"[INFO] Found {len(file_to_commands)} files to edit\n")

    # 应用编辑
    success_count = 0
    for file_path, commands in file_to_commands.items():
        print(f"[INFO] Editing {file_path} ({len(commands)} edits)...")
        if apply_search_replace(file_path, commands):
            success_count += 1
            print(f"  [SUCCESS] Updated {file_path}")
        else:
            print(f"  [WARNING] No changes to {file_path}")

    print(f"\n[INFO] Applied edits to {success_count}/{len(file_to_commands)} files")

    if success_count > 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
