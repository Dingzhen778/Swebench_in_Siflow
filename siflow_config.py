"""
SiFlow 配置常量
"""
import os

# 项目根目录配置
# 可以通过环境变量 SWEBENCH_PROJECT_ROOT 覆盖
# 默认使用当前配置文件所在目录（3-layer-test目录）
PROJECT_ROOT = os.environ.get("SWEBENCH_PROJECT_ROOT",
                               os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.abspath(PROJECT_ROOT)  # 确保是绝对路径

# SiFlow 连接配置
REGION = "cn-shanghai"
CLUSTER = "hercules"
ACCESS_KEY_ID = "7d84eb9a-1b36-4729-94d7-75a9fc5c093e"
ACCESS_KEY_SECRET = "UIjoX0ianEdQWGPR2r"
RESOURCE_POOL = "cn-shanghai-hercules-ai-infra-ondemand-shared"

# 实例类型
INSTANCE_TYPE = "sci.c23-2"

# 存储卷配置 (需要根据你的SiFlow账户配置修改)
# VOLUME_MOUNT_DIR: 存储卷在容器内的挂载路径
# VOLUME_ID: SiFlow平台上的存储卷ID
VOLUME_MOUNT_DIR = "/volume/ai-infra"
VOLUME_ID = 1

# 镜像命名规范
IMAGE_NAME_BASE = "swebench-base"
IMAGE_NAME_ENV_PREFIX = "swebench-env"
IMAGE_NAME_INSTANCE_PREFIX = "swebench"
IMAGE_VERSION = "1.0.0"

# 镜像分类
IMAGE_CATEGORY_MAJOR = "swebench"
IMAGE_CATEGORY_MINOR_BASE = "base"
IMAGE_CATEGORY_MINOR_ENV = "env"

# Registry URL 模板
REGISTRY_URL_TEMPLATE = "registry-cn-shanghai.siflow.cn/ai-infra/{image_name}:{version}-{commit_id}"

# 超时和重试配置
BUILD_TIMEOUT = 3600  # 1小时
BUILD_CHECK_INTERVAL = 30  # 30秒
QUERY_MAX_ERRORS = 5

# 批量操作配置
DEFAULT_MAX_WORKERS = 5
DEFAULT_BATCH_DELAY = 2.0
DEFAULT_BATCH_SIZE = 10

