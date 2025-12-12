# 项目通用化改造方案

## 目标
支持不同的patch生成方法（如agentless, claude, gpt4等），让项目可以灵活评估不同方法生成的patch。

## 当前问题

### 1. 硬编码的Patch方法名称
- `run_model_eval.py`: 硬编码为"model"
- `run_gold_eval_fixed.py`: 硬编码为"gold"和"model"
- 任务名称前缀: 硬编码为"mp"（model-patch）和"gf"（gold-fixed）

### 2. 硬编码的Patch文件路径
- `/volume/ai-infra/rhjiang/SWE-bench-cc/predictions/model` (绝对路径)
- `patches/model/` (相对路径)
- 应该支持: `patches/{method_name}/`

### 3. 硬编码的Patch文件扩展名
- `.diff` (标准格式)
- `.agentless_raw` (Agentless格式)
- 应该支持自定义扩展名

### 4. 硬编码的日志输出目录
- `eval_outputs/` (旧)
- `model_patch_logs/` (当前)
- 应该支持: `{method_name}_patch_logs/`

### 5. 硬编码的Patch格式处理
- `apply_agentless.py`: 专门处理Agentless格式
- 应该支持插件化的格式处理器

## 改造方案

### 方案1: 配置文件 + 方法注册机制

#### 1.1 创建方法配置文件 `eval/method_config.py`

```python
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
    }
}

# 默认方法
DEFAULT_METHOD = "agentless"
```

#### 1.2 创建Patch格式处理器接口 `eval/patch_processors.py`

```python
"""
Patch格式处理器
支持不同的patch格式转换和应用
"""

class PatchProcessor:
    """Patch处理器基类"""
    
    def can_handle(self, file_path: Path) -> bool:
        """判断是否能处理该文件"""
        raise NotImplementedError
    
    def convert_to_diff(self, file_path: Path, output_path: Path) -> bool:
        """转换为标准git diff格式"""
        raise NotImplementedError
    
    def apply_directly(self, file_path: Path, repo_dir: Path) -> bool:
        """直接应用patch（如果支持）"""
        raise NotImplementedError


class AgentlessProcessor(PatchProcessor):
    """Agentless SEARCH/REPLACE格式处理器"""
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix == ".agentless_raw"
    
    def convert_to_diff(self, file_path: Path, output_path: Path) -> bool:
        # 使用现有的apply_agentless.py逻辑
        ...
    
    def apply_directly(self, file_path: Path, repo_dir: Path) -> bool:
        # 使用现有的apply_agentless.py逻辑
        ...


class DiffProcessor(PatchProcessor):
    """标准git diff格式处理器"""
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix in [".diff", ".patch"]
    
    def convert_to_diff(self, file_path: Path, output_path: Path) -> bool:
        # 直接复制
        import shutil
        shutil.copy(file_path, output_path)
        return True
    
    def apply_directly(self, file_path: Path, repo_dir: Path) -> bool:
        # 使用git apply
        ...


# 注册所有处理器
PATCH_PROCESSORS = {
    "agentless": AgentlessProcessor(),
    "diff": DiffProcessor(),
}
```

#### 1.3 修改 `run_gold_eval_fixed.py`

**关键修改点：**

1. **函数签名修改**:
```python
def run_gold_eval_for_instance(
    instance_id, 
    image_version=None, 
    timeout=1800, 
    wait=True, 
    method_name="agentless",  # 新增：方法名称
    patch_type="gold"  # 保留兼容性，但优先使用method_name
):
```

2. **Patch文件路径**:
```python
# 旧代码
model_patch_dir = Path("/volume/ai-infra/rhjiang/SWE-bench-cc/predictions/model")

# 新代码
from method_config import METHOD_CONFIGS
method_config = METHOD_CONFIGS.get(method_name)
patch_dir = Path(f"patches/{method_config['name']}")
```

3. **任务名称生成**:
```python
# 旧代码
if patch_type == "model":
    prefix_code = "mp"
else:
    prefix_code = "gf"

# 新代码
prefix_code = method_config['task_prefix']
```

4. **日志输出路径**:
```python
# 旧代码
test_output_file = f".../eval_outputs/{instance_id}_test_output.txt"

# 新代码
log_dir = method_config['log_dir']
test_output_file = f".../{log_dir}/{instance_id}_test_output.txt"
```

5. **Patch格式处理**:
```python
# 旧代码
if '.agentless_raw' in str(patch_file_path):
    # 硬编码的agentless处理

# 新代码
from patch_processors import PATCH_PROCESSORS
processor = PATCH_PROCESSORS[method_config['format_type']]
if processor.can_handle(patch_file_path):
    # 使用处理器
```

#### 1.4 修改 `run_model_eval.py`

**关键修改点：**

