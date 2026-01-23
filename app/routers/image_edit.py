"""
图像编辑路由模块
"""

import uuid
from typing import List

import torch
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ..config import settings
from ..models import get_model_manager
from ..utils.logger import get_logger
from ..utils.image_utils import (
    read_and_validate_image,
    save_images_to_temp,
    create_zip_from_images,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/image-edit", tags=["图像编辑"])


@router.post("")
async def edit_image(
    images: List[UploadFile] = File(..., description="上传的图像文件（支持1-2张）"),
    prompt: str = Form(..., description="编辑图像的描述文本"),
    negative_prompt: str = Form("", description="不希望出现在图像中的内容"),
    num_inference_steps: int = Form(40, ge=20, le=100, description="推理步数"),
    true_cfg_scale: float = Form(4.0, ge=1.0, le=10.0, description="CFG尺度参数"),
    guidance_scale: float = Form(1.0, ge=1.0, le=10.0, description="指导尺度"),
    seed: int = Form(-1, description="随机种子，-1表示随机生成"),
    num_images: int = Form(1, ge=1, le=4, description="生成图像数量"),
):
    """
    图像编辑端点：基于上传的图像进行编辑
    
    - **images**: 上传1-2张图像作为编辑基础
    - **prompt**: 描述要进行的编辑操作
    - **negative_prompt**: 描述不希望出现的内容
    - **num_inference_steps**: 推理步数
    - **true_cfg_scale**: CFG尺度
    - **guidance_scale**: 指导尺度
    - **seed**: 随机种子
    - **num_images**: 生成图像数量
    """
    model_manager = get_model_manager()
    
    if not model_manager.is_image_edit_loaded:
        raise HTTPException(status_code=503, detail="图像编辑模型未加载")
    
    # 验证图像数量
    if len(images) > 2:
        raise HTTPException(status_code=400, detail="最多上传2张图像")
    
    if len(images) == 0:
        raise HTTPException(status_code=400, detail="请至少上传1张图像")
    
    # 读取并验证图像
    pil_images = []
    for image_file in images:
        pil_image = await read_and_validate_image(
            image_file,
            allowed_types=settings.security.allowed_image_types,
            max_size_mb=settings.security.max_upload_size_mb,
        )
        pil_images.append(pil_image)
    
    # 获取随机数生成器
    generator = model_manager.get_generator(seed)
    
    logger.info(f"开始编辑图像 | prompt: {prompt[:50]}... | 输入图像数: {len(pil_images)}")
    
    try:
        with torch.inference_mode():
            result = model_manager.image_edit_pipeline(
                image=pil_images,
                prompt=prompt,
                negative_prompt=negative_prompt if negative_prompt else None,
                generator=generator,
                true_cfg_scale=true_cfg_scale,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                num_images_per_prompt=num_images,
            )
        
        output_images = result.images
        logger.info(f"图像编辑成功 | 数量: {len(output_images)}")
        
        # 保存图像
        saved_images = save_images_to_temp(output_images, prefix="edited")
        
        if len(saved_images) == 1:
            filepath, filename = saved_images[0]
            return FileResponse(
                filepath,
                media_type="image/png",
                filename=filename,
            )
        else:
            image_paths = [path for path, _ in saved_images]
            zip_path = create_zip_from_images(image_paths)
            
            return FileResponse(
                zip_path,
                media_type="application/zip",
                filename=f"edited_images_{uuid.uuid4().hex[:8]}.zip",
            )
    
    except Exception as e:
        logger.error(f"图像编辑失败: {e}")
        raise HTTPException(status_code=500, detail=f"编辑失败: {str(e)}")


@router.post("/batch")
async def batch_edit(
    image: UploadFile = File(..., description="上传的单张图像文件"),
    prompts: str = Form(..., description="多个编辑提示，用|分隔"),
    negative_prompt: str = Form("", description="不希望出现在图像中的内容"),
    num_inference_steps: int = Form(40, ge=20, le=100, description="推理步数"),
    true_cfg_scale: float = Form(4.0, ge=1.0, le=10.0, description="CFG尺度参数"),
    seed: int = Form(-1, description="随机种子，-1表示随机生成"),
):
    """
    批量编辑端点：对同一张图像应用多个编辑提示
    
    - **image**: 上传单张图像
    - **prompts**: 多个编辑提示，用|分隔（例如："添加帽子|改变背景为海滩|添加太阳镜"）
    - **negative_prompt**: 描述不希望出现的内容
    - **num_inference_steps**: 推理步数
    - **seed**: 随机种子
    
    返回包含所有编辑结果的ZIP文件
    """
    model_manager = get_model_manager()
    
    if not model_manager.is_image_edit_loaded:
        raise HTTPException(status_code=503, detail="图像编辑模型未加载")
    
    # 解析提示列表
    prompt_list = [p.strip() for p in prompts.split("|") if p.strip()]
    
    if not prompt_list:
        raise HTTPException(status_code=400, detail="请提供至少一个有效的编辑提示")
    
    if len(prompt_list) > settings.generation.max_batch_prompts:
        raise HTTPException(
            status_code=400,
            detail=f"批量编辑提示数量不能超过 {settings.generation.max_batch_prompts}"
        )
    
    # 读取并验证图像
    pil_image = await read_and_validate_image(
        image,
        allowed_types=settings.security.allowed_image_types,
        max_size_mb=settings.security.max_upload_size_mb,
    )
    
    # 获取随机数生成器
    generator = model_manager.get_generator(seed)
    
    logger.info(f"开始批量编辑 | 提示数: {len(prompt_list)}")
    
    all_saved_images = []
    
    try:
        for i, prompt in enumerate(prompt_list):
            logger.info(f"处理提示 {i+1}/{len(prompt_list)}: {prompt[:30]}...")
            
            with torch.inference_mode():
                result = model_manager.image_edit_pipeline(
                    image=[pil_image],
                    prompt=prompt,
                    negative_prompt=negative_prompt if negative_prompt else None,
                    generator=generator,
                    true_cfg_scale=true_cfg_scale,
                    guidance_scale=1.0,
                    num_inference_steps=num_inference_steps,
                    num_images_per_prompt=1,
                )
            
            # 保存结果
            saved = save_images_to_temp(result.images, prefix=f"batch_{i}")
            all_saved_images.extend(saved)
        
        logger.info(f"批量编辑完成 | 总输出: {len(all_saved_images)}")
        
        # 打包所有结果
        image_paths = [path for path, _ in all_saved_images]
        zip_path = create_zip_from_images(image_paths)
        
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=f"batch_edit_{uuid.uuid4().hex[:8]}.zip",
        )
    
    except Exception as e:
        logger.error(f"批量编辑失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量编辑失败: {str(e)}")
