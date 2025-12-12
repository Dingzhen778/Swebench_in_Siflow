"""
Patch格式处理器
支持不同的patch格式转换和应用
"""

import shutil
import subprocess
from pathlib import Path
from typing import Optional


class PatchProcessor:
    """Patch处理器基类"""
    
    def can_handle(self, file_path: Path) -> bool:
        """判断是否能处理该文件"""
        raise NotImplementedError
    
    def convert_to_diff(self, file_path: Path, output_path: Path, repo_dir: Path = None) -> bool:
        """
        转换为标准git diff格式
        
        Args:
            file_path: 输入patch文件路径
            output_path: 输出diff文件路径
            repo_dir: 仓库目录（某些格式需要）
            
        Returns:
            是否成功
        """
        raise NotImplementedError
    
    def apply_directly(self, file_path: Path, repo_dir: Path) -> bool:
        """
        直接应用patch（如果支持）
        
        Args:
            file_path: patch文件路径
            repo_dir: 仓库目录
            
        Returns:
            是否成功
        """
        raise NotImplementedError


class AgentlessProcessor(PatchProcessor):
    """Agentless SEARCH/REPLACE格式处理器"""
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix == ".agentless_raw"
    
    def convert_to_diff(self, file_path: Path, output_path: Path, repo_dir: Path = None) -> bool:
        """
        将Agentless格式转换为git diff
        
        注意：这个函数在容器内执行，需要apply_agentless.py脚本
        """
        # 这个转换在容器内通过脚本完成
        # 这里只是标记，实际逻辑在generate_eval_script_fixed中
        return True
    
    def apply_directly(self, file_path: Path, repo_dir: Path) -> bool:
        """
        直接应用Agentless格式（在容器内）
        
        注意：这个函数在容器内执行
        """
        # 实际应用在容器内通过apply_agentless.py完成
        return True


class DiffProcessor(PatchProcessor):
    """标准git diff格式处理器"""
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix in [".diff", ".patch"]
    
    def convert_to_diff(self, file_path: Path, output_path: Path, repo_dir: Path = None) -> bool:
        """直接复制diff文件"""
        try:
            shutil.copy(file_path, output_path)
            return True
        except Exception as e:
            print(f"Error copying diff file: {e}")
            return False
    
    def apply_directly(self, file_path: Path, repo_dir: Path) -> bool:
        """使用git apply应用patch"""
        try:
            result = subprocess.run(
                ["git", "apply", "--verbose", str(file_path)],
                cwd=repo_dir,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return True
            # 如果git apply失败，尝试patch命令
            result = subprocess.run(
                ["patch", "--batch", "--fuzz=5", "-p1", "-i", str(file_path)],
                cwd=repo_dir,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error applying diff: {e}")
            return False


# 注册所有处理器
PATCH_PROCESSORS = {
    "agentless": AgentlessProcessor(),
    "diff": DiffProcessor(),
}


def get_processor(format_type: str) -> Optional[PatchProcessor]:
    """
    获取指定格式的处理器
    
    Args:
        format_type: 格式类型（"agentless"或"diff"）
        
    Returns:
        处理器实例，如果不存在则返回None
    """
    return PATCH_PROCESSORS.get(format_type)

