"""
图像处理工具模块
"""

import os
import io
import uuid
import time
import zipfile
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image
from fastapi import UploadFile, HTTPException

from .logger import get_logger

logger = get_logger(__name__)


def validate_image_file(
    file: UploadFile,
    allowed_types: List[str],
    max_size_mb: int,
) -> None:
    """
    验证上传的图像文件
    
    Args:
        file: 上传的文件
        allowed_types: 允许的MIME类型列表
        max_size_mb: 最大文件大小（MB）
    
    Raises:
        HTTPException: 验证失败时抛出
    """
    # 检查文件类型
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file.content_type}。支持的类型: {allowed_types}"
        )
    
    # 检查文件大小（需要先读取内容）
    # 注意：这会消耗文件内容，调用后需要重置文件指针或使用返回的内容


async def read_and_validate_image(
    file: UploadFile,
    allowed_types: List[str],
    max_size_mb: int,
) -> Image.Image:
    """
    读取并验证上传的图像
    
    Args:
        file: 上传的文件
        allowed_types: 允许的MIME类型列表
        max_size_mb: 最大文件大小（MB）
    
    Returns:
        PIL Image对象
    
    Raises:
        HTTPException: 验证失败或读取失败时抛出
    """
    # 检查文件类型
    if file.content_type and file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file.content_type}。支持的类型: {allowed_types}"
        )
    
    # 读取文件内容
    content = await file.read()
    
    # 检查文件大小
    max_size_bytes = max_size_mb * 1024 * 1024
    if len(content) > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制: {len(content) / 1024 / 1024:.2f}MB > {max_size_mb}MB"
        )
    
    # 尝试打开图像
    try:
        image = Image.open(io.BytesIO(content)).convert("RGB")
        return image
    except Exception as e:
        logger.error(f"无法打开图像文件: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"无法解析图像文件: {str(e)}"
        )


def save_image_to_temp(
    image: Image.Image,
    prefix: str = "generated",
    format: str = "PNG",
) -> Tuple[str, str]:
    """
    保存图像到临时目录
    
    Args:
        image: PIL Image对象
        prefix: 文件名前缀
        format: 图像格式
    
    Returns:
        (文件路径, 文件名) 元组
    """
    temp_dir = tempfile.gettempdir()
    filename = f"{prefix}_{uuid.uuid4().hex[:8]}.{format.lower()}"
    filepath = os.path.join(temp_dir, filename)
    
    image.save(filepath, format)
    logger.debug(f"图像已保存到: {filepath}")
    
    return filepath, filename


def save_images_to_temp(
    images: List[Image.Image],
    prefix: str = "generated",
    format: str = "PNG",
) -> List[Tuple[str, str]]:
    """
    批量保存图像到临时目录
    
    Args:
        images: PIL Image对象列表
        prefix: 文件名前缀
        format: 图像格式
    
    Returns:
        [(文件路径, 文件名), ...] 列表
    """
    results = []
    for i, image in enumerate(images):
        filepath, filename = save_image_to_temp(
            image,
            prefix=f"{prefix}_{i}",
            format=format,
        )
        results.append((filepath, filename))
    return results


def create_zip_from_images(
    image_paths: List[str],
    zip_name: Optional[str] = None,
) -> str:
    """
    将多个图像文件打包成ZIP
    
    Args:
        image_paths: 图像文件路径列表
        zip_name: ZIP文件名（可选）
    
    Returns:
        ZIP文件路径
    """
    temp_dir = tempfile.gettempdir()
    if zip_name is None:
        zip_name = f"images_{uuid.uuid4().hex[:8]}.zip"
    
    zip_path = os.path.join(temp_dir, zip_name)
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for path in image_paths:
            if os.path.exists(path):
                arcname = os.path.basename(path)
                zipf.write(path, arcname)
    
    logger.debug(f"ZIP文件已创建: {zip_path}")
    return zip_path


def cleanup_old_temp_files(
    max_age_hours: int = 24,
    patterns: Optional[List[str]] = None,
) -> int:
    """
    清理过期的临时文件
    
    Args:
        max_age_hours: 文件最大保留时间（小时）
        patterns: 要清理的文件名模式列表
    
    Returns:
        清理的文件数量
    """
    if patterns is None:
        patterns = ["generated_", "edited_", "batch_edit_", "images_"]
    
    temp_dir = tempfile.gettempdir()
    max_age_seconds = max_age_hours * 3600
    current_time = time.time()
    cleaned_count = 0
    
    try:
        for filename in os.listdir(temp_dir):
            # 检查文件名是否匹配模式
            if not any(filename.startswith(p) for p in patterns):
                continue
            
            filepath = os.path.join(temp_dir, filename)
            
            # 跳过目录
            if not os.path.isfile(filepath):
                continue
            
            # 检查文件年龄
            file_age = current_time - os.path.getmtime(filepath)
            if file_age > max_age_seconds:
                try:
                    os.remove(filepath)
                    cleaned_count += 1
                    logger.debug(f"已清理过期文件: {filename}")
                except OSError as e:
                    logger.warning(f"无法删除文件 {filename}: {e}")
    
    except Exception as e:
        logger.error(f"清理临时文件时出错: {e}")
    
    if cleaned_count > 0:
        logger.info(f"已清理 {cleaned_count} 个过期临时文件")
    
    return cleaned_count
