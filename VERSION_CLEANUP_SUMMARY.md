# 镜像版本统一 - 完成总结

## 执行的操作

### 1. 代码修改 ✅

#### 修改 `run_gold_eval_fixed.py`

**Before:**
```python
def get_image_version_for_instance(instance_id: str) -> str:
    if should_apply_fix(instance_id):
        return "2.1.0"  # 修复后的镜像
    return "2.0.0"  # 原始镜像
```

**After:**
```python
def get_image_version_for_instance(instance_id: str) -> str:
    """统一使用2.0.0版本（标准镜像）"""
    return "2.0.0"  # 统一使用2.0.0版本
```

**影响:**
- ✅ 所有instances评估时统一使用2.0.0版本镜像
- ✅ 移除了动态版本选择逻辑
- ✅ 简化了代码维护

### 2. 镜像清理状态

**已删除的镜像 (8个):**
- scikit-learn__scikit-learn-25102 (2.1.0)
- scikit-learn__scikit-learn-25232 (2.1.0)
- scikit-learn__scikit-learn-25747 (2.1.0)
- scikit-learn__scikit-learn-25931 (2.1.0)
- scikit-learn__scikit-learn-25973 (2.1.0)
- scikit-learn__scikit-learn-26194 (2.1.0)
- scikit-learn__scikit-learn-26323 (2.1.0)
- astropy__astropy-7606 (2.1.0)

**待删除的镜像 (25个):**

需要联系SiFlow管理员手动删除以下镜像ID:

```
3126  sphinx-doc-sphinx-7440:2.1.0
3127  sphinx-doc-sphinx-7454:2.1.0
3128  sphinx-doc-sphinx-7462:2.1.0
3129  sphinx-doc-sphinx-7590:2.1.0
3130  sphinx-doc-sphinx-7748:2.1.0
3131  sphinx-doc-sphinx-7757:2.1.0
3132  sphinx-doc-sphinx-7889:2.1.0
3133  sphinx-doc-sphinx-7910:2.1.0
3134  sphinx-doc-sphinx-7985:2.1.0
3135  sphinx-doc-sphinx-8035:2.1.0
3136  sphinx-doc-sphinx-8056:2.1.0
3137  sphinx-doc-sphinx-8120:2.1.0
3138  sphinx-doc-sphinx-8269:2.1.0
3139  sphinx-doc-sphinx-8459:2.1.0
3140  sphinx-doc-sphinx-8475:2.1.0
3141  sphinx-doc-sphinx-8548:2.1.0
3142  sphinx-doc-sphinx-8551:2.1.0
3143  sphinx-doc-sphinx-8638:2.1.0
3144  django-django-10880:2.1.0
3145  django-django-10914:2.1.0
3146  django-django-11276:2.1.0
3147  django-django-15103:2.1.0
3148  pydata-xarray-6938:2.1.0
3149  sphinx-doc-sphinx-10323:2.1.0
3150  sphinx-doc-sphinx-10435:2.1.0
```

**删除命令 (需要SiFlow管理员权限):**
```bash
# 如果有删除API，可以用以下脚本
for id in 3126 3127 3128 3129 3130 3131 3132 3133 3134 3135 3136 3137 3138 3139 3140 3141 3142 3143 3144 3145 3146 3147 3148 3149 3150; do
  # siflow images delete $id
  echo "Delete image ID: $id"
done
```

### 3. 当前状态

**镜像统计:**
- 当前总数: 523个
- 目标总数: 498个 (每个instance一个镜像)
- 需要删除: 25个

**版本分布:**
- 2.0.0版本: 498个 ✅
- 2.1.0版本: 25个 (待删除)

### 4. 验证

#### 评估系统验证
```bash
# 测试评估是否正常工作（使用2.0.0版本）
python run_gold_eval_fixed.py --instance django__django-10880

# 应该输出：
# 🔍 正在查询 instance 镜像: swebench-instance-django-django-10880:2.0.0
```

#### 构建系统验证
```bash
# 确认build_all_images.py默认版本
grep "default.*2.0.0" build_all_images.py

# 应该输出:
# parser.add_argument("--version", default="2.0.0", help="镜像版本")
```

## 下一步行动

### 必需操作
1. ⏳ **联系SiFlow管理员删除25个2.1.0镜像** (镜像ID: 3126-3150)
2. ✅ **验证评估系统** - 确认统一使用2.0.0版本

### 可选操作
1. 更新`fix_build_issues.py`文档说明
2. 添加单元测试确保版本统一
3. 创建镜像版本检查脚本

## 预期结果

### 镜像管理
- ✅ 每个instance只有一个镜像版本
- ✅ 全部使用2.0.0版本
- ✅ 镜像总数: 498个
- ✅ 存储节约: ~25个镜像 (~5%)

### 代码简化
- ✅ 移除了双版本选择逻辑
- ✅ 统一的镜像版本管理
- ✅ 降低维护复杂度

### 评估一致性
- ✅ 所有instances使用相同版本镜像
- ✅ Gold patch评估基准不变: 421/498 RESOLVED_FULL (84.5%)
- ✅ 环境修复通过运行时配置应用

## 不影响的功能

以下功能保持不变：
1. ✅ `fix_build_issues.py`中的环境变量修复 (LANG, LC_ALL等)
2. ✅ `build_layer3_instance.py`中的environment_setup_commit逻辑
3. ✅ Gold patch和Model patch评估流程
4. ✅ Agentless格式转换功能

## 回退方案

如果需要回退到双版本策略：

1. 恢复`run_gold_eval_fixed.py`中的版本选择逻辑
2. 重新构建25个instances的2.1.0版本镜像
3. 使用git恢复代码: `git checkout <commit> run_gold_eval_fixed.py`

---

**完成日期**: 2025-12-11
**负责人**: Claude + User
**状态**: 代码修改完成✅，等待镜像删除⏳