1. **支持方法参数**:
```python
def run_patch_eval(instance_id, method_name="agentless"):
    """运行指定方法的patch评估"""
    
    from method_config import METHOD_CONFIGS
    method_config = METHOD_CONFIGS.get(method_name)
    if not method_config:
        raise ValueError(f"Unknown method: {method_name}")
    
    # 检测patch文件
    patch_dir = Path(f"patches/{method_config['name']}")
    patch_file = None
    for ext in method_config['file_extensions']:
        candidate = patch_dir / f"{instance_id}{ext}"
        if candidate.exists():
            patch_file = candidate
            break
    
    # 调用评估
    result = run_gold_eval_for_instance(
        instance_id=instance_id,
        method_name=method_name,  # 传递方法名
        patch_type="custom"  # 非gold
    )
```

#### 1.5 创建新的统一入口脚本 `eval/run_eval.py`

```python
"""
统一的评测入口脚本
支持不同方法的patch评测
"""

import argparse
from method_config import METHOD_CONFIGS, DEFAULT_METHOD

def main():
    parser = argparse.ArgumentParser(description="SWE-bench Patch评测")
    parser.add_argument("instance_id", help="Instance ID")
    parser.add_argument("--method", default=DEFAULT_METHOD, 
                       choices=list(METHOD_CONFIGS.keys()),
                       help="Patch生成方法")
    parser.add_argument("--version", help="镜像版本")
    parser.add_argument("--wait", action="store_true", help="等待完成")
    
    args = parser.parse_args()
    
    if args.method == "gold":
        from run_gold_eval_fixed import run_gold_eval_for_instance
        run_gold_eval_for_instance(
            instance_id=args.instance_id,
            method_name="gold",
            wait=args.wait
        )
    else:
        from run_model_eval import run_patch_eval
        run_patch_eval(
            instance_id=args.instance_id,
            method_name=args.method
        )

if __name__ == "__main__":
    main()
```

#### 1.6 更新 `README.md`

添加"配置新方法"章节：

```markdown
## 配置新的Patch生成方法

### 1. 添加方法配置

编辑 `eval/method_config.py`，添加新方法：

```python
METHOD_CONFIGS = {
    "your_method": {
        "name": "your_method",
        "display_name": "Your Method",
        "file_extensions": [".diff", ".patch"],  # 支持的扩展名
        "format_type": "diff",  # 格式类型（diff或agentless）
        "log_dir": "your_method_patch_logs",  # 日志目录
        "task_prefix": "ym",  # SiFlow任务名前缀
        "description": "Your method description"
    }
}
```

### 2. 放置Patch文件

将patch文件放到对应目录：
```
patches/your_method/{instance_id}.diff
```

### 3. 运行评测

```bash
python eval/run_eval.py <instance_id> --method your_method
```

### 4. 查看结果

结果日志在：
```
your_method_patch_logs/{instance_id}_test_output.txt
```

SiFlow任务名称格式：
```
eval-{short_id}-{task_prefix}-{timestamp}
```
```

## 文件修改清单

### 需要修改的文件

1. **新建文件**:
   - `eval/method_config.py` - 方法配置
   - `eval/patch_processors.py` - Patch格式处理器
   - `eval/run_eval.py` - 统一入口脚本

2. **修改文件**:
   - `eval/run_gold_eval_fixed.py` - 支持method_name参数
   - `eval/run_model_eval.py` - 重构为通用方法
   - `README.md` - 更新文档

3. **保持兼容**:
   - `eval/apply_agentless.py` - 保留，作为AgentlessProcessor的实现
   - `eval/agentless_parser.py` - 保留

### 向后兼容性

- 保留`patch_type`参数，但优先使用`method_name`
- 默认方法为"agentless"，保持现有行为
- 旧的`run_model_eval.py`仍然可用，内部调用新接口

## 实施步骤

1. ✅ 创建`method_config.py`配置文件
2. ✅ 创建`patch_processors.py`处理器接口
3. ✅ 重构`run_gold_eval_fixed.py`支持方法配置
4. ✅ 重构`run_model_eval.py`为通用方法
5. ✅ 创建统一入口`run_eval.py`
6. ✅ 更新`README.md`文档
7. ✅ 测试验证（使用现有agentless方法）
8. ✅ 提交代码

## 示例：添加Claude方法

```bash
# 1. 配置方法（已在method_config.py中）
# 2. 放置patch文件
cp claude_patches/*.diff patches/claude/

# 3. 运行评测
python eval/run_eval.py django__django-13670 --method claude

# 4. 查看结果
cat claude_patch_logs/django__django-13670_test_output.txt
```

## 优势

1. **灵活性**: 轻松添加新方法，无需修改核心代码
2. **可维护性**: 配置与代码分离，清晰明了
3. **可扩展性**: 支持新的patch格式处理器
4. **向后兼容**: 保持现有功能不变
5. **统一接口**: 所有方法使用相同的评测逻辑

