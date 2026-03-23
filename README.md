# SWE-bench SiFlow Evaluation System

基于 SiFlow 平台的 SWE-bench 完整评测系统，集成 **mini-swe-agent** 自动生成 patch，再通过三层 Docker 镜像架构在 SiFlow 上评测。

## 整体工作流

```
① 构建镜像（一次性）        ② 生成 Patch                ③ 评测
build/ 三层 Docker 镜像  →  patch_gen/ mini-swe-agent  →  eval/ SiFlow 评测
                                      ↓
                             patches/{method}/*.diff
```

## 目录结构

```
Swebench_in_Siflow/
├── mini-swe-agent/             # ★ submodule: mini-swe-agent agent 框架
│   └── src/minisweagent/       #   DefaultAgent / LitellmModel / LocalEnvironment ...
├── patch_gen/                  # ★ Patch 生成模块（新增）
│   ├── generate_patch.py       #   单/批量 patch 生成入口
│   └── run_and_eval.py         #   端到端：生成 + eval 一键运行
├── build/                      # 镜像构建
│   ├── build_all_images.py     #   批量构建入口
│   ├── build_layer1_base.py    #   Layer1: Base 镜像
│   ├── build_layer2_env.py     #   Layer2: Environment 镜像
│   ├── build_layer3_instance.py#   Layer3: Instance 镜像
│   ├── fix_build_issues.py     #   特殊实例构建修复
│   └── repo_version_to_python.py # 版本映射
├── build_docker_in_scitix/     # SciTix 平台专用构建脚本
├── eval/                       # 评测脚本
│   ├── run_model_eval.py       #   评测入口 (支持 model/gold)
│   ├── run_gold_eval_fixed.py  #   Gold 评测底层实现
│   └── method_config.py        #   方法配置
├── patches/                    # Patch 文件
│   ├── gold/                   #   Gold Patch (500 个)
│   ├── model/                  #   旧 Model Patch (Qwen2.5-72B)
│   └── {method}/               #   新方法生成的 patch（按 method 名命名）
├── logs/                       # 评测日志
├── siflow_config.py            # SiFlow 配置
└── siflow_utils.py             # 工具函数
```

## 三层 Docker 镜像架构

```
Layer 1: Base (swebench-base:2.0.0)
  └─ Ubuntu + git + Miniconda3
     ↓
Layer 2: Environment (swebench-env-{repo}-{version}:2.0.0)
  └─ Python 环境 + 项目依赖
     ↓
Layer 3: Instance (swebench-instance-{instance_id}:2.0.0)
  └─ 代码仓库 + 安装项目（代码位于 /testbed）
```

## 快速开始

### 0. 初始化
参考 `.env.template`，配置好 `.env`，使用 SiFlow 上的 key，具体资源参考官方文档。

安装依赖：

```bash
# SiFlow SDK（建议 0.2.9）
pip install siflow-0.2.9-py3-none-any.whl
pip install -U --target ./.vendor_siflow siflow-0.2.9-py3-none-any.whl

# mini-swe-agent（submodule，首次克隆后需初始化）
git submodule update --init --recursive
pip install -e mini-swe-agent/

# 其他依赖
pip install -r requirements.txt
```

安装 SiFlow SDK（建议 0.2.9）：

```bash
wget https://oss-cn-shanghai.siflow.cn/ai-infra-download/siflow-public/siflow-0.2.9-py3-none-any.whl
pip install siflow-0.2.9-py3-none-any.whl
```

如果脚本使用 `.vendor_siflow`（本项目很多脚本是这样），还需要同步安装到 vendor 目录：

```bash
pip install -U --target ./.vendor_siflow siflow-0.2.9-py3-none-any.whl
```

### 1. 构建镜像

```bash
cd build/
python build_all_images.py --layer all --version 2.0.0
```

### 1.1 在 SciTix 继续构建（区分 aries / cetus，先 env，再分批 instance）

推荐使用 `build_docker_in_scitix/continue_build_with_progress.py`，特点：
- 支持 `--platform aries|cetus`
- 先提交 env，再分批提交 instance
- 在提交 instance 前，强制等待 env 进入可用（`registry_url` 可取）
- env 长时间不可用时，支持自动重提（`--retry-env-submit`）
- 若平台返回 duplicate active（同名同版本已 active），需要等待其完成或先在平台侧清理后再重提
- 单次新增 instance 提交数强制不超过 `24`
- 进度写入 `build_docker_in_scitix/build_progress.md`

示例：

