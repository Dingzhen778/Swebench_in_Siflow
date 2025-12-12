# SWE-bench SiFlow Evaluation System

基于SiFlow平台的SWE-bench评测系统，采用三层Docker镜像架构。

## 目录结构

```
3-layer-test/
├── build/                    # 镜像构建相关
│   ├── build_all_images.py   # 批量构建入口
│   ├── build_layer1_base.py  # Layer1: Base镜像
│   ├── build_layer2_env.py   # Layer2: Environment镜像
│   ├── build_layer3_instance.py  # Layer3: Instance镜像
│   ├── fix_build_issues.py   # 构建问题修复
│   └── repo_version_to_python.py # Python版本映射
├── eval/                     # 评测相关
│   ├── run_eval.py               # 统一评测入口（推荐使用）
│   ├── run_gold_eval_fixed.py    # Gold Patch评测
│   ├── run_model_eval.py         # 通用Patch评测（支持多种方法）
│   ├── method_config.py          # 方法配置文件
│   ├── patch_processors.py       # Patch格式处理器
│   ├── apply_agentless.py        # Agentless格式应用
│   └── agentless_parser.py       # Agentless格式解析
├── {method}_patch_logs/      # 各方法的评测日志目录
│   ├── agentless_patch_logs/  # Agentless方法日志
│   ├── claude_patch_logs/     # Claude方法日志
│   ├── gold_patch_logs/      # Gold Patch日志
│   └── model_patch_logs/      # Model Patch日志（向后兼容）
├── patches/                  # Patch文件
│   ├── gold/                 # Gold Patch (500个, 来自SWE-bench_Verified)
│   ├── test/                 # Test Patch (500个, 来自SWE-bench_Verified)
│   ├── agentless/            # Agentless方法生成的patch
│   ├── claude/               # Claude方法生成的patch
│   └── model/                # Model Patch（向后兼容，指向agentless）
├── siflow_config.py          # SiFlow配置
├── siflow_utils.py           # SiFlow工具函数
├── requirements.txt          # Python依赖
└── README.md                 # 本文档
```

## 三层Docker镜像架构

```
Layer 1: Base (swebench-base:2.0.0)
  └─ Ubuntu + git + build-essential + Miniconda3
     ↓
Layer 2: Environment (swebench-env-{repo}-{version}:2.0.0)
  └─ Python环境 + 项目依赖（按repo+version复用）
     ↓
Layer 3: Instance (swebench-instance-{instance_id}:2.0.0)
  └─ 克隆代码仓库 + 安装项目（每个instance独立）
```

**优势**：
- Layer1: 所有instance共享（~1个）
- Layer2: 按Python版本复用（~60个）
- Layer3: 每个instance独立（~500个）
- 总存储约100GB，构建时间大幅减少

### 镜像版本

- **2.0.0**: 标准版本（默认）
- **2.1.0**: 特殊版本，用于26个需要特殊处理的instances
  - 20个 sphinx-doc instances
  - 6个 django/pylint instances

## 快速开始

### 1. 构建镜像

```bash
cd build/

# 构建所有层级
python build_all_images.py --layer all --version 2.0.0

# 只构建Base层
python build_all_images.py --layer base --version 2.0.0

# 只构建Environment层
python build_all_images.py --layer env --version 2.0.0

# 只构建Instance层（可指定repo过滤）
python build_all_images.py --layer instance --version 2.0.0 --repo django
```

### 2. 运行评测

#### 方式1: 使用统一入口（推荐）

```bash
cd eval/

# 评测agentless方法（默认）
python run_eval.py <instance_id> --method agentless

# 评测claude方法
python run_eval.py <instance_id> --method claude

# 评测gold patch
python run_eval.py <instance_id> --method gold
```

#### 方式2: 使用专用脚本

```bash
cd eval/

# Gold Patch评测
python run_gold_eval_fixed.py <instance_id> --version 2.0.0 --wait

# 通用Patch评测（支持--method参数）
python run_model_eval.py <instance_id> --method agentless
```

### 3. Patch格式和存储

#### 支持的Patch格式

**1. 标准git diff格式**
```
--- a/path/to/file.py
+++ b/path/to/file.py
@@ -10,3 +10,4 @@
 existing line
+new line
```

**2. Agentless SEARCH/REPLACE格式**
```python
### path/to/file.py
<<<<<<< SEARCH
old code
=======
new code
>>>>>>> REPLACE
```

#### Patch文件存储位置

所有patch文件统一存储在 `patches/` 目录下：

```
patches/
├── gold/                    # Gold Patch (来自SWE-bench_Verified)
│   └── {instance_id}.diff
├── test/                    # Test Patch (来自SWE-bench_Verified)
│   └── {instance_id}.diff
├── agentless/               # Agentless方法生成的patch
│   └── {instance_id}.agentless_raw
├── claude/                  # Claude方法生成的patch
│   └── {instance_id}.diff
└── {other_method}/          # 其他方法的patch
    └── {instance_id}.{ext}
```

#### 评测日志存储位置

每个方法的评测日志存储在对应的目录：

```
{method}_patch_logs/
├── agentless_patch_logs/
│   └── {instance_id}_test_output.txt
├── claude_patch_logs/
│   └── {instance_id}_test_output.txt
└── gold_patch_logs/
    └── {instance_id}_test_output.txt
```

## SWE-bench Resolve逻辑

评测结果判定：
- **RESOLVED_FULL**: FAIL_TO_PASS全部通过 + PASS_TO_PASS全部保持通过
- **RESOLVED_PARTIAL**: 部分FAIL_TO_PASS通过
- **RESOLVED_NO**: 测试失败

## 配置新方法

### 1. 添加方法配置

编辑 `eval/method_config.py`，添加新方法：

```python
METHOD_CONFIGS = {
    "your_method": {
        "name": "your_method",
        "display_name": "Your Method",
        "file_extensions": [".diff", ".patch"],  # 支持的扩展名
        "format_type": "diff",  # 格式类型（"diff"或"agentless"）
        "log_dir": "your_method_patch_logs",  # 日志目录
        "task_prefix": "ym",  # SiFlow任务名前缀
        "description": "Your method description"
    }
}
```

### 2. 放置Patch文件

将patch文件放到对应目录：
```bash
mkdir -p patches/your_method
cp your_patches/*.diff patches/your_method/
```

### 3. 运行评测

```bash
cd eval/
python run_eval.py <instance_id> --method your_method
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

## 配置说明

### siflow_config.py
```python
RESOURCE_POOL = "ai-infra"      # 资源池
INSTANCE_TYPE = "4c8g"          # 实例类型
EVAL_TIMEOUT = 1800             # 评测超时（秒）
```

### method_config.py
```python
METHOD_CONFIGS = {
    "agentless": {...},  # Agentless方法配置
    "claude": {...},     # Claude方法配置
    "gold": {...},       # Gold Patch配置
}
```

### 环境变量
- `SIFLOW_BASE_URL`: SiFlow API地址
- `SIFLOW_TOKEN`: SiFlow访问令牌

## 依赖

```bash
pip install -r requirements.txt
```

主要依赖：
- siflow SDK
- datasets (HuggingFace)
- swebench
