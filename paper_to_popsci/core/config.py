"""
配置管理模块
"""
import os
from pathlib import Path
from typing import Optional


class Config:
    """配置类"""

    # 输出配置
    OUTPUT_DIR = os.getenv("PAPER_OUTPUT_DIR", "./paper_outputs")
    TEMP_DIR = os.getenv("PAPER_TEMP_DIR", "/tmp/paper_interpreter")

    # API 配置 - Gemini (文本生成)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
    GEMINI_API_URL = os.getenv("GEMINI_API_URL", "https://yunwu.ai")

    # API 配置 - Nano Banana (配图生成)
    NANO_BANANA_API_KEY = os.getenv("NANO_BANANA_API_KEY", "")
    NANO_BANANA_MODEL = os.getenv("NANO_BANANA_MODEL", "gemini-3-pro-image-preview")
    NANO_BANANA_API_URL = os.getenv("NANO_BANANA_API_URL", "https://yunwu.ai")

    # 限制配置
    MAX_PAPER_SIZE_MB = int(os.getenv("MAX_PAPER_SIZE_MB", "50"))
    CHUNK_SIZE_TOKENS = int(os.getenv("CHUNK_SIZE_TOKENS", "4000"))
    DEFAULT_TIMEOUT_SECONDS = int(os.getenv("DEFAULT_TIMEOUT_SECONDS", "30"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

    # 配图配置
    ILLUSTRATION_COUNT = int(os.getenv("ILLUSTRATION_COUNT", "5"))
    ILLUSTRATION_TIMEOUT = int(os.getenv("ILLUSTRATION_TIMEOUT", "120"))

    # 风格配置
    STYLE = {
        "background_color": "#FDF6E3",
        "text_color": "#2C3E50",
        "accent_color": "#16A085",
        "font_family": "'Noto Serif SC', 'Georgia', serif",
        "font_family_sans": "'Noto Sans SC', 'Helvetica', sans-serif",
    }

    @classmethod
    def ensure_dirs(cls):
        """确保必要的目录存在"""
        Path(cls.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        Path(cls.TEMP_DIR).mkdir(parents=True, exist_ok=True)
