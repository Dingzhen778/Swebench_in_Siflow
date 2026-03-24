# 当前进度与问题上下文

> 最后更新：2026-03-24

---

## 当前问题

### ModuleNotFoundError: No module named 'minisweagent'

**现象**：提交 SiFlow Task 后，Step 1（generate patch）立即报错：
```
File "<runner>", line 13, in <module>
ModuleNotFoundError: No module named 'minisweagent'
```

**根因**：
`run_generate_and_eval.py` 在容器内通过 `sys.path.insert(0, MINI_SWE_SRC)` 加载 mini-swe-agent，其中：
```python
MINI_SWE_SRC = "/volume/ai-infra/rhjiang/Swebench_in_Siflow/mini-swe-agent/src"
```
但 aries 上的 swebench-instance 容器**没有挂载 `/volume/ai-infra`**（aries inline 模式不挂 volume），所以找不到 minisweagent 包。

**解决方案（待执行）**：
将本项目代码（含 mini-swe-agent submodule）放到 aries 对应的 volume 下（如 `/volume/hisys-data/rhjiang/` 或类似路径），
让容器能通过 volume 挂载访问到 `/volume/...` 路径。

确认挂载路径后，更新 `MINI_SWE_SRC` 常量即可。

---

## 整体架构

```
本机（控制节点）                    aries 集群（SciTix）
─────────────────              ─────────────────────────────────────
run_generate_and_eval.py  →    SiFlow Task（swebench-instance 容器）
  提交 Task                      ├── Step 1: mini-swe-agent 生成 patch
  轮询状态                        │     调用 Qwen3-30B API
  查看结果                        ├── Step 2: git apply patch
                                  ├── Step 3: pip install -e .
                                  ├── Step 4: reset + apply test patch
                                  └── Step 5: 运行测试，exit 0=RESOLVED
```

**关键设计**：
- 生成 + 评测合并在一个 Task 里（避免 patch 传递问题）
- patch 以 base64 打印到 stdout（`PATCH_BEGIN_B64`/`PATCH_END_B64` 标记），可从日志手动提取
- Task exit_code = 0 → 测试通过 = RESOLVED

---

## 文件结构

```
Swebench_in_Siflow/
├── mini-swe-agent/          ← git submodule（SWE-agent/mini-swe-agent）
│   └── src/minisweagent/    ← 需要在 aries 容器内可访问
├── patch_gen/
│   ├── run_generate_and_eval.py   ← 主入口：提交合并 Task（生成+评测）
│   ├── generate_patch.py          ← 本地运行版本（需要 /testbed，备用）
│   ├── generate_patch_siflow_backup.py  ← 旧版 siflow 提交方式（备份）
│   └── run_and_eval.py            ← 分步版（先生成再 eval）
├── eval/
│   ├── method_config.py     ← 已添加 qwen3_30b 方法
│   ├── run_model_eval.py    ← eval 主入口（--method qwen3_30b）
│   └── run_gold_eval_fixed.py  ← eval 核心逻辑（aries inline 模式）
├── build/
│   └── fix_build_issues.py  ← get_env_vars()
├── siflow_config.py
├── siflow_utils.py
└── .env                     ← SIFLOW_ACCESS_KEY_ID/SECRET
```

---

## 关键常量（run_generate_and_eval.py）

```python
MINI_SWE_SRC        = "/volume/ai-infra/rhjiang/Swebench_in_Siflow/mini-swe-agent/src"
# ↑ 这是当前路径，容器内无法访问（未挂载）。
# 移到 aries volume 后改成对应路径，例如：
# MINI_SWE_SRC = "/volume/hisys-data/rhjiang/Swebench_in_Siflow/mini-swe-agent/src"

ARIES_RESOURCE_POOL = "ap-southeast-aries-hisys-ondemand-shared"
ARIES_INSTANCE_TYPE = "sci.c23-2"
IMAGE_VERSION       = "1.0.0"
DEFAULT_MODEL       = "openai/Qwen/Qwen3-30B-A3B-mcore"
DEFAULT_API_BASE    = "https://scitix-aries.scitix.ai/siflow/aries/hisys/rhjiang/qwen3-30b-a3b-mcore/v1"
```

---

## 已解决的历史问题

| 问题 | 解决方案 |
|------|----------|
| 本机无 /testbed，agent 找不到代码库 | 改为在 aries swebench-instance 容器内运行 |
| bash -lc '...' 内用 python3 -c "..." 引号冲突 | 改用 heredoc `<<"PY"` |
| volume 写回失败（容器内写 /volume 不可见） | 放弃 volume 写回，patch 通过 stdout base64 打印 |
| IMAGE_VERSION=2.0.0 找不到 | 改为 1.0.0 |
| tool_call 格式失败（模型输出 <think> 块） | 用 LitellmTextbasedModel + backticks 格式 |
| minisweagent 模块找不到 | **待解决**：需 aries volume 挂载 |

---

## 下一步

1. **将本项目移到 aries 对应的 volume 目录**（用户操作）
2. **更新 `MINI_SWE_SRC` 常量**到新路径（一行修改）
3. **重新提交两个测试 Task**（django__django-13837 / 13670）
4. 验证后批量跑全部 500 个实例

---

## 已提交的测试 Task（均失败，原因：module not found）

| 实例 | Task UUID | 状态 |
|------|-----------|------|
| django__django-13837 | c5ccefad-69ff-4304-ab7e-875e976ab1ba | Failed（引号bug） |
| django__django-13670 | 8d717299-ae40-4917-83d1-c8d2afcd421f | Failed（引号bug） |
| django__django-13837 | 31aa3657-d3fc-4311-94e9-43c75d45a1aa | Failed（module not found） |
| django__django-13670 | 6ba4ba19-ef47-4f25-a3ee-b4239fddf88d | Failed（module not found） |
