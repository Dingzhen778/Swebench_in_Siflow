#!/bin/bash
# 在Docker容器内应用Agentless SEARCH/REPLACE patch
# 用法: ./apply_agentless_in_container.sh <agentless_raw_file>

set -e

AGENTLESS_FILE="$1"

if [ ! -f "$AGENTLESS_FILE" ]; then
    echo "Error: Agentless file not found: $AGENTLESS_FILE"
    exit 1
fi

echo "📥 应用Agentless patch: $AGENTLESS_FILE"

# Python脚本应用SEARCH/REPLACE
python3 << 'PYTHON_SCRIPT'
import sys
import re
from pathlib import Path

def extract_python_blocks(text):
    pattern = r"```python\n(.*?)\n```"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches

def split_edit_multifile_commands(commands):
    from collections import OrderedDict
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

def apply_search_replace(file_path, commands):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"⚠️  File not found: {file_path}")
        return False

    original_content = content

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
            print(f"  ✓ Applied edit to {file_path}")
        else:
            # 尝试带换行符
            search_with_nl = "\n" + search + "\n"
            replace_with_nl = "\n" + replace + "\n"
            if search_with_nl in content:
                content = content.replace(search_with_nl, replace_with_nl, 1)
                print(f"  ✓ Applied edit to {file_path} (with newlines)")
            else:
                print(f"  ⚠️  SEARCH block not found in {file_path}")

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True

    return False

# 主流程
agentless_file = sys.argv[1]
raw_output = Path(agentless_file).read_text()

code_blocks = extract_python_blocks(raw_output)
if not code_blocks:
    print("❌ No Python code blocks found")
    sys.exit(1)

file_to_commands = split_edit_multifile_commands(code_blocks)
if not file_to_commands:
    print("❌ No file commands found")
    sys.exit(1)

print(f"📝 Found {len(file_to_commands)} files to edit")

success_count = 0
for file_path, commands in file_to_commands.items():
    print(f"📄 Editing {file_path} ({len(commands)} edits)...")
    if apply_search_replace(file_path, commands):
        success_count += 1

print(f"\n✅ Applied edits to {success_count}/{len(file_to_commands)} files")

if success_count == 0:
    sys.exit(1)

PYTHON_SCRIPT
python3 << 'END_PYTHON' "$AGENTLESS_FILE"
