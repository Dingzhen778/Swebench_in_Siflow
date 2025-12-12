"""
获取 SWE-bench 仓库版本对应的 Python 版本

直接从 SWE-bench 官方的 MAP_REPO_VERSION_TO_SPECS 读取，确保版本准确
"""

from swebench.harness.constants import MAP_REPO_VERSION_TO_SPECS


def get_python_version(repo: str, project_version: str) -> str:
    """
    根据仓库名和项目版本获取对应的 Python 版本

    直接从 SWE-bench 官方的 MAP_REPO_VERSION_TO_SPECS 读取
    不使用任何硬编码，确保版本与 SWE-bench 官方完全一致

    Args:
        repo: 仓库名 (例如: django/django)
        project_version: 项目版本 (例如: 3.0, 5.2)

    Returns:
        Python 版本字符串 (例如: 3.9)

    Raises:
        ValueError: 如果找不到对应的配置
    """
    if repo not in MAP_REPO_VERSION_TO_SPECS:
        raise ValueError(f"未找到仓库 {repo} 的配置")

    if project_version not in MAP_REPO_VERSION_TO_SPECS[repo]:
        raise ValueError(f"未找到 {repo} 版本 {project_version} 的配置")

    specs = MAP_REPO_VERSION_TO_SPECS[repo][project_version]

    if 'python' not in specs:
        raise ValueError(f"Repo {repo} version {project_version} 的 specs 中没有 python 字段")

    return specs['python']
