#!/usr/bin/env python3
"""
使用 SciTix ACCESS_KEY 查询 slimerl 镜像
"""
import sys
from pathlib import Path

# 添加 vendor 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent / '.vendor_siflow'))

from siflow import SiFlow


def get_slimerl_image_url():
    """
    使用 SciTix ACCESS_KEY 查询 slimerl 镜像的完整 URL
    """
    print("\n" + "="*70)
    print("查询 SciTix 平台上的 slimerl 镜像")
    print("="*70 + "\n")

    # SciTix 认证信息
    SCITIX_ACCESS_KEY_ID = "45a7c966-07be-450f-a690-f5d62975307c"
    SCITIX_ACCESS_KEY_SECRET = "1yDjNoyzGYH7o9AwCP"

    # 尝试不同的 SciTix 区域和集群
    scitix_configs = [
        {"region": "ap-southeast", "cluster": "aries", "name": "ap-southeast (aries)"},
        {"region": "ap-southeast", "cluster": "cks", "name": "ap-southeast (cks)"},
        {"region": "us-east", "cluster": "cetus", "name": "us-east (cetus)"},
        {"region": "us-west", "cluster": "pisces", "name": "us-west (pisces)"},
    ]

    for config in scitix_configs:
        print(f"\n{'='*70}")
        print(f"尝试配置: {config['name']}")
        print(f"{'='*70}")
        print(f"   Region: {config['region']}")
        print(f"   Cluster: {config['cluster']}")

        try:
            # 创建 SciTix 客户端
            client = SiFlow(
                region=config['region'],
                cluster=config['cluster'],
                access_key_id=SCITIX_ACCESS_KEY_ID,
                access_key_secret=SCITIX_ACCESS_KEY_SECRET
            )
            print(f"✅ 客户端创建成功")

            # 查询 slimerl 镜像
            print(f"\n📌 查询镜像: slimerl")
            images = client.images.list(
                keyword="slimerl",
                pageSize=50
            )

            print(f"✅ API 调用成功")

            if hasattr(images, 'rows') and images.rows:
                print(f"\n🎉 找到 {len(images.rows)} 个镜像:\n")

                for idx, img in enumerate(images.rows, 1):
                    name = getattr(img, 'name', 'N/A')
                    version = getattr(img, 'version', 'N/A')
                    status = getattr(img, 'status', 'N/A')
                    img_id = getattr(img, 'id', 'N/A')

                    print(f"{'='*70}")
                    print(f"镜像 #{idx}")
                    print(f"{'='*70}")
                    print(f"  名称: {name}")
                    print(f"  版本: {version}")
                    print(f"  状态: {status}")
                    print(f"  ID: {img_id}")

                    # 获取 Registry URL
                    cluster_urls = getattr(img, 'cluster_images_url', [])
                    if cluster_urls:
                        print(f"  Registry URLs:")
                        for url in cluster_urls:
                            if ': ' in url:
                                clean_url = url.split(': ')[-1]
                                print(f"    ✅ {clean_url}")
                            else:
                                print(f"    ✅ {url}")
                    else:
                        print(f"  ⚠️  未找到 Registry URL")

                    # 打印其他有用信息
                    build_status = getattr(img, 'image_build_status', 'N/A')
                    if build_status != 'N/A':
                        print(f"  构建状态: {build_status}")

                    description = getattr(img, 'description', '')
                    if description:
                        print(f"  描述: {description}")

                    print()

                return images.rows

            else:
                print(f"⚠️  未找到匹配的镜像")
                print(f"   返回对象类型: {type(images)}")

        except Exception as e:
            print(f"❌ 失败: {e}")
            print(f"   错误类型: {type(e).__name__}")
            import traceback
            traceback.print_exc()

    return None


def list_all_scitix_images():
    """列出 SciTix 平台上的所有镜像"""
    print("\n" + "="*70)
    print("列出 SciTix 平台上的所有镜像")
    print("="*70 + "\n")

    SCITIX_ACCESS_KEY_ID = "45a7c966-07be-450f-a690-f5d62975307c"
    SCITIX_ACCESS_KEY_SECRET = "1yDjNoyzGYH7o9AwCP"

    try:
        client = SiFlow(
            region="ap-southeast",
            cluster="aries",
            access_key_id=SCITIX_ACCESS_KEY_ID,
            access_key_secret=SCITIX_ACCESS_KEY_SECRET
        )

        print("📌 查询所有镜像（前50个）...")
        images = client.images.list(pageSize=50)

        if hasattr(images, 'rows') and images.rows:
            print(f"\n找到 {len(images.rows)} 个镜像:\n")
            for idx, img in enumerate(images.rows, 1):
                name = getattr(img, 'name', 'N/A')
                version = getattr(img, 'version', 'N/A')
                status = getattr(img, 'status', 'N/A')
                print(f"{idx}. {name}:{version} ({status})")
        else:
            print("未找到镜像")

    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="查询 SciTix 平台镜像")
    parser.add_argument("--list-all", action="store_true", help="列出所有镜像")

    args = parser.parse_args()

    if args.list_all:
        list_all_scitix_images()
    else:
        result = get_slimerl_image_url()

        if result:
            print("\n" + "="*70)
            print("✅ 成功找到 slimerl 镜像！")
            print("="*70)
        else:
            print("\n" + "="*70)
            print("❌ 未能找到 slimerl 镜像")
            print("="*70)
            print("\n💡 尝试: python get_slimerl_url.py --list-all")
