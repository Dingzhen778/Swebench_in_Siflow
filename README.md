# SWE-bench SiFlow 评估系统

SWE-bench评估系统的SiFlow平台实现，支持3层Docker镜像构建和Gold/Model Patch评估。

## 目录结构

```
3-layer-test/
├── README.md                           # 本文档
├── build_all_images.py                 # 批量构建所有层级镜像（主入口）
├── build_layer1_base.py                # 构建Layer 1: Base镜像
├── build_layer2_env.py                 # 构建Layer 2: Environment镜像
├── build_layer3_instance.py            # 构建Layer 3: Instance镜像
├── fix_build_issues.py                 # 特殊instance的构建修复配置
├── repo_version_to_python.py           # Repo和Python版本映射
├── siflow_config.py                    # SiFlow平台配置
├── siflow_utils.py                     # SiFlow工具函数
├── run_gold_eval_fixed.py              # 运行Gold Patch评估
├── run_model_eval.py                   # 运行Model Patch评估
├── agentless_parser.py                 # 解析Agentless SEARCH/REPLACE格式
└── apply_agentless.py                  # 应用Agentless格式patch
```

## 快速开始

### 1. 构建镜像

#### 构建所有层级（一键构建）
```bash
# 默认版本2.0.0
python build_all_images.py

# 指定版本
python build_all_images.py --version 2.1.0

# 只构建特定层级
python build_all_images.py --layer instance --version 2.0.0

# 强制重建
python build_all_images.py --force
```

#### 从JSON文件构建指定instances
```bash
python build_all_images.py --layer instance \
  --instances-file validation_instances.json \
  --version 2.0.0 \
  --force
```

#### 分层构建

**Layer 1: Base镜像**（所有instance共享）
```bash
python build_layer1_base.py --version 2.0.0
```

**Layer 2: Environment镜像**（每个Python版本一个）
```bash
python build_layer2_env.py --version 2.0.0
```

**Layer 3: Instance镜像**（每个instance一个）
```bash
python build_layer3_instance.py <instance_id> --version 2.0.0
```

### 2. 运行评估

#### Gold Patch评估
```bash
# 单个instance
python run_gold_eval_fixed.py <instance_id> --version 2.0.0

# 等待任务完成
python run_gold_eval_fixed.py <instance_id> --version 2.0.0 --wait
```

#### Model Patch评估
```bash
# 单个instance
python run_model_eval.py <instance_id> --version 2.0.0

# 等待任务完成
python run_model_eval.py <instance_id> --version 2.0.0 --wait
```

## 镜像架构

### 3层Docker镜像设计

```
Layer 1: Base (swebench-base:2.0.0)
  └─ 系统依赖、git、conda等基础工具
     ↓
Layer 2: Environment (swebench-env-{repo}-{version}:2.0.0)
  └─ Python环境、特定版本的conda环境
     ↓
Layer 3: Instance (swebench-instance-{instance_id}:2.0.0)
  └─ 克隆代码仓库、安装项目依赖
```

**优势**：
- 缓存复用，加速构建
- Base层所有instance共享
- Environment层按Python版本复用（约60个）
- 总存储约100GB（env缓存）

### 镜像版本说明

- **2.0.0**：标准版本，适用于大部分instance（默认）
- **2.1.0**：特殊版本，用于26个需要特殊处理的instances
  - 20个sphinx-doc instances
  - 6个其他instances (django, pylint等)

**构建逻辑差异**：
- 2.0.0：标准构建流程
- 2.1.0：不使用environment_setup_commit，直接在base_commit上安装（更稳定）

## 评估流程

### Gold Patch评估流程

1. **加载Instance信息**：从Dataset获取instance元数据
2. **准备Patch文件**：读取gold patch和test patch
3. **查询镜像**：获取instance镜像URL
4. **生成评估脚本**：
   - 应用gold patch到源代码
   - 重新安装仓库
   - 重置测试文件到base_commit
   - 应用test patch
   - 运行测试
5. **创建SiFlow任务**：提交到平台运行
6. **解析结果**：
   - `RESOLVED_FULL`：所有FAIL_TO_PASS通过，所有PASS_TO_PASS保持通过
   - `RESOLVED_NO`：测试未全部通过

### Model Patch评估流程

类似Gold Patch，但：
- Patch来源：`/volume/ai-infra/rhjiang/SWE-bench-cc/predictions/model/`
- 支持两种格式：
  - 标准diff格式 (`.diff`)
  - Agentless SEARCH/REPLACE格式 (`.agentless_raw`)

## Patch格式

### 标准Diff格式

```diff
diff --git a/file.py b/file.py
index abc123..def456 100644
--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
 def foo():
-    return 1
+    return 2
```

### Agentless格式

```
<<<<<<< SEARCH
def foo():
    return 1
=======
def foo():
    return 2
>>>>>>> REPLACE
```

**处理流程**：
1. `agentless_parser.py` 解析SEARCH/REPLACE块
2. `apply_agentless.py` 应用修改到文件
3. `git diff` 生成标准diff
4. 用标准diff进行评估

## 特殊Instance处理

### fix_build_issues.py

针对28个需要特殊处理的instances，提供：

1. **环境变量修复**：
```python
INSTANCE_FIXES = {
    "sphinx-doc__sphinx-7440": {
        "env_vars": {
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PYTHONIOENCODING": "utf-8"
        }
    }
}
```

