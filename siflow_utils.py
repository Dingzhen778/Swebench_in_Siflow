"""
SiFlow 通用工具函数
"""

import time
import json
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from siflow import SiFlow
from siflow_config import (
    REGION, CLUSTER, ACCESS_KEY_ID, ACCESS_KEY_SECRET,
    BUILD_TIMEOUT, BUILD_CHECK_INTERVAL, QUERY_MAX_ERRORS
)


def create_siflow_client() -> SiFlow:
    """创建 SiFlow 客户端"""
    return SiFlow(
        region=REGION,
        cluster=CLUSTER,
        access_key_id=ACCESS_KEY_ID,
        access_key_secret=ACCESS_KEY_SECRET
    )


def image_exists(client: SiFlow, image_name: str, version: str = "1.0.0") -> bool:
    """
    检查镜像是否存在（不管状态，只要记录存在就返回True）

    Args:
        client: SiFlow 客户端
        image_name: 镜像名称
        version: 镜像版本（精确匹配）

    Returns:
        镜像是否存在
    """
    try:
        # 不加image_build_type过滤，查询所有类型的镜像
        images = client.images.list(
            keyword=image_name,
            pageSize=100
        )

        if not images or not hasattr(images, 'rows'):
            return False

        for img in images.rows:
            img_name = getattr(img, 'name', '')
            img_version = getattr(img, 'version', '')

            # 精确匹配name和version
            if img_name == image_name and img_version == version:
                return True

        return False

    except Exception as e:
        # 静默失败
        return False


def get_image_registry_url(client: SiFlow, image_name: str, version: str = "1.0.0") -> Optional[str]:
    """
    获取镜像的 Registry URL

    Args:
        client: SiFlow 客户端
        image_name: 镜像名称
        version: 镜像版本（精确匹配）

    Returns:
        Registry URL 或 None
    """
    try:
        # 使用keyword搜索，但只接受精确匹配且版本正确的结果
        # 添加image_build_type="custom"过滤,只查找新版本镜像(有正确metadata)
        images = client.images.list(
            keyword=image_name,
            image_build_type="custom",
            pageSize=100
        )

        if not images or not hasattr(images, 'rows'):
            return None

        for img in images.rows:
            img_name = getattr(img, 'name', '')
            img_version = getattr(img, 'version', '')

            # 精确匹配name和version
            if img_name == image_name and img_version == version:
                cluster_urls = getattr(img, 'cluster_images_url', [])
                if cluster_urls:
                    # "上海集群请使用该URL: registry-cn-shanghai..."
                    url = cluster_urls[0]
                    if ': ' in url:
                        return url.split(': ')[-1]
                    return url

        return None

    except Exception as e:
        # 静默失败
        return None


def wait_for_image_build(
    client: SiFlow,
    image_name: str,
    image_id: Optional[int] = None,
    timeout: int = BUILD_TIMEOUT,
    check_interval: int = BUILD_CHECK_INTERVAL
) -> Dict:
    """
    等待镜像构建完成

    Args:
        client: SiFlow 客户端
        image_name: 镜像名称
        image_id: 镜像ID（可选）
        timeout: 超时时间（秒）
        check_interval: 检查间隔（秒）

    Returns:
        包含构建结果的字典
    """
    print(f"📌 等待镜像构建完成: {image_name}")
    print(f"   超时: {timeout}秒, 检查间隔: {check_interval}秒")
    print()

    start_time = time.time()
    last_status = None
    query_error_count = 0

    while time.time() - start_time < timeout:
        try:
            images = client.images.list(
                keyword=image_name,
                image_build_type="custom"
            )

            if images and len(images.rows) > 0:
                image = images.rows[0]

                # 检查构建状态
                build_status = getattr(image, 'image_build_status', None)
                build_message = getattr(image, 'image_build_message', None)
                current_status = f"{image.status}|{build_status}"

                if current_status != last_status:
                    elapsed = int(time.time() - start_time)
                    elapsed_min = elapsed // 60
                    elapsed_sec = elapsed % 60
                    print(f"   [{elapsed_min:02d}:{elapsed_sec:02d}] 状态: {image.status}, 构建: {build_status}")
                    if build_message:
                        print(f"              消息: {build_message}")
                    last_status = current_status

                # 检查是否成功
                if build_status == "Succeeded" or image.status == "success":
                    print()
                    print(f"✅ 镜像构建完成！")

                    # 获取镜像URL
                    image_url = None
                    if hasattr(image, 'cluster_images_url') and image.cluster_images_url:
                        for url in image.cluster_images_url:
                            if ": " in url:
                                image_url = url.split(": ")[-1]
                            else:
                                image_url = url
                            break

                    return {
                        "success": True,
                        "image_name": image.name,
                        "image_id": image.id,
                        "image_url": image_url,
                        "status": "completed",
                        "build_time": int(time.time() - start_time)
                    }

                # 检查是否失败
                elif build_status == "Failed" or image.status in ["failed", "error"]:
                    print()
                    print(f"❌ 镜像构建失败")
                    print(f"   状态: {image.status}")
                    print(f"   构建状态: {build_status}")
                    print(f"   消息: {build_message}")
                    print()

                    return {
                        "success": False,
                        "image_name": image_name,
                        "status": "failed",
                        "error": build_message
                    }

                query_error_count = 0

        except Exception as e:
            query_error_count += 1
            elapsed = int(time.time() - start_time)
            print(f"   [{elapsed}s] ⚠️  查询失败 ({query_error_count}/{QUERY_MAX_ERRORS}): {e}")

            if query_error_count >= QUERY_MAX_ERRORS:
                print(f"   ❌ 查询失败次数过多")
                return {
                    "success": False,
                    "image_name": image_name,
                    "status": "query_failed",
                    "error": str(e)
                }

        time.sleep(check_interval)

    print()
    print(f"❌ 镜像构建超时 ({timeout}秒)")
    return {
        "success": False,
        "image_name": image_name,
        "status": "timeout"
    }


