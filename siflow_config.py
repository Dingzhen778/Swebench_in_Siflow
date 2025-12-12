"""
SiFlow 配置常量
"""

# SiFlow 连接配置
REGION = "cn-shanghai"
CLUSTER = "hercules"
ACCESS_KEY_ID = "7d84eb9a-1b36-4729-94d7-75a9fc5c093e"
ACCESS_KEY_SECRET = "UIjoX0ianEdQWGPR2r"
RESOURCE_POOL = "cn-shanghai-hercules-ai-infra-ondemand-shared"

# 实例类型
INSTANCE_TYPE = "sci.c23-2"

# Dockerfiles 路径
DOCKERFILE_BASE_DIR = "/volume/ai-infra/rhjiang/SWE-bench-cc/docker_build/dockerfiles"
DOCKERFILE_BASE_PATH = f"{DOCKERFILE_BASE_DIR}/base/Dockerfile"
DOCKERFILE_ENV_DIR = f"{DOCKERFILE_BASE_DIR}/env"
DOCKERFILE_VERIFIED_DIR = f"{DOCKERFILE_BASE_DIR}/verified"  # SWE-bench Verified 专用
DOCKERFILE_INSTANCE_DIR = f"{DOCKERFILE_BASE_DIR}/instance"
INSTANCE_ENV_MAPPING_FILE = f"{DOCKERFILE_BASE_DIR}/instance_env_mapping.json"

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
