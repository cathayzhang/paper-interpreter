"""
LLM 客户端模块
支持 Gemini API (文本生成) 和 Nano Banana API (图像生成)
"""
import json
import time
from typing import Iterator, Optional, Dict, Any
import requests

from .config import Config
from .logger import logger


class LLMClient:
    """Gemini LLM 客户端 (文本生成) - 支持 OpenAI 兼容格式"""

    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.model = Config.GEMINI_MODEL
        self.base_url = Config.GEMINI_API_URL

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        生成文本

        Args:
            prompt: 用户提示
            temperature: 温度参数
            max_tokens: 最大生成 token 数
            system_prompt: 系统提示

        Returns:
            生成的文本
        """
        # 尝试 OpenAI 兼容格式（大多数代理服务支持）
        try:
            return self._generate_openai_format(prompt, temperature, max_tokens, system_prompt)
        except Exception as e:
            logger.debug(f"OpenAI 格式失败，尝试 Gemini 原生格式: {e}")
            return self._generate_gemini_format(prompt, temperature, max_tokens, system_prompt)

    def _generate_openai_format(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        system_prompt: Optional[str] = None
    ) -> str:
        """使用 OpenAI 兼容格式生成"""
        url = f"{self.base_url}/v1/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 0.95,
        }

        for attempt in range(Config.MAX_RETRIES):
            try:
                logger.debug(f"OpenAI 格式请求 (尝试 {attempt + 1}/{Config.MAX_RETRIES})")

                response = requests.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=Config.DEFAULT_TIMEOUT_SECONDS
                )
                response.raise_for_status()

                result = response.json()

                # OpenAI 格式响应
                if "choices" in result and len(result["choices"]) > 0:
                    choice = result["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        return choice["message"]["content"]

                raise RuntimeError("无法解析 OpenAI 格式响应")

            except requests.exceptions.Timeout:
                logger.warning(f"OpenAI 格式请求超时 (尝试 {attempt + 1})")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise
            except Exception as e:
                logger.warning(f"OpenAI 格式请求失败 (尝试 {attempt + 1}): {e}")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise

    def _generate_gemini_format(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        system_prompt: Optional[str] = None
    ) -> str:
        """使用 Gemini 原生格式生成"""
        url = f"{self.base_url}/v1beta/models/{self.model}:generateContent"

        headers = {
            "Content-Type": "application/json",
        }

        # 构建请求体
        contents = []
        if system_prompt:
            contents.append({
                "role": "user",
                "parts": [{"text": system_prompt}]
            })
            contents.append({
                "role": "model",
                "parts": [{"text": " understood. "}]
            })

        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })

        data = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "topP": 0.95,
                "topK": 40,
            }
        }

        # 发送请求
        for attempt in range(Config.MAX_RETRIES):
            try:
                logger.debug(f"Gemini 格式请求 (尝试 {attempt + 1}/{Config.MAX_RETRIES})")

                response = requests.post(
                    url,
                    headers=headers,
                    json=data,
                    params={"key": self.api_key},
                    timeout=Config.DEFAULT_TIMEOUT_SECONDS
                )
                response.raise_for_status()

                result = response.json()

                # 提取生成的文本
                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        text_parts = [part["text"] for part in candidate["content"]["parts"]]
                        return "".join(text_parts)

                # 检查是否有错误
                if "error" in result:
                    raise RuntimeError(f"API 错误: {result['error']}")

                raise RuntimeError("无法解析 API 响应")

            except requests.exceptions.Timeout:
                logger.warning(f"Gemini 格式请求超时 (尝试 {attempt + 1})")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise
            except Exception as e:
                logger.warning(f"Gemini 格式请求失败 (尝试 {attempt + 1}): {e}")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise

    def generate_stream(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> Iterator[str]:
        """流式生成文本"""
        # 简化实现，非流式返回
        yield self.generate(prompt, temperature, max_tokens)


class ImageGeneratorClient:
    """图像生成客户端 (Nano Banana / Gemini Image)"""

    def __init__(self):
        self.api_key = Config.NANO_BANANA_API_KEY
        self.model = Config.NANO_BANANA_MODEL
        self.base_url = Config.NANO_BANANA_API_URL

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 768,
        num_images: int = 1
    ) -> Optional[bytes]:
        """
        生成图像

        Args:
            prompt: 正向提示词
            negative_prompt: 负向提示词
            width: 图像宽度
            height: 图像高度
            num_images: 生成数量

        Returns:
            图像数据 (bytes) 或 None
        """
        # 尝试使用 OpenAI 图像生成格式
        try:
            return self._generate_openai_image(prompt, width, height)
        except Exception as e:
            logger.debug(f"OpenAI 图像格式失败，尝试 Gemini 格式: {e}")
            return self._generate_gemini_image(prompt)

    def _generate_openai_image(self, prompt: str, width: int, height: int) -> Optional[bytes]:
        """使用 OpenAI 兼容格式生成图像"""
        url = f"{self.base_url}/v1/images/generations"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        data = {
            "model": self.model,
            "prompt": prompt,
            "n": 1,
            "size": f"{width}x{height}",
            "response_format": "b64_json"
        }

        for attempt in range(Config.MAX_RETRIES):
            try:
                logger.info(f"OpenAI 图像生成请求 (尝试 {attempt + 1}/{Config.MAX_RETRIES})")

                response = requests.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=Config.ILLUSTRATION_TIMEOUT
                )

                if response.status_code != 200:
                    logger.warning(f"OpenAI 图像 API 错误: {response.status_code} - {response.text}")
                    if attempt < Config.MAX_RETRIES - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return None

                result = response.json()

                # 解析图像数据
                if "data" in result and len(result["data"]) > 0:
                    import base64
                    image_data = result["data"][0].get("b64_json")
                    if image_data:
                        return base64.b64decode(image_data)

                logger.warning("OpenAI 响应中未找到图像数据")
                return None

            except requests.exceptions.Timeout:
                logger.warning(f"OpenAI 图像生成超时 (尝试 {attempt + 1})")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    return None
            except Exception as e:
                logger.warning(f"OpenAI 图像生成失败 (尝试 {attempt + 1}): {e}")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    return None

        return None

    def _generate_gemini_image(self, prompt: str) -> Optional[bytes]:
        """使用 Gemini 原生格式生成图像"""
        image_model = "gemini-3-pro-preview"
        url = f"{self.base_url}/v1beta/models/{image_model}:generateContent"

        headers = {
            "Content-Type": "application/json",
        }

        # 构建请求体 - Gemini 图像生成格式
        data = {
            "contents": [{
                "role": "user",
                "parts": [
                    {"text": f"Generate an image: {prompt}"}
                ]
            }],
            "generationConfig": {
                "responseModalities": ["IMAGE", "TEXT"],
                "temperature": 0.7,
            }
        }

        for attempt in range(Config.MAX_RETRIES):
            try:
                logger.info(f"Gemini 图像生成请求 (尝试 {attempt + 1}/{Config.MAX_RETRIES})")

                response = requests.post(
                    url,
                    headers=headers,
                    json=data,
                    params={"key": self.api_key},
                    timeout=Config.ILLUSTRATION_TIMEOUT
                )

                if response.status_code != 200:
                    logger.warning(f"Gemini 图像 API 错误: {response.status_code} - {response.text}")
                    if attempt < Config.MAX_RETRIES - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return None

                result = response.json()

                # 解析图像数据
                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        for part in candidate["content"]["parts"]:
                            if "inlineData" in part:
                                import base64
                                image_data = base64.b64decode(part["inlineData"]["data"])
                                return image_data

                logger.warning("Gemini 响应中未找到图像数据")
                return None

            except requests.exceptions.Timeout:
                logger.warning(f"Gemini 图像生成超时 (尝试 {attempt + 1})")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    return None
            except Exception as e:
                logger.warning(f"Gemini 图像生成失败 (尝试 {attempt + 1}): {e}")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    return None

        return None
