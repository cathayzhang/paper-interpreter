"""
配图生成模块
根据提示词生成文章配图
"""
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import Config
from .logger import logger
from .llm_client import ImageGeneratorClient


class IllustrationGenerator:
    """配图生成器"""

    def __init__(self):
        self.client = ImageGeneratorClient()

    def generate_all(
        self,
        prompts: List[Dict[str, Any]],
        output_dir: Path,
        max_workers: int = 2
    ) -> List[Dict[str, Any]]:
        """
        生成所有配图

        Args:
            prompts: 配图提示词列表
            output_dir: 输出目录
            max_workers: 并发数

        Returns:
            配图结果列表
        """
        logger.info(f"开始生成配图: {len(prompts)} 张")

        output_dir.mkdir(parents=True, exist_ok=True)
        results = []

        # 串行生成（避免 API 限流）
        for i, prompt_data in enumerate(prompts):
            result = self._generate_single(prompt_data, output_dir, i)
            results.append(result)

            # 间隔避免限流
            if i < len(prompts) - 1:
                time.sleep(2)

        success_count = sum(1 for r in results if r["success"])
        logger.info(f"配图生成完成: {success_count}/{len(prompts)} 张成功")

        return results

    def _generate_single(
        self,
        prompt_data: Dict[str, Any],
        output_dir: Path,
        index: int
    ) -> Dict[str, Any]:
        """生成单张配图"""
        section = prompt_data.get("section", "unknown")
        prompt = prompt_data.get("prompt", "")
        style = prompt_data.get("style", "")
        negative_prompt = prompt_data.get("negative_prompt", "")

        # 生成文件名
        timestamp = int(time.time())
        filename = f"{section}_{timestamp}_{index:02d}.png"
        filepath = output_dir / filename

        result = {
            "section": section,
            "prompt": prompt,
            "filepath": str(filepath),
            "filename": filename,
            "success": False
        }

        try:
            logger.info(f"生成配图 [{index+1}]: {section}")

            # 使用 Gemini 原生格式生成图像
            image_data = self._generate_with_gemini(prompt, style, negative_prompt)

            if image_data:
                # 保存图像
                with open(filepath, "wb") as f:
                    f.write(image_data)

                result["success"] = True
                logger.info(f"配图生成成功: {filename}")
            else:
                logger.warning(f"配图生成失败: {section}，使用占位符")
                result["filepath"] = None

        except Exception as e:
            logger.warning(f"配图生成异常: {e}")
            result["filepath"] = None

        return result

    def _generate_with_gemini(self, prompt: str, style: str, negative_prompt: str) -> Optional[bytes]:
        """使用 Gemini 原生格式生成图像"""
        import requests
        import base64

        # Gemini 图像生成端点
        url = f"{Config.NANO_BANANA_API_URL}/v1beta/models/{Config.NANO_BANANA_MODEL}:generateContent"

        headers = {
            "Content-Type": "application/json",
        }

        # 构建提示词 - 针对通俗易懂的图表优化
        full_prompt = f"""Generate an educational infographic/diagram in Chinese:

Requirements:
- Use simple, clear Chinese text labels that anyone can understand
- Style: Clean, modern infographic style with warm beige/cream background (#FDF6E3)
- Content: {prompt}
- Avoid: {negative_prompt}

Important Design Principles:
- Make it INSTANTLY UNDERSTANDABLE at a glance - like a great social media infographic
- Use relatable analogies and visual metaphors from daily life
- Include before/after comparisons or step-by-step visual flows
- Use icons, simple shapes, and clear visual hierarchy
- Add brief Chinese annotations that explain the "why" and "so what"
- Make viewers want to SAVE and SHARE this image
- Text must be large enough to read, use conversational Chinese
- Focus on "Aha!" moment - the viewer should get it immediately
- Professional but approachable, like a high-quality popular science illustration"""

        data = {
            "contents": [{
                "role": "user",
                "parts": [{"text": full_prompt}]
            }],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
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
                    params={"key": Config.NANO_BANANA_API_KEY},
                    timeout=Config.ILLUSTRATION_TIMEOUT
                )

                if response.status_code != 200:
                    logger.warning(f"Gemini 图像 API 错误: {response.status_code} - {response.text}")
                    if attempt < Config.MAX_RETRIES - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return None

                result = response.json()
                logger.debug(f"Gemini 响应: {result}")

                # 解析图像数据
                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        for part in candidate["content"]["parts"]:
                            if "inlineData" in part:
                                image_data = base64.b64decode(part["inlineData"]["data"])
                                return image_data
                            elif "text" in part:
                                logger.debug(f"Gemini 文本响应: {part['text']}")

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

    def create_placeholder(self, output_dir: Path, section: str) -> Path:
        """
        创建占位符图像

        Args:
            output_dir: 输出目录
            section: 章节名

        Returns:
            占位符文件路径
        """
        try:
            from PIL import Image, ImageDraw, ImageFont

            # 创建空白图像
            img = Image.new('RGB', (1024, 768), color='#F5F5DC')
            draw = ImageDraw.Draw(img)

            # 添加文字
            text = f"[{section}]\n配图生成中..."

            # 尝试使用默认字体
            try:
                font = ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", 40)
            except:
                font = ImageFont.load_default()

            # 计算文字位置（居中）
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (1024 - text_width) // 2
            y = (768 - text_height) // 2

            draw.text((x, y), text, fill='#666666', font=font)

            # 保存
            filename = f"{section}_placeholder.png"
            filepath = output_dir / filename
            img.save(filepath)

            return filepath

        except ImportError:
            logger.warning("PIL 未安装，跳过占位符创建")
            return None
        except Exception as e:
            logger.warning(f"创建占位符失败: {e}")
            return None
