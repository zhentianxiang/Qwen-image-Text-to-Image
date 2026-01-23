"""
文生图路由模块
"""

import uuid
from typing import List

import torch
from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from ..config import settings
from ..models import get_model_manager
from ..utils.logger import get_logger
from ..utils.image_utils import save_images_to_temp, create_zip_from_images

logger = get_logger(__name__)
router = APIRouter(prefix="/text-to-image", tags=["文生图"])


@router.post("")
async def generate_image(
    prompt: str = Form(..., description="生成图像的描述文本"),
    negative_prompt: str = Form("", description="不希望出现在图像中的内容"),
    aspect_ratio: str = Form("1:1", description="图像宽高比"),
    num_inference_steps: int = Form(50, ge=20, le=100, description="推理步数"),
    true_cfg_scale: float = Form(4.0, ge=1.0, le=10.0, description="CFG尺度参数"),
    seed: int = Form(-1, description="随机种子，-1表示随机生成"),
    num_images: int = Form(1, ge=1, le=4, description="生成图像数量"),
):
    """
    文生图端点：根据文本提示生成图像
    
    - **prompt**: 描述要生成的图像内容
    - **negative_prompt**: 描述不希望出现的内容
    - **aspect_ratio**: 图像宽高比，支持 1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3
    - **num_inference_steps**: 推理步数，越多质量越好但速度越慢
    - **true_cfg_scale**: CFG尺度，控制生成图像与提示的匹配程度
    - **seed**: 随机种子，用于复现结果
    - **num_images**: 生成图像数量
    """
    model_manager = get_model_manager()
    
    if not model_manager.is_text_to_image_loaded:
        raise HTTPException(status_code=503, detail="文生图模型未加载")
    
    # 获取宽高比对应的尺寸
    width, height = settings.get_aspect_ratio_size(aspect_ratio)
    
    # 获取随机数生成器
    generator = model_manager.get_generator(seed)
    
    logger.info(f"开始生成图像 | prompt: {prompt[:50]}... | size: {width}x{height}")
    
    try:
        with torch.inference_mode():
            result = model_manager.text_to_image_pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt if negative_prompt else None,
                width=width,
                height=height,
                num_inference_steps=num_inference_steps,
                true_cfg_scale=true_cfg_scale,
                generator=generator,
                num_images_per_prompt=num_images,
            )
        
        images = result.images
        logger.info(f"图像生成成功 | 数量: {len(images)}")
        
        # 保存图像到临时目录
        saved_images = save_images_to_temp(images, prefix="generated")
        
        if len(saved_images) == 1:
            # 单张图像直接返回
            filepath, filename = saved_images[0]
            return FileResponse(
                filepath,
                media_type="image/png",
                filename=filename,
            )
        else:
            # 多张图像返回ZIP
            image_paths = [path for path, _ in saved_images]
            zip_path = create_zip_from_images(image_paths)
            
            return FileResponse(
                zip_path,
                media_type="application/zip",
                filename=f"generated_images_{uuid.uuid4().hex[:8]}.zip",
            )
    
    except Exception as e:
        logger.error(f"图像生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.get("/aspect-ratios")
async def get_aspect_ratios():
    """获取支持的宽高比及其对应尺寸"""
    return settings.aspect_ratios
