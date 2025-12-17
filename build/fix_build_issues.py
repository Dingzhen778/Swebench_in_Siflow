#!/usr/bin/env python3
"""
修复instance构建和评测问题的补丁

修复的问题类型：
1. pip_too_old: 旧版本pip不支持--no-use-pep517参数
2. unicode_error: UnicodeEncodeError（容器默认ASCII编码）
3. p2p_env_issue: PASS_TO_PASS测试因环境差异失败
4. large_repo_clone: 大仓库git clone超时，需要用archive下载
5. setup_py_install: pip install失败，需要用setup.py develop
"""

# 需要特殊处理的instance和对应的修复方案
INSTANCE_FIXES = {
    # ============================================================================
    # 1. pip版本问题 - 移除--no-use-pep517参数
    # ============================================================================

    # scikit-learn instances (7个) - 已注释，v2.0.0版本已经可以正常工作
    # "scikit-learn__scikit-learn-26323": {
    #     "issue": "pip_too_old",
    #     "fix": "remove_no_use_pep517"
    # },
    # "scikit-learn__scikit-learn-26194": {
    #     "issue": "pip_too_old",
    #     "fix": "remove_no_use_pep517"
    # },
    # "scikit-learn__scikit-learn-25973": {
    #     "issue": "pip_too_old",
    #     "fix": "remove_no_use_pep517"
    # },
    # "scikit-learn__scikit-learn-25931": {
    #     "issue": "pip_too_old",
    #     "fix": "remove_no_use_pep517"
    # },
    # "scikit-learn__scikit-learn-25747": {
    #     "issue": "pip_too_old",
    #     "fix": "remove_no_use_pep517"
    # },
    # "scikit-learn__scikit-learn-25232": {
    #     "issue": "pip_too_old",
    #     "fix": "remove_no_use_pep517"
    # },
    # "scikit-learn__scikit-learn-25102": {
    #     "issue": "pip_too_old",
    #     "fix": "remove_no_use_pep517"
    # },

    # astropy 3.1 instances (2个) - git clone超时 + pip install失败
    # 解决方案: 用GitHub archive下载 + setup.py develop安装
    "astropy__astropy-8872": {
        "issue": "large_repo_clone + setup_py_install + numpy_compat",
        "fix": "use_archive_and_setup_py",
        "additional_fixes": ["inject_numpy_compat"],
        "note": "astropy 3.1: git clone timeout, pip install fails, use archive + setup.py develop"
    },
    "astropy__astropy-8707": {
        "issue": "large_repo_clone + setup_py_install + numpy_compat",
        "fix": "use_archive_and_setup_py",
        "additional_fixes": ["inject_numpy_compat", "fix_pytest_setup"],
        "note": "astropy 3.1: git clone timeout, pip install fails, use archive + setup.py develop"
    },

    # pylint instance (1个) - 需要pip修复 (测试参数问题在dataset层面)
    "pylint-dev__pylint-7277": {
        "issue": "pip_too_old",
        "fix": "remove_no_use_pep517",
        "note": "Issue #292: Dataset test parameter issue - requires dataset update"
    },

    # ============================================================================
    # 2. UnicodeEncodeError - 需要UTF-8环境变量 (20个)
    # ============================================================================

    # Sphinx instances (18个)
    "sphinx-doc__sphinx-7440": {
        "issue": "unicode_error",
        "fix": "set_utf8_env"
    },
    "sphinx-doc__sphinx-7454": {
        "issue": "unicode_error",
        "fix": "set_utf8_env"
    },
    "sphinx-doc__sphinx-7462": {
        "issue": "unicode_error",
        "fix": "set_utf8_env"
    },
    "sphinx-doc__sphinx-7590": {
        "issue": "unicode_error",
        "fix": "set_utf8_env"
    },
    "sphinx-doc__sphinx-7748": {
        "issue": "unicode_error",
        "fix": "set_utf8_env"
    },
    "sphinx-doc__sphinx-7757": {
        "issue": "unicode_error",
        "fix": "set_utf8_env"
    },
    "sphinx-doc__sphinx-7889": {
        "issue": "unicode_error",
        "fix": "set_utf8_env"
    },
    "sphinx-doc__sphinx-7910": {
        "issue": "unicode_error",
        "fix": "set_utf8_env"
    },
    "sphinx-doc__sphinx-7985": {
        "issue": "unicode_error",
        "fix": "set_utf8_env"
    },
    "sphinx-doc__sphinx-8035": {
        "issue": "unicode_error",
        "fix": "set_utf8_env"
    },
    "sphinx-doc__sphinx-8056": {
        "issue": "unicode_error",
        "fix": "set_utf8_env"
    },
    "sphinx-doc__sphinx-8120": {
        "issue": "unicode_error",
        "fix": "set_utf8_env"
    },
    "sphinx-doc__sphinx-8269": {
        "issue": "unicode_error",
        "fix": "set_utf8_env"
    },
    "sphinx-doc__sphinx-8459": {
        "issue": "unicode_error",
        "fix": "set_utf8_env"
    },
    "sphinx-doc__sphinx-8475": {
        "issue": "unicode_error",
        "fix": "set_utf8_env"
    },
    "sphinx-doc__sphinx-8548": {
        "issue": "unicode_error",
        "fix": "set_utf8_env"
    },
    "sphinx-doc__sphinx-8551": {
        "issue": "unicode_error",
        "fix": "set_utf8_env"
    },
    "sphinx-doc__sphinx-8638": {
        "issue": "unicode_error",
        "fix": "set_utf8_env"
    },

    # Django instances (2个)
    "django__django-10880": {
        "issue": "unicode_error",
        "fix": "set_utf8_env"
    },
    "django__django-10914": {
        "issue": "unicode_error",
        "fix": "set_utf8_env"
    },

    # ============================================================================
    # 3. PASS_TO_PASS环境问题 (6个)
    # ============================================================================

    # Django P2P failures
    "django__django-11276": {
        "issue": "p2p_env_issue",
        "fix": "set_utf8_env",  # 可能也是编码问题
        "note": "F2P: 26/26, P2P: 546/548 - 2个P2P测试失败"
    },
    "django__django-15103": {
        "issue": "p2p_env_issue",
        "fix": "set_utf8_env",
        "note": "F2P: 2/2, P2P: 15/17 - 2个P2P测试失败"
    },

    # Xarray P2P failure
    "pydata__xarray-6938": {
        "issue": "p2p_env_issue",
        "fix": "set_utf8_env",
        "note": "F2P: 1/1, P2P: 429/430 - 1个P2P测试失败"
    },

    # Sphinx P2P failures
    "sphinx-doc__sphinx-10323": {
        "issue": "p2p_env_issue",
        "fix": "set_utf8_env",
        "note": "F2P: 1/1, P2P: 38/40 - 2个P2P测试失败"
    },
    "sphinx-doc__sphinx-10435": {
        "issue": "p2p_env_issue",
        "fix": "set_utf8_env",
        "note": "F2P: 0/1, P2P: 74/74 - F2P未通过"
    },

    # Astropy leap-second issue - 已注释，v2.0.0版本可以正常工作
    # "astropy__astropy-7606": {
    #     "issue": "p2p_env_issue",
    #     "fix": "set_utf8_env",
    #     "note": "leap-second文件过期"
    # },
}


