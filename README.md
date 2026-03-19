# SWE-bench SiFlow Evaluation System

基于SiFlow平台的SWE-bench评测系统，采用三层Docker镜像架构。

## 目录结构

```
3-layer-test/
├── build/                      # 镜像构建
│   ├── build_all_images.py     # 批量构建入口
│   ├── build_layer1_base.py    # Layer1: Base镜像
│   ├── build_layer2_env.py     # Layer2: Environment镜像
│   ├── build_layer3_instance.py # Layer3: Instance镜像
│   ├── fix_build_issues.py     # 特殊实例构建修复
│   └── repo_version_to_python.py # 版本映射
├── eval/                       # 评测脚本
│   ├── run_model_eval.py       # 评测入口 (支持model/gold)
│   ├── run_gold_eval_fixed.py  # Gold评测(底层实现)
│   └── method_config.py        # 方法配置
├── patches/                    # Patch文件
│   ├── gold/                   # Gold Patch (500个)
│   ├── model/                  # Model Patch (500个, Qwen2.5-72B)
│   └── test/                   # Test Patch (运行时生成)
├── logs/                       # 评测日志
│   └── model_patch/            # Model评测日志
├── results/                    # 评测结果
│   ├── model_patch_478_results.csv
│   └── gold_patch_results.csv
├── siflow_config.py            # SiFlow配置
└── siflow_utils.py             # 工具函数
```

## 三层Docker镜像架构

```
Layer 1: Base (swebench-base:2.0.0)
  └─ Ubuntu + git + Miniconda3
     ↓
Layer 2: Environment (swebench-env-{repo}-{version}:2.0.0)
  └─ Python环境 + 项目依赖
     ↓
Layer 3: Instance (swebench-instance-{instance_id}:2.0.0)
  └─ 代码仓库 + 安装项目
```

## 快速开始

### 0.初始化
参考.env.template，配置好.env，使用siflow上的key，具体资源参考官方文档

### 1. 构建镜像

```bash
cd build/
python build_all_images.py --layer all --version 2.0.0
```

### 1.1 在 SciTix(aries) 继续构建（先 env，再分批 instance）

推荐使用 `build_docker_in_scitix/continue_build_with_progress.py`，特点：
- 固定 `ap-southeast/aries`
- 先提交 env，再分批提交 instance
- 单次新增 instance 提交数强制不超过 `24`
- 进度写入 `build_docker_in_scitix/build_progress.md`

示例：

```bash
cd build_docker_in_scitix
/minconda3/envs/swebench_scitix/bin/python continue_build_with_progress.py \
  --image-version 1.0.0 \
  --env-version 1.0.0 \
  --max-new 24 \
  --batch-size 8 \
  --delay 1 \
  --preferred-repo django/django
```

### 2. 运行评测

```bash
cd eval/

# Model Patch评测
python run_model_eval.py <instance_id> --method model

# Gold Patch评测
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

| 方法 | Patch来源 | RESOLVED | 总数 | 比例 |
|------|----------|----------|------|------|
| model | Qwen2.5-72B | 126 | 480 | 26.3% |
| gold | SWE-bench官方 | - | 500 | 基准 |

## Resolve逻辑

- **RESOLVED_FULL**: FAIL_TO_PASS全部通过 + PASS_TO_PASS全部保持通过
- **RESOLVED_PARTIAL**: 部分FAIL_TO_PASS通过
- **RESOLVED_NO**: 测试失败