2. **安装命令修复**：
```python
"install_cmd": "python -m pip install -e .[test]"  # 移除--no-use-pep517
```

3. **Pre-install命令**：
```python
"pre_install": [
    "sed -i 's/pytest/pytest -rA/' tox.ini"
]
```

### 使用2.1.0镜像的26个instances

需要使用2.1.0版本的instances列表：

**Sphinx instances (20个)**：
- sphinx-doc__sphinx-7440, 7454, 7462, 7590, 7748, 7757
- sphinx-doc__sphinx-7889, 7910, 7985, 8035, 8056, 8120
- sphinx-doc__sphinx-8269, 8459, 8475, 8548, 8551, 8638
- sphinx-doc__sphinx-10323, 10435

**其他 (6个)**：
- django__django-10880, 10914, 11276, 15103
- pydata__xarray-6938
- pylint-dev__pylint-7277

**运行评估时指定版本**：
```bash
python run_gold_eval_fixed.py sphinx-doc__sphinx-7440 --version 2.1.0
```

## 配置说明

### siflow_config.py

```python
# 资源池配置
RESOURCE_POOL = "ai_infra"

# 实例类型
INSTANCE_TYPE = "t4-90GB-v1"

# 镜像拉取策略
IMAGE_PULL_POLICY = "IfNotPresent"
```

### 环境变量

需要在 `~/.siflow` 或环境变量中配置：
```bash
export SIFLOW_API_KEY="your_api_key"
export SIFLOW_API_URL="https://console.siflow.cn"
```

## 常见问题

### 1. 镜像构建失败

**问题**：Git checkout冲突
```
error: Your local changes would be overwritten by checkout
```

**解决**：这通常发生在尝试使用2.0.0构建需要2.1.0的26个特殊instances时。使用2.1.0版本：
```bash
python build_layer3_instance.py <instance_id> --version 2.1.0 --force
```

### 2. 依赖缺失

**问题**：ModuleNotFoundError: No module named 'roman'

**解决**：该instance需要使用2.1.0镜像。

### 3. 任务提交失败

**问题**：Task name too long (>35 chars)

**解决**：任务名称前缀会自动缩短，如果仍然超长，使用更短的task_name_suffix。

### 4. 镜像版本冲突

**问题**：平台上同一instance有2.0.0和2.1.0两个版本

**解决**：
- 保留需要的版本
- 删除不需要的版本（需要管理员权限）
- 确保评估时指定正确版本

## 文件路径

### Patch文件位置
```
/volume/ai-infra/rhjiang/SWE-bench-cc/predictions/
├── gold/                    # Gold patches (.diff)
├── model/                   # Model patches (.diff, .agentless_raw)
└── test_patches/            # Test patches (.diff)
```

### 评估输出
```
/volume/ai-infra/rhjiang/SWE-bench-cc/siflow/3-layer-test/eval_outputs/
└── {instance_id}_test_output.txt
```

### 构建日志
```
/tmp/
├── build_base.log
├── build_env.log
└── build_instance_{instance_id}.log
```

## 高级用法

### 批量构建特定repo的instances

```bash
python build_all_images.py \
  --layer instance \
  --repo "sphinx-doc/sphinx" \
  --version 2.1.0 \
  --force
```

### 分批构建（避免超时）

```bash
# 第1批：前100个
python build_all_images.py \
  --layer instance \
  --max 100 \
  --version 2.0.0

# 第2批：接下来100个（需要修改代码跳过前100）
```

### 检查镜像状态

```python
from siflow_utils import create_siflow_client, image_exists

client = create_siflow_client()
exists = image_exists(client, "swebench-instance-django__django-11039", "2.0.0")
print(f"镜像存在: {exists}")
```

## 性能优化

### 构建优化

1. **使用--force有选择性地重建**：只重建失败的镜像
2. **调整--delay参数**：根据API限流情况调整提交间隔
3. **分批构建**：大量镜像分批提交，避免超时

### 评估优化

1. **并发评估**：可以同时提交多个评估任务
2. **不等待模式**：使用批量脚本提交后在平台查看结果
3. **复用镜像**：确保镜像已缓存在平台上

## 开发指南

### 添加新的Instance修复

1. 在 `fix_build_issues.py` 的 `INSTANCE_FIXES` 中添加：
```python
"new-repo__new-instance": {
    "env_vars": {"VAR": "value"},
    "install_cmd": "custom install command",
    "pre_install": ["sed command"]
}
```

2. 重新构建该instance镜像：
```bash
python build_layer3_instance.py new-repo__new-instance --version 2.0.0 --force
```

### 修改评估脚本

评估脚本生成在 `run_gold_eval_fixed.py` 的 `generate_eval_script_fixed()` 函数中。

关键步骤顺序（不要改变）：
1. Apply patch
2. Reinstall repository
3. Reset test files to base_commit
4. Apply test patch
5. Run tests

## 参考资料

- SWE-bench官方仓库: https://github.com/princeton-nlp/SWE-bench
- SWE-bench论文: https://arxiv.org/abs/2310.06770
- Dataset: princeton-nlp/SWE-bench_Verified (Hugging Face)

## 版本历史

### v2.1.0 (2025-12-12)
- 添加26个特殊instance的2.1.0镜像支持
- 简化构建逻辑（不使用environment_setup_commit）
- 提高构建稳定性

### v2.0.0 (2025-12-10)
- 初始版本
- 3层镜像架构
- 支持Gold/Model Patch评估
- 支持Agentless格式

## License

MIT License
