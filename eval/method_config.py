"""
Patch方法配置
"""

METHOD_CONFIGS = {
    "model": {
        "name": "model",
        "display_name": "Model Patch (Qwen2.5-72B)",
        "file_extensions": [".diff"],
        "format_type": "diff",
        "log_dir": "logs/model_patch",
        "task_prefix": "mp",
        "description": "Qwen2.5-72B生成的patch (126条resolved)"
    },
    "gold": {
        "name": "gold",
        "display_name": "Gold Patch",
        "file_extensions": [".diff"],
        "format_type": "diff",
        "log_dir": "logs/gold_patch",
        "task_prefix": "gp",
        "description": "SWE-bench官方gold patch"
    }
}

DEFAULT_METHOD = "model"


def get_method_config(method_name: str):
    """获取方法配置"""
    return METHOD_CONFIGS.get(method_name)


def list_methods():
    """列出所有可用的方法"""
    return list(METHOD_CONFIGS.keys())
