"""
Patch方法配置
每个方法定义：
- 方法名称（用于路径、任务名等）
- Patch文件扩展名
- Patch格式类型（用于选择处理器）
- 日志目录名称
"""

METHOD_CONFIGS = {
    "agentless": {
        "name": "agentless",
        "display_name": "Agentless",
        "file_extensions": [".agentless_raw"],
        "format_type": "agentless",  # 使用agentless处理器
        "log_dir": "agentless_patch_logs",
        "task_prefix": "agentless",
        "description": "Agentless SEARCH/REPLACE格式"
    },
    "claude": {
        "name": "claude",
        "display_name": "Claude",
        "file_extensions": [".diff", ".patch"],
        "format_type": "diff",  # 标准git diff
        "log_dir": "claude_patch_logs",
        "task_prefix": "claude",
        "description": "Claude生成的git diff格式"
    },
    "gpt4": {
        "name": "gpt4",
        "display_name": "GPT-4",
        "file_extensions": [".diff", ".patch"],
        "format_type": "diff",
        "log_dir": "gpt4_patch_logs",
        "task_prefix": "gpt4",
        "description": "GPT-4生成的git diff格式"
    },
    "gold": {
        "name": "gold",
        "display_name": "Gold Patch",
        "file_extensions": [".diff"],
        "format_type": "diff",
        "log_dir": "gold_patch_logs",
        "task_prefix": "gf",  # 保持兼容
        "description": "SWE-bench官方gold patch"
    },
    # 向后兼容：model作为agentless的别名
    "model": {
        "name": "agentless",
        "display_name": "Agentless (model)",
        "file_extensions": [".agentless_raw", ".diff"],
        "format_type": "agentless",
        "log_dir": "model_patch_logs",  # 保持旧目录名
        "task_prefix": "mp",  # 保持旧前缀
        "description": "Agentless SEARCH/REPLACE格式（向后兼容）"
    }
}

# 默认方法
DEFAULT_METHOD = "agentless"


def get_method_config(method_name: str):
    """
    获取方法配置
    
    Args:
        method_name: 方法名称
        
    Returns:
        方法配置字典，如果不存在则返回None
    """
    return METHOD_CONFIGS.get(method_name)


def list_methods():
    """列出所有可用的方法"""
    return list(METHOD_CONFIGS.keys())

