"""
从Agentless复制的SEARCH/REPLACE解析函数（去除依赖）
"""

import re
from collections import OrderedDict


def extract_python_blocks(text):
    """提取```python代码块"""
    pattern = r"```python\n(.*?)\n```"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches


def split_edit_multifile_commands(commands, diff_format=False) -> dict:
    """拆分多文件编辑命令"""
    file_to_commands = OrderedDict()

    if diff_format:
        for command in commands:
            file_name = None
            for subcommand in command.split(">>>>>>> REPLACE")[:-1]:
                subcommand = subcommand.strip()
                if "<<<<<<< SEARCH" in subcommand:
                    fn = subcommand.split("<<<<<<< SEARCH")[0].lstrip("#").strip()
                    if fn:
                        file_name = "'" + fn + "'"

                if len(subcommand.split("<<<<<<< SEARCH")) != 2:
                    continue

                converted_command = (
                    "<<<<<<< SEARCH"
                    + subcommand.split("<<<<<<< SEARCH")[1]
                    + "\n"
                    + ">>>>>>> REPLACE"
                )

                # 去重
                if (
                    file_name not in file_to_commands
                    or converted_command not in file_to_commands[file_name]
                ):
                    file_to_commands.setdefault(file_name, []).append(converted_command)

    return file_to_commands


def parse_diff_edit_commands(commands, content, file_loc_intervals=None):
    """解析并应用SEARCH/REPLACE编辑"""
    if file_loc_intervals is None:
        file_loc_intervals = []

    replaced = False

    for subcommand in commands:
        if not subcommand.startswith("<<<<<<< SEARCH") or not subcommand.endswith(">>>>>>> REPLACE"):
            continue

        subcommand = "\n".join(subcommand.splitlines()[1:-1])

        if len(subcommand.split("\n=======\n")) != 2:
            continue

        original, replace = subcommand.split("\n=======\n")

        # 处理 "..."
        if replace.startswith("...\n") and len(replace) > 4:
            replace = replace[4:]

        if original == "...":
            # 特殊处理
            pass

        if original.startswith("...\n") and len(original) > 4:
            original = original[4:]

        # 应用替换
        original_with_newlines = "\n" + original + "\n"
        replace_with_newlines = "\n" + replace + "\n"

        if original_with_newlines in content:
            content = content.replace(original_with_newlines, replace_with_newlines, 1)
            replaced = True
        elif original in content:
            content = content.replace(original, replace, 1)
            replaced = True

    return content, replaced
