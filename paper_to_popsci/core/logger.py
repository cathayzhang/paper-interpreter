"""
日志模块
"""
import logging
import sys


def get_logger(name: str = "paper_to_popsci") -> logging.Logger:
    """获取配置好的日志记录器"""
    logger = logging.getLogger(name)

    if not logger.handlers:
        # 设置日志级别
        logger.setLevel(logging.INFO)

        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # 设置格式
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%H:%M:%S"
        )
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    return logger


# 全局日志实例
logger = get_logger()