def filter_instances_by_keyword(instances: List[str], keyword: str) -> List[str]:
    """
    按关键词过滤实例列表

    Args:
        instances: 实例ID列表
        keyword: 过滤关键词（支持repo或instance_id的一部分）

    Returns:
        过滤后的实例列表
    """
    keyword_lower = keyword.lower()
    return [inst for inst in instances if keyword_lower in inst.lower()]


def filter_envs_by_repo(env_keys: List[str], repo: str) -> List[str]:
    """
    按仓库名过滤环境列表

    Args:
        env_keys: 环境key列表
        repo: 仓库名（例如: django, sympy）

    Returns:
        过滤后的环境列表
    """
    repo_lower = repo.lower()
    return [key for key in env_keys if key.lower().startswith(repo_lower)]


def read_instances_from_file(filepath: str) -> List[str]:
    """从文件读取实例列表"""
    with open(filepath, 'r') as f:
        instances = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return instances


def print_summary(results: List[Dict], task_name: str = "操作"):
    """
    打印操作总结

    Args:
        results: 结果列表
        task_name: 任务名称
    """
    print("\n" + "="*60)
    print(f"📊 {task_name}总结")
    print("="*60)

    success_count = sum(1 for r in results if r.get("success"))
    failed_count = len(results) - success_count

    print(f"总计: {len(results)}")
    print(f"成功: {success_count}")
    print(f"失败: {failed_count}")
    print()

    # 打印成功的项
    if success_count > 0 and success_count <= 20:
        print("✅ 成功:")
        for r in results:
            if r.get("success"):
                name = r.get("image_name") or r.get("instance_id") or r.get("env_key", "N/A")
                print(f"  • {name}")
        print()

    # 打印失败的项
    if failed_count > 0:
        print("❌ 失败:")
        for r in results:
            if not r.get("success"):
                name = r.get("image_name") or r.get("instance_id") or r.get("env_key", "N/A")
                error = r.get("error", "Unknown")
                error_short = error[:100] + "..." if len(error) > 100 else error
                print(f"  • {name}: {error_short}")
        print()


def sanitize_image_name(name: str) -> str:
    """
    清理镜像名称，确保符合SiFlow命名规范

    Args:
        name: 原始名称

    Returns:
        清理后的名称（只包含小写字母、数字和连字符）
    """
    # 替换双下划线为单连字符
    name = name.replace("__", "-")
    # 替换下划线为连字符
    name = name.replace("_", "-")
    # 转小写
    name = name.lower()
    return name


def delete_image(client: SiFlow, image_id: int, image_name: str = None) -> bool:
    """
    删除单个镜像

    Args:
        client: SiFlow 客户端
        image_id: 镜像ID
        image_name: 镜像名称（用于日志）

    Returns:
        是否删除成功
    """
    try:
        import httpx

        path = f"/aiapi/v1/image-sync-server/images-management/{image_id}"
        base_url = str(client.base_url).rstrip('/')
        url = f"{base_url}{path}"

        headers = client.auth_headers
        resp = httpx.delete(url, headers=headers, timeout=30.0)

        if resp.status_code == 200:
            return True
        else:
            print(f"   HTTP {resp.status_code}: {resp.text[:200]}")
            return False

    except Exception as e:
        print(f"   删除失败: {e}")
        return False


def list_images_by_keyword(client: SiFlow, keyword: str) -> List:
    """
    按关键词列出镜像（支持分页）

    Args:
        client: SiFlow 客户端
        keyword: 搜索关键词

    Returns:
        镜像列表
    """
    all_images = []
    page = 1
    page_size = 100

    try:
        while True:
            images = client.images.list(
                keyword=keyword,
                image_build_type="custom",
                page=page,
                pageSize=page_size
            )

            if not images or not hasattr(images, 'rows') or len(images.rows) == 0:
                break

            # 过滤出符合命名规则的镜像
            for image in images.rows:
                image_name = getattr(image, 'name', '')
                if keyword in image_name:
                    all_images.append(image)

            # 检查是否还有更多页
            total = getattr(images, 'total', None)
            if total and len(all_images) >= total:
                break

            # 如果本页数量少于page_size，说明已经是最后一页
            if len(images.rows) < page_size:
                break

            page += 1

        return all_images

    except Exception as e:
        print(f"查询镜像失败: {e}")
        return all_images