def get_env_vars(instance_id: str) -> dict:
    """
    获取需要添加的环境变量

    Args:
        instance_id: 实例ID

    Returns:
        环境变量字典 {var_name: value}
    """
    if instance_id not in INSTANCE_FIXES:
        return {}

    fix_info = INSTANCE_FIXES[instance_id]

    if fix_info["fix"] == "set_utf8_env":
        # 设置UTF-8编码环境变量，解决UnicodeEncodeError
        return {
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PYTHONIOENCODING": "utf-8"
        }

    return {}


def get_pre_install_fix(instance_id: str, original_pre_install: list) -> list:
    """
    获取修复后的pre_install命令列表

    Args:
        instance_id: 实例ID
        original_pre_install: 原始pre_install列表

    Returns:
        修复后的pre_install列表
    """
    if instance_id not in INSTANCE_FIXES:
        return original_pre_install

    # 对于所有修复，保持原始pre_install不变
    # environment_setup_commit会处理NumPy兼容性等问题
    return original_pre_install


def get_install_cmd_fix(instance_id: str, original_install_cmd: str) -> str:
    """
    获取修复后的install命令

    Args:
        instance_id: 实例ID
        original_install_cmd: 原始install命令

    Returns:
        修复后的install命令
    """
    if instance_id not in INSTANCE_FIXES:
        return original_install_cmd

    fix_info = INSTANCE_FIXES[instance_id]

    if fix_info["fix"] == "remove_no_use_pep517":
        # 移除--no-use-pep517参数（旧版本pip不支持）
        # 同时移除-e参数（旧版本setuptools不支持PEP 660 build_editable hook）
        fixed_cmd = original_install_cmd
        fixed_cmd = fixed_cmd.replace('--no-use-pep517 ', '')
        fixed_cmd = fixed_cmd.replace(' --no-use-pep517', '')
        # 移除 -e 参数，改为普通安装
        fixed_cmd = fixed_cmd.replace(' -e ', ' ')
        fixed_cmd = fixed_cmd.replace('install -e ', 'install ')
        return fixed_cmd

    return original_install_cmd


