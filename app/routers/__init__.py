from .text_to_image import router as text_to_image_router
from .image_edit import router as image_edit_router
from .text_to_video import router as text_to_video_router
from .image_to_video import router as image_to_video_router
from .info import router as info_router
from .tasks import router as tasks_router
from .auth import router as auth_router

__all__ = [
    "text_to_image_router",
    "image_edit_router",
    "text_to_video_router",
    "image_to_video_router",
    "info_router",
    "tasks_router",
    "auth_router",
]