```bash
cd build_docker_in_scitix
/minconda3/envs/swebench_scitix/bin/python continue_build_with_progress.py \
  --platform aries \
  --image-version 1.0.0 \
  --env-version 1.0.0 \
  --max-new 24 \
  --batch-size 8 \
  --delay 1 \
  --env-ready-timeout 3600 \
  --env-ready-poll 30 \
  --retry-env-submit 1 \
  --preferred-repo django/django
```

全量提交通用入口（支持平台区分）：

```bash
/minconda3/envs/swebench_scitix/bin/python build_docker_in_scitix/build_all_images_in_scitix.py \
  --platform aries \
  --layer env \
  --version 1.0.0 \
  --env-version 1.0.0
```

### 1.5 安装 mini-swe-agent（首次）

本项目通过 git submodule 集成了 mini-swe-agent：

```bash
# 克隆项目时初始化 submodule
git submodule update --init --recursive

# 安装 mini-swe-agent 到当前 Python 环境
pip install -e mini-swe-agent/
```

### 2. 生成 Patch（mini-swe-agent）

使用 `patch_gen/generate_patch.py` 驱动模型生成 patch：

```bash
# 生成单个实例的 patch
python patch_gen/generate_patch.py \
    --instance django__django-13670 \
    --model openai/gpt-4o \
    --method my_model

# 批量生成（并发 4）
python patch_gen/generate_patch.py \
    --batch \
    --model openai/gpt-4o \
    --method my_model \
    --workers 4

# 使用兼容 OpenAI 协议的第三方 API
OPENAI_API_BASE=https://your-api.com/v1 \
OPENAI_API_KEY=your-key \
python patch_gen/generate_patch.py \
    --instance django__django-13670 \
    --model openai/your-model-name \
    --method my_model
```

生成的 patch 保存到 `patches/{method}/{instance_id}.diff`，自动兼容 eval 流水线。

### 2.1 一键生成 + 评测

```bash
# 单个实例：生成 patch 并立即评测
python patch_gen/run_and_eval.py \
    --instance django__django-13670 \
    --model openai/gpt-4o \
    --method my_model

# 批量端到端
python patch_gen/run_and_eval.py \
    --batch \
    --model openai/gpt-4o \
    --method my_model \
    --workers 4

# 只评测（patch 已在 patches/{method}/ 下）
python patch_gen/run_and_eval.py \
    --instance django__django-13670 \
    --model openai/gpt-4o \
    --method my_model \
    --eval-only
```

### 2.2 单独运行评测

```bash
cd eval/

# 评测已有 patch（model/gold/自定义方法）
python run_model_eval.py <instance_id> --method my_model

# Gold Patch 评测
python run_model_eval.py <instance_id> --method gold
```

### 2.1 集群差异（cetus vs aries）

`eval/run_gold_eval_fixed.py` 已内置集群分支：
- `cetus`（或非 aries）：沿用原流程，使用 volume 挂载（读取/写入宿主路径）
- `aries`：自动走 inline-no-volume 流程（不挂 volume，patch 以 base64 内联后写入容器 `/tmp/*.patch`）

因此在 `aries` 上只需要设置：

```bash
SIFLOW_REGION=ap-southeast
SIFLOW_CLUSTER=aries
SIFLOW_RESOURCE_POOL=ap-southeast-aries-hisys-ondemand-shared
```

然后直接运行：

```bash
python eval/run_gold_eval_fixed.py django__django-12754 --version 1.0.0 --wait
```

## 评测结果

| 方法 | Patch 来源 | RESOLVED | 总数 | 比例 |
|------|-----------|----------|------|------|
| model | Qwen2.5-72B | 126 | 480 | 26.3% |
| gold | SWE-bench 官方 | - | 500 | 基准 |

## Resolve 逻辑

- **RESOLVED_FULL**: FAIL_TO_PASS 全部通过 + PASS_TO_PASS 全部保持通过
- **RESOLVED_PARTIAL**: 部分 FAIL_TO_PASS 通过
- **RESOLVED_NO**: 测试失败

## mini-swe-agent 集成说明

- **submodule 路径**: `mini-swe-agent/`（来源：`git@github.com:SWE-agent/mini-swe-agent.git`）
- **运行环境**: `LocalEnvironment`（直接在宿主机/容器的 bash 中执行，工作目录 `/testbed`）
- **模型支持**: 通过 LiteLLM 支持 OpenAI、Anthropic、自定义兼容 API 等 100+ 模型
- **输出格式**: `patches/{method}/{instance_id}.diff`（标准 git diff，与现有 eval 流水线完全兼容）
- **轨迹日志**: `logs/{method}_patch/{instance_id}.traj.json`（含完整对话历史和 cost）
- **配置文件**: 默认使用 `mini-swe-agent/src/minisweagent/config/benchmarks/swebench.yaml`，可通过 `--config` 覆盖