def should_apply_fix(instance_id: str) -> bool:
    """检查是否需要应用补丁"""
    return instance_id in INSTANCE_FIXES


def get_fix_info(instance_id: str) -> dict:
    """获取补丁信息"""
    return INSTANCE_FIXES.get(instance_id, {})


def uses_archive_download(instance_id: str) -> bool:
    """检查是否需要用GitHub archive下载代替git clone（大仓库超时问题）"""
    if instance_id not in INSTANCE_FIXES:
        return False
    fix_info = INSTANCE_FIXES[instance_id]
    return fix_info.get("fix") == "use_archive_and_setup_py"


def uses_setup_py_install(instance_id: str) -> bool:
    """检查是否需要用setup.py develop代替pip install"""
    if instance_id not in INSTANCE_FIXES:
        return False
    fix_info = INSTANCE_FIXES[instance_id]
    return fix_info.get("fix") == "use_archive_and_setup_py"


def get_test_patch_fix(instance_id: str, original_test_patch: str) -> str:
    """
    获取修复后的test_patch

    对于需要注入NumPy兼容性代码或pytest修复的实例,在test_patch开头添加修复代码

    Args:
        instance_id: 实例ID
        original_test_patch: 原始test_patch内容

    Returns:
        修复后的test_patch内容
    """
    if instance_id not in INSTANCE_FIXES:
        return original_test_patch

    fix_info = INSTANCE_FIXES[instance_id]
    additional_fixes = fix_info.get("additional_fixes", [])

    if not additional_fixes:
        return original_test_patch

    # 构建注入代码
    injected_code = []

    if "inject_numpy_compat" in additional_fixes:
        # NumPy 1.24+ 兼容性修复 (来自 SWE-bench issue #484)
        numpy_compat = '''--- a/conftest.py
+++ b/conftest.py
@@ -1,3 +1,15 @@
+# NumPy 1.24+ compatibility fix for removed type aliases
+# Reference: https://github.com/SWE-bench/SWE-bench/issues/484
+import sys
+try:
+    import numpy as np
+    if not hasattr(np, 'int'):
+        np.int = int
+    if not hasattr(np, 'float'):
+        np.float = float
+    if not hasattr(np, 'bool'):
+        np.bool = bool
+except ImportError:
+    pass
+
 # ... existing conftest.py content ...
'''
        injected_code.append(numpy_compat)

    if "fix_pytest_setup" in additional_fixes:
        # pytest 7.4+ 不支持nose风格setup (来自 SWE-bench issue #484)
        # 这个修复需要修改具体的测试文件,暂时通过conftest.py添加兼容性处理
        pytest_compat = '''--- a/conftest.py
+++ b/conftest.py
@@ -1,3 +1,20 @@
+# pytest 7.4+ compatibility for nose-style setup/teardown
+# Reference: https://github.com/SWE-bench/SWE-bench/issues/484
+import pytest
+
+# Monkey patch to support nose-style setup(self) methods
+def _wrap_nose_setup(original_setup):
+    def setup_method(self, method):
+        return original_setup(self)
+    return setup_method
+
+def _wrap_nose_teardown(original_teardown):
+    def teardown_method(self, method):
+        return original_teardown(self)
+    return teardown_method
+
+pytest.TestCase.setup_method = property(lambda self: _wrap_nose_setup(self.setup) if hasattr(self, 'setup') else None)
+
 # ... existing conftest.py content ...
'''
        injected_code.append(pytest_compat)

    if injected_code:
        # 将注入代码添加到test_patch开头
        # 注意: 这是一个简化的实现,实际上需要更复杂的patch合并逻辑
        # 对于实际使用,可能需要直接修改conftest.py文件
        return '\n'.join(injected_code) + '\n\n' + original_test_patch

    return original_test_patch
