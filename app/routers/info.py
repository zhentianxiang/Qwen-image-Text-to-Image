"""
信息查询路由模块
"""

from fastapi import APIRouter

from ..config import settings
from ..models import get_model_manager
from ..schemas import HealthResponse, ModelInfo, ModelsResponse

router = APIRouter(tags=["系统信息"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    健康检查端点
    
    返回服务状态和模型加载情况
    """
    model_manager = get_model_manager()
    
    return HealthResponse(
        status="healthy",
        text_to_image_model_loaded=model_manager.is_text_to_image_loaded,
        image_edit_model_loaded=model_manager.is_image_edit_loaded,
        gpu_available=model_manager.gpu_available,
        gpu_count=model_manager.gpu_count,
    )


@router.get("/models", response_model=ModelsResponse)
async def list_models():
    """
    列出可用模型信息
    
    返回所有支持的模型及其状态
    """
    model_manager = get_model_manager()
    
    return ModelsResponse(
        text_to_image=ModelInfo(
            name=settings.models.text_to_image_model,
            description="Qwen-Image-2512 文生图模型",
            capabilities=["text-to-image", "image generation"],
            status="loaded" if model_manager.is_text_to_image_loaded else "not loaded",
        ),
        image_edit=ModelInfo(
            name=settings.models.image_edit_model,
            description="Qwen-Image-Edit-2511 图像编辑模型",
            capabilities=["image-to-image", "image editing", "multi-image composition"],
            status="loaded" if model_manager.is_image_edit_loaded else "not loaded",
        ),
    )


@router.get("/aspect-ratios")
async def get_aspect_ratios():
    """
    获取支持的宽高比
    
    返回所有支持的图像宽高比及其对应的像素尺寸
    """
    return settings.aspect_ratios
