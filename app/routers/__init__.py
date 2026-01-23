"""
路由模块
"""

from .text_to_image import router as text_to_image_router
from .image_edit import router as image_edit_router
from .info import router as info_router

__all__ = ["text_to_image_router", "image_edit_router", "info_router"]
