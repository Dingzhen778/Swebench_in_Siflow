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
│   ├── run_gold_eval_fixed.py    # Gold Patch评测
│   ├── run_model_eval.py         # Model Patch评测
│   ├── apply_agentless.py        # Agentless格式应用
│   └── agentless_parser.py       # Agentless格式解析
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

```bash
cd eval/

# Gold Patch评测（单个instance）
python run_gold_eval_fixed.py <instance_id> --version 2.0.0 --wait

# Model Patch评测（单个instance）
python run_model_eval.py <instance_id> --version 2.0.0 --wait
```

### 3. Patch格式

支持两种patch格式：

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

Model Patch放置位置：
- 标准格式: `predictions/model/{instance_id}.diff`
- Agentless格式: `predictions/model/{instance_id}.agentless_raw`

## SWE-bench Resolve逻辑

评测结果判定：
- **RESOLVED_FULL**: FAIL_TO_PASS全部通过 + PASS_TO_PASS全部保持通过
- **RESOLVED_PARTIAL**: 部分FAIL_TO_PASS通过
- **RESOLVED_NO**: 测试失败

## 配置说明

### siflow_config.py
```python
RESOURCE_POOL = "ai-infra"      # 资源池
INSTANCE_TYPE = "4c8g"          # 实例类型
EVAL_TIMEOUT = 1800             # 评测超时（秒）
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
