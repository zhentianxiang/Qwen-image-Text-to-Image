"""
Qwen Image Service - 主程序入口

多模态图像生成与编辑服务
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .models import get_model_manager
from .routers import text_to_image_router, image_edit_router, info_router
from .utils.logger import setup_logger, get_logger
from .utils.image_utils import cleanup_old_temp_files


# 初始化日志
setup_logger(
    name="qwen_image",
    level=settings.logging.level,
    log_format=settings.logging.format,
    file_path=settings.logging.file_path if settings.logging.file_enabled else None,
)
logger = get_logger("qwen_image")


async def cleanup_task():
    """定期清理临时文件的后台任务"""
    while True:
        await asyncio.sleep(settings.cleanup.check_interval_minutes * 60)
        if settings.cleanup.enabled:
            try:
                cleanup_old_temp_files(max_age_hours=settings.cleanup.max_age_hours)
            except Exception as e:
                logger.error(f"清理临时文件时出错: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    应用生命周期管理
    
    启动时加载模型，关闭时释放资源
    """
    logger.info("=" * 50)
    logger.info("Qwen Image Service 正在启动...")
    logger.info("=" * 50)
    
    # 加载模型
    model_manager = get_model_manager()
    try:
        await model_manager.load_models()
    except Exception as e:
        logger.error(f"模型加载失败: {e}")
        raise
    
    # 启动清理任务
    cleanup_task_handle = None
    if settings.cleanup.enabled:
        cleanup_task_handle = asyncio.create_task(cleanup_task())
        logger.info(f"临时文件清理任务已启动 (间隔: {settings.cleanup.check_interval_minutes}分钟)")
    
    logger.info("=" * 50)
    logger.info("服务启动完成！")
    logger.info(f"API文档: http://{settings.app.host}:{settings.app.port}/docs")
    logger.info("=" * 50)
    
    yield
    
    # 清理资源
    logger.info("正在关闭服务...")
    
    if cleanup_task_handle:
        cleanup_task_handle.cancel()
        try:
            await cleanup_task_handle
        except asyncio.CancelledError:
            pass
    
    await model_manager.unload_models()
    logger.info("服务已关闭")


# 创建FastAPI应用
app = FastAPI(
    title=settings.app.app_name,
    description=settings.app.app_description,
    version=settings.app.app_version,
    lifespan=lifespan,
)

# 添加CORS中间件
# 注意：当 allow_origins=["*"] 时，allow_credentials 必须为 False（CORS规范要求）
cors_origins = settings.security.cors_origins
cors_credentials = settings.security.cors_allow_credentials

# 如果 origins 包含 "*"，则不能使用 credentials
if "*" in cors_origins:
    cors_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_credentials,
    allow_methods=settings.security.cors_allow_methods,
    allow_headers=settings.security.cors_allow_headers,
)

# 注册路由
app.include_router(text_to_image_router)
app.include_router(image_edit_router)
app.include_router(info_router)


@app.get("/")
async def root():
    """根路径 - 返回服务信息"""
    return {
        "name": settings.app.app_name,
        "version": settings.app.app_version,
        "docs": "/docs",
        "health": "/health",
    }


def main():
    """主函数 - 用于直接运行"""
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
    )


if __name__ == "__main__":
    main()
