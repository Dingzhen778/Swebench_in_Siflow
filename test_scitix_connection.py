#!/usr/bin/env python3
"""
测试连接 scitix 平台并获取 slimerl 镜像信息
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加 vendor 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent / '.vendor_siflow'))

# 加载环境变量
load_dotenv()

# 尝试导入 siflow SDK
try:
    from siflow import SiFlow
    print("✅ SiFlow SDK 导入成功")
except ImportError as e:
    print(f"❌ 无法导入 SiFlow SDK: {e}")
    sys.exit(1)


def test_scitix_connection():
    """测试连接 scitix 平台"""

    print("\n" + "="*70)
    print("测试连接 scitix 平台")
    print("="*70 + "\n")

    # 从环境变量读取配置
    access_key_id = os.environ.get("SIFLOW_ACCESS_KEY_ID", "")
    access_key_secret = os.environ.get("SIFLOW_ACCESS_KEY_SECRET", "")

    if not access_key_id or not access_key_secret:
        print("❌ 未找到 ACCESS_KEY_ID 或 ACCESS_KEY_SECRET")
        print("   请在 .env 文件中配置")
        return None

    print(f"📌 配置信息:")
    print(f"   ACCESS_KEY_ID: {access_key_id[:8]}...")
    print(f"   ACCESS_KEY_SECRET: {'*' * 10}")

    # 尝试不同的 region/cluster 配置
    test_configs = [
        {
            "name": "scitix ap-southeast (aries)",
            "region": "ap-southeast",
            "cluster": "aries"
        },
        {
            "name": "scitix ap-southeast (cks)",
            "region": "ap-southeast",
            "cluster": "cks"
        },
        {
            "name": "scitix us-east (cetus)",
            "region": "us-east",
            "cluster": "cetus"
        },
        {
            "name": "scitix us-west (pisces)",
            "region": "us-west",
            "cluster": "pisces"
        },
        {
            "name": "siflow cn-shanghai (hercules)",
            "region": "cn-shanghai",
            "cluster": "hercules"
        }
    ]

    for config in test_configs:
        print(f"\n{'='*70}")
        print(f"尝试配置: {config['name']}")
        print(f"{'='*70}")
        print(f"   Region: {config['region']}")
        print(f"   Cluster: {config['cluster']}")

        try:
            # 创建客户端
            client = SiFlow(
                region=config['region'],
                cluster=config['cluster'],
                access_key_id=access_key_id,
                access_key_secret=access_key_secret
            )

            print(f"✅ 客户端创建成功")

            # 尝试查询镜像
            print(f"\n📌 查询镜像: slimerl")

            try:
                images = client.images.list(
                    keyword="slimerl",
                    pageSize=50
                )

                print(f"✅ API 调用成功")

                if hasattr(images, 'rows') and images.rows:
                    print(f"\n🎉 找到 {len(images.rows)} 个镜像:\n")

                    for idx, img in enumerate(images.rows, 1):
                        print(f"镜像 #{idx}:")
                        print(f"  名称: {getattr(img, 'name', 'N/A')}")
                        print(f"  版本: {getattr(img, 'version', 'N/A')}")
                        print(f"  状态: {getattr(img, 'status', 'N/A')}")
                        print(f"  ID: {getattr(img, 'id', 'N/A')}")

                        # 尝试获取 URL
                        cluster_urls = getattr(img, 'cluster_images_url', [])
                        if cluster_urls:
                            print(f"  Registry URLs:")
                            for url in cluster_urls:
                                if ': ' in url:
                                    print(f"    - {url.split(': ')[-1]}")
                                else:
                                    print(f"    - {url}")

                        # 打印所有可用属性（调试用）
                        print(f"  所有属性: {dir(img)}")
                        print()

                    return images.rows[0]

                elif hasattr(images, 'items') and images.items:
                    print(f"\n🎉 找到 {len(images.items)} 个镜像:\n")

                    for idx, img in enumerate(images.items, 1):
                        print(f"镜像 #{idx}:")
                        print(f"  名称: {getattr(img, 'name', 'N/A')}")
                        print(f"  版本: {getattr(img, 'version', 'N/A')}")
                        print(f"  状态: {getattr(img, 'status', 'N/A')}")
                        print()

                    return images.items[0]

                else:
                    print(f"⚠️  未找到匹配的镜像")
                    print(f"   返回对象类型: {type(images)}")
                    print(f"   返回对象属性: {dir(images)}")

            except Exception as e:
                print(f"❌ 查询镜像失败: {e}")
                print(f"   错误类型: {type(e).__name__}")
                import traceback
                traceback.print_exc()

        except Exception as e:
            print(f"❌ 客户端创建失败: {e}")
            print(f"   错误类型: {type(e).__name__}")
            import traceback
            traceback.print_exc()

    return None


def list_all_images():
    """列出所有可访问的镜像"""
    print("\n" + "="*70)
    print("列出所有镜像（使用原 siflow 配置）")
    print("="*70 + "\n")

    access_key_id = os.environ.get("SIFLOW_ACCESS_KEY_ID", "")
    access_key_secret = os.environ.get("SIFLOW_ACCESS_KEY_SECRET", "")

    try:
        client = SiFlow(
            region="cn-shanghai",
            cluster="hercules",
            access_key_id=access_key_id,
            access_key_secret=access_key_secret
        )

        print("📌 查询所有镜像（前20个）...")
        images = client.images.list(pageSize=20)

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

    parser = argparse.ArgumentParser(description="测试 scitix 平台连接")
    parser.add_argument("--list-all", action="store_true", help="列出所有镜像")

    args = parser.parse_args()

    if args.list_all:
        list_all_images()
    else:
        result = test_scitix_connection()

        if result:
            print("\n" + "="*70)
            print("✅ 成功找到镜像！")
            print("="*70)
        else:
            print("\n" + "="*70)
            print("❌ 未能找到 slimerl 镜像")
            print("="*70)
            print("\n💡 提示:")
            print("   1. scitix 可能使用不同的 API 端点")
            print("   2. 可能需要不同的认证凭据")
            print("   3. 镜像可能在不同的命名空间下")
            print("   4. 尝试运行: python test_scitix_connection.py --list-all")
