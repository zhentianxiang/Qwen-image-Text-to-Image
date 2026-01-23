"""
日志配置模块
"""

import logging
import sys
from pathlib import Path
from typing import Optional


_loggers: dict = {}


def setup_logger(
    name: str = "qwen_image",
    level: str = "INFO",
    log_format: Optional[str] = None,
    file_path: Optional[str] = None,
) -> logging.Logger:
    """
    设置并返回logger
    
    Args:
        name: logger名称
        level: 日志级别
        log_format: 日志格式
        file_path: 日志文件路径（可选）
    
    Returns:
        配置好的logger实例
    """
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 日志格式
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    formatter = logging.Formatter(log_format)
    
    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件输出（可选）
    if file_path:
        log_dir = Path(file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    _loggers[name] = logger
    return logger


def get_logger(name: str = "qwen_image") -> logging.Logger:
    """
    获取logger实例
    
    如果logger不存在，会使用默认配置创建
    """
    if name not in _loggers:
        return setup_logger(name)
    return _loggers[name]
