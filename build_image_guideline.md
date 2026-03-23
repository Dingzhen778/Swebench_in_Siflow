# SWE-bench 镜像全量构建指南（支持 aries / cetus）

## 1. 目标与数量

基于 `princeton-nlp/SWE-bench_Verified` 的 500 个 test instances：

- `base`: 1 个（`swebench-base:1.0.0`）
- `env`: 按 `(repo, version)` 去重，当前为 **80** 个
- `instance`: 每个 instance 1 个，共 **500** 个

总镜像数：

`1(base) + 80(env) + 500(instance) = 581`

说明：版本与已构建镜像对齐，统一 `1.0.0`。

## 2. 三层构建逻辑

1. Layer1 `base`
2. Layer2 `env`（repo-version 级）
3. Layer3 `instance`（样本级）

CodeRL sandbox 运行使用 `instance` 镜像；`env/base` 被复用。

## 3. 集群区分（必须）

构建阶段和训练阶段都要区分平台，不是只在训练时区分。

- `aries`（SciTix）：`ap-southeast / aries`
- `cetus`：`cn-shanghai / cetus`

脚本入口统一：

- `build_docker_in_scitix/build_all_images_in_scitix.py`
- `build_docker_in_scitix/continue_build_with_progress.py`

都支持 `--platform aries|cetus`，并自动注入对应 `region/cluster/resource_pool`。

## 4. 正确的提交顺序

不要一次 `--layer all` 后立即冲 instance。正确顺序是：

1. 先提交 `base/env`
2. 等待 env 可用（`registry_url` 非空）
3. 再提交 `instance`

否则会出现：`Environment image not found`。

## 5. 推荐命令

### 5.1 提交 base + env（aries）

```bash
cd /volume/ai-infra/rhjiang/Swebench_in_Siflow
/minconda3/envs/swebench_scitix/bin/python \
  build_docker_in_scitix/build_all_images_in_scitix.py \
  --platform aries \
  --layer env \
  --version 1.0.0 \
  --env-version 1.0.0 \
  --delay 1
```

### 5.2 继续提 instance（单次最多 24）

```bash
cd /volume/ai-infra/rhjiang/Swebench_in_Siflow/build_docker_in_scitix
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

## 6. `DeadlineExceeded` 处理

典型日志：

`error: failed to solve: DeadlineExceeded: context deadline exceeded`

该类问题常见于镜像导出/上传阶段超时。处理策略：

- 不直接继续提 instance
- 使用 `continue_build_with_progress.py`：
1. 先等待 env ready
2. 超时后自动重提 env（`--retry-env-submit`）
3. env ready 后再提 instance

注意：如果平台返回
`cannot register duplicate image: an active image with name ... already exists`，
说明同名同版本镜像已处于 `active`，无法重复注册。此时只能：

1. 继续等待该 `active` 镜像转为可用；或
2. 在平台侧清理/终止该卡住任务后再重提。

## 7. 进度与验收

进度文件：

- `build_docker_in_scitix/build_progress.md`
- `build_docker_in_scitix/build_progress_last_run.json`

验收口径：

- `base=1`
- `env=80` 且可用（有 `registry_url`）
- `instance=500`（可分批补齐）
