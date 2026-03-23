#!/usr/bin/env python3
import sys
import argparse
import uvicorn

from ._local_proxy import app


def start_proxy():
    """主函数"""
    parser = argparse.ArgumentParser(description="启动OpenAI代理服务")
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="服务主机地址 (默认: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="服务端口 (默认: 8000)"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="启用热重载 (开发模式)"
    )
    parser.add_argument(
        "--log-level", 
        default="info", 
        choices=["debug", "info", "warning", "error"],
        help="日志级别 (默认: info)"
    )
    parser.add_argument(
        "--api-key", 
        help="OpenAI API密钥 (也可以通过环境变量OPENAI_API_KEY设置)"
    )
    parser.add_argument(
        "--openai-url",
        default="",
        help="API基础URL (默认: https://api.openai.com/v1)"
    )
    
    args = parser.parse_args()
    
    if not args.openai_url:
        print("错误: 请设置OpenAI API基础URL")
        print("方法: 使用 --openai-url 参数")
        sys.exit(1)
    
    # 设置OpenAI配置
    from ._local_proxy import set_openai_config
    set_openai_config(args.openai_url, args.api_key)
    
    print(f"启动OpenAI代理服务...")
    print(f"主机: {args.host}")
    print(f"端口: {args.port}")
    print(f"OpenAI URL: {args.openai_url}")
    print(f"热重载: {'启用' if args.reload else '禁用'}")
    print(f"日志级别: {args.log_level}")
    print(f"API文档: http://{args.host}:{args.port}/docs")
    print(f"健康检查: http://{args.host}:{args.port}/health")
    print("-" * 50)
    
    # 启动服务
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
        access_log=True
    )

if __name__ == "__main__":
    start_proxy()