# 镜像版本迁移方案 - 零风险迁移

## 策略：渐进式替换

**目标**: 每个instance只保留一个2.0.0版本镜像（包含所有修复）

**方案**: 先删除旧2.0.0，用2.1.0服务，然后重建新2.0.0，最后删除2.1.0

## 当前状态

### 镜像分布
- 总镜像数: 523个
- 单版本instances: 473个（只有2.0.0）
- 双版本instances: 25个（同时有2.0.0和2.1.0）

### 双版本instances (25个)
**已在INSTANCE_FIXES中配置:**
```
sphinx-doc instances (20个):
  7440, 7454, 7462, 7590, 7748, 7757, 7889, 7910, 7985
  8035, 8056, 8120, 8269, 8459, 8475, 8548, 8551, 8638
  10323, 10435

django instances (4个):
  10880, 10914, 11276, 15103

xarray instance (1个):
  6938
```

### 已删除2.1.0的instances (8个) - 现在只用2.0.0
```
scikit-learn (7个): 25102, 25232, 25747, 25931, 25973, 26194, 26323
astropy (1个): 7606
```

## 迁移步骤

### 步骤1: 删除旧2.0.0镜像 (25个) ⏳

**要删除的2.0.0镜像ID:**
```
2541  django-django-10880:2.0.0
2542  django-django-10914:2.0.0
2560  django-django-11276:2.0.0
2831  django-django-15103:2.0.0
2967  sphinx-doc-sphinx-10323:2.0.0
2968  sphinx-doc-sphinx-10435:2.0.0
2975  sphinx-doc-sphinx-7440:2.0.0
2976  sphinx-doc-sphinx-7454:2.0.0
2977  sphinx-doc-sphinx-7462:2.0.0
2978  sphinx-doc-sphinx-7590:2.0.0
2979  sphinx-doc-sphinx-7748:2.0.0
2980  sphinx-doc-sphinx-7757:2.0.0
2981  sphinx-doc-sphinx-7889:2.0.0
2982  sphinx-doc-sphinx-7910:2.0.0
2983  sphinx-doc-sphinx-7985:2.0.0
2984  sphinx-doc-sphinx-8035:2.0.0
2985  sphinx-doc-sphinx-8056:2.0.0
2986  sphinx-doc-sphinx-8120:2.0.0
2988  sphinx-doc-sphinx-8269:2.0.0
2989  sphinx-doc-sphinx-8459:2.0.0
2990  sphinx-doc-sphinx-8475:2.0.0
2991  sphinx-doc-sphinx-8548:2.0.0
2992  sphinx-doc-sphinx-8551:2.0.0
2996  sphinx-doc-sphinx-8638:2.0.0
3098  pydata-xarray-6938:2.0.0
```

**执行方式**: 联系SiFlow管理员手动删除

**结果**:
- 这25个instances临时只有2.1.0版本
- 评估系统自动使用2.1.0（fix_build_issues.py配置）
- 其他473个instances不受影响

### 步骤2: 重新构建2.0.0镜像 (25个) ⏳

**构建命令:**
```bash
# 使用build_all_images.py重新构建这25个instances
# 关键：构建时INSTANCE_FIXES配置生效，包含所有修复

python build_all_images.py \
  --layer instance \
  --version 2.0.0 \
  --env-version 2.0.0 \
  --instances-file instances_to_rebuild.json \
  --force  # 强制重建
```

**instances_to_rebuild.json内容:**
```json
[
  {"instance_id": "sphinx-doc__sphinx-7440", "repo": "sphinx-doc/sphinx", "version": "3.0"},
  {"instance_id": "sphinx-doc__sphinx-7454", "repo": "sphinx-doc/sphinx", "version": "3.0"},
  ...
  {"instance_id": "django__django-10880", "repo": "django/django", "version": "3.0"},
  ...
  {"instance_id": "pydata__xarray-6938", "repo": "pydata/xarray", "version": "0.12"}
]
```

**构建逻辑验证:**
- `build_layer3_instance.py` 会调用 `should_apply_fix()`
- 应用环境变量修复 (`get_env_vars()`)
- 应用install命令修复 (`get_install_cmd_fix()`)
- 应用environment_setup_commit逻辑

**预期结果:**
- 新2.0.0镜像包含所有修复（等价于之前的2.1.0）
- 这25个instances同时有2.0.0和2.1.0版本

### 步骤3: 验证新2.0.0镜像 ✅

**验证方法:**
```bash
# 对比测试：同一个instance分别用2.0.0和2.1.0评估
# 应该得到相同结果

# 测试新2.0.0版本
python run_gold_eval_fixed.py \
  --instance sphinx-doc__sphinx-7440 \
  --version 2.0.0

# 测试旧2.1.0版本
python run_gold_eval_fixed.py \
  --instance sphinx-doc__sphinx-7440 \
  --version 2.1.0

# 比较结果应该一致
```

**验证清单:**
- [ ] sphinx-doc__sphinx-7440 (2.0.0 vs 2.1.0)
- [ ] django__django-10880 (2.0.0 vs 2.1.0)
- [ ] pydata__xarray-6938 (2.0.0 vs 2.1.0)

### 步骤4: 删除2.1.0镜像 (25个) ⏳

**验证通过后，删除2.1.0镜像ID:**
```
3126-3150 (共25个)
```

### 步骤5: 更新代码 ✅

修改`run_gold_eval_fixed.py`:
```python
def get_image_version_for_instance(instance_id: str) -> str:
    """统一使用2.0.0版本"""
    return "2.0.0"
```

## 风险分析

### ✅ 零风险点
1. **步骤1**: 删除旧2.0.0不影响服务（自动降级到2.1.0）
2. **步骤2**: 重建期间服务不中断（用2.1.0）
3. **步骤3**: 验证阶段可以回退

### ⚠️ 需要注意
1. **步骤2构建时间**: 25个instances，预计1-2小时
2. **依赖问题**: sphinx instances需要roman模块等
3. **并发限制**: 控制构建并发数（--delay 2秒）

## 执行时间表

| 步骤 | 操作 | 预计时间 | 负责人 |
|------|------|----------|--------|
| 1 | 删除25个旧2.0.0镜像 | 5分钟 | SiFlow管理员 |
| 2 | 重新构建25个新2.0.0镜像 | 1-2小时 | 自动构建 |
| 3 | 验证新镜像 | 30分钟 | 测试运行 |
| 4 | 删除25个2.1.0镜像 | 5分钟 | SiFlow管理员 |
| 5 | 更新代码 | 5分钟 | 代码提交 |

**总计**: ~2-3小时

## 回退方案

**如果步骤3验证失败:**
1. 保留2.1.0镜像继续服务
2. 删除新构建的有问题的2.0.0镜像
3. 分析构建问题，修复后重试步骤2

## 最终状态

- ✅ 镜像总数: 498个
- ✅ 每个instance一个镜像
- ✅ 全部使用2.0.0版本
- ✅ 所有修复都在2.0.0镜像中
- ✅ 代码逻辑简化（单版本）

---

**创建日期**: 2025-12-11
**状态**: 待执行
**优先级**: 中
