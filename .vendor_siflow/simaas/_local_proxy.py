import logging
from typing import Optional, Dict, Any
import httpx
from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager
import json

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局变量
global openai_base_url, openai_api_key
openai_base_url = ""
openai_api_key = ""


class ProxyService:
    """代理服务类"""
    
    def __init__(self, api_key: str, base_url: str = ""):
        self.api_key = api_key
        self.base_url = base_url
    
    async def close(self):
        """关闭客户端连接"""

    async def proxy_openai_api(self, request: Request):
        # proxy request to OpenAI API
        headers = {k: v for k, v in request.headers.items() if
                   k not in {'host', 'content-length', 'x-forwarded-for', 'x-real-ip', 'connection'}}
        url = f'{self.base_url}{request.url.path}'

        # create httpx async client
        client = httpx.AsyncClient()
        
        request_body = await request.json() if request.method in {'POST', 'PUT'} else None
        if request_body is not None:
            request_body["stream"] = True

        content: Dict[str, Any] = {
            "id": "",
            "object": "chat.completion",
            "created": "",
            "model": "",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "",
                        "content": "",
                        "tool_calls": []
                    },
                    "delta": {
                        "role": "",
                        "content": "",
                        "reasoning_content": "",
                        "tool_calls": []
                    },
                    "finish_reason": "",
                    "content_filter_results": {
                        "hate": {
                            "filtered": False
                        },
                        "self_harm": {
                            "filtered": False
                        },
                        "sexual": {
                            "filtered": False
                        },
                        "violence": {
                            "filtered": False
                        },
                        "jailbreak": {
                            "filtered": False,
                            "detected": False
                        },
                        "profanity": {
                            "filtered": False, 
                            "detected": False
                        }
                    }
                }
            ],
            "system_fingerprint": "",
            "usage":{
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "prompt_tokens_details": None,
                "completion_tokens_details": None
            }
        }
        try:
            print(request.method, url, headers, request.query_params, request_body)
            st = client.stream(request.method, url, headers=headers, params=request.query_params, json=request_body)
            async with st as res:
                lastChunk = b''
                async for chunk in res.aiter_bytes():
                    lines = (lastChunk + chunk).split(b'\n')
                    for line in lines:
                        print(line)
                        if line.startswith(b'data: '):
                            data = line[6:]
                            if data.strip() != b'[DONE]':
                                try:
                                    parsed = json.loads(data)
                                    if "id" in parsed:
                                        content["id"] = parsed["id"]
                                    if "created" in parsed:
                                        content["created"] = parsed["created"]
                                    if "model" in parsed:   
                                        content["model"] = parsed["model"]
                                    if "system_fingerprint" in parsed:
                                        content["system_fingerprint"] = parsed["system_fingerprint"]
                                    if "usage" in parsed:   
                                        content["usage"] = parsed["usage"]
                                    if len(parsed["choices"]) > 0:
                                        for choice in parsed["choices"]:
                                            choice_index = choice["index"]
                                            if choice_index < len(content["choices"]):
                                                if "tool_calls" in choice["delta"]:
                                                    content["choices"][choice_index]["delta"]["tool_calls"] = choice["delta"]["tool_calls"]
                                                if choice["finish_reason"] is not None:
                                                    content["choices"][choice_index]["finish_reason"] = choice["finish_reason"]
                                                if choice["content_filter_results"] is not None:
                                                    content["choices"][choice_index]["content_filter_results"] = choice["content_filter_results"]
                                                if "role" in choice["delta"]:
                                                    content["choices"][choice_index]["delta"]["role"] = choice["delta"]["role"]
                                                if choice["delta"].get("content"):
                                                    delta_dict = content["choices"][choice_index]["delta"]
                                                    if isinstance(delta_dict, dict):
                                                        delta_dict["content"] += choice["delta"]["content"]
                                                if choice["delta"].get("reasoning_content"):
                                                    delta_dict = content["choices"][choice_index]["delta"]
                                                    if isinstance(delta_dict, dict):
                                                        delta_dict["reasoning_content"] += choice["delta"]["reasoning_content"]
                                except json.JSONDecodeError as e:
                                    logger.error(f"JSON解析错误: {e}, 内容: {data}")
                                    lastChunk = line
                                    continue
                            else:
                                break
            
            if res.status_code == 200:
                content["choices"][0]["message"]["content"] = content["choices"][0]["delta"]["content"]
                content["choices"][0]["message"]["tool_calls"] = content["choices"][0]["delta"]["tool_calls"]
                content["choices"][0]["message"]["role"] = content["choices"][0]["delta"]["role"]
                return content
            else:
                raise HTTPException(status_code=res.status_code, detail=res.text)

        except httpx.RequestError as exc:
            raise HTTPException(status_code=500, detail=f'An error occurred while requesting: {exc}')


# 全局代理服务实例
proxy_service: Optional[ProxyService] = None

def set_openai_config(base_url: str, api_key: str):
    """设置OpenAI配置"""
    global openai_base_url, openai_api_key
    openai_base_url = base_url
    openai_api_key = api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global proxy_service  
    proxy_service = ProxyService(openai_api_key, openai_base_url)
    logger.info(f"Proxy service initialized with base_url: {openai_base_url}")
    
    yield
    
    # 关闭时清理
    if proxy_service:
        await proxy_service.close()
        logger.info("Proxy service closed")


# 创建FastAPI应用
app = FastAPI(
    title="OpenAI Proxy Service",
    description="代理转发OpenAI请求的服务，支持流式和非流式响应",
    version="1.0.0",
    lifespan=lifespan
)

@app.api_route('/{path:path}', methods=['GET', 'POST', 'PUT', 'DELETE'])
async def request_handler(request: Request):
    if proxy_service is None:
        raise HTTPException(status_code=500, detail="Proxy service not initialized")
    return await proxy_service.proxy_openai_api(request)
