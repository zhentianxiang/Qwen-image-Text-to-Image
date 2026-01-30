"""
文生视频路由
"""

from typing import Dict, Any
import json
import uuid
from datetime import datetime
import os

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import get_db, TaskHistory
from ..schemas.requests import TextToVideoRequest
from ..services.auth import get_current_user
from ..services.task_queue import get_task_queue, TaskType
from ..utils.logger import get_logger
from ..config import settings
from ..models.database import User
from ..services.task_history import check_and_update_quota

logger = get_logger(__name__)
router = APIRouter(prefix="/generate/text-to-video", tags=["文生视频"])

def _run_text_to_video_inference(
    prompt: str,
    negative_prompt: str = "",
    num_frames: int = 49,
    num_inference_steps: int = 50,
    guidance_scale: float = 6.0,
    seed: int = -1,
    **kwargs
) -> Dict[str, Any]:
    """
    运行文生视频推理 (由 Worker 进程调用)
    """
    try:
        from ..models.pipelines import get_model_manager
        from diffusers.utils import export_to_video
        
        manager = get_model_manager()
        
        # 此时 manager._load_text_to_video_model() 应该已经在 worker 中被调用
        pipe = manager.video_pipeline
        
        if pipe is None:
            raise RuntimeError("Video pipeline not initialized")
            
        generator = manager.get_generator(seed)
        
        logger.info(f"Starting text-to-video generation: {prompt}")
        
        frames = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_frames=num_frames,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            generator=generator,
            **kwargs
        ).frames[0]
        
        # 保存结果
        output_dir = settings.storage.output_dir
        if settings.storage.organize_by_date:
            date_str = datetime.now().strftime("%Y/%m/%d")
            output_dir = os.path.join(output_dir, date_str)
        
        # 如果是 Worker 调用，user_id 可能在 kwargs 里
        user_id = kwargs.get("user_id")
        if user_id and settings.storage.organize_by_user:
             output_dir = os.path.join(output_dir, f"user_{user_id}")
             
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"t2v_{uuid.uuid4().hex}.mp4"
        file_path = os.path.join(output_dir, filename)
        
        export_to_video(frames, file_path, fps=8)
        
        return {
            "success": True,
            "file_path": file_path,
            "filename": filename,
            "media_type": "video/mp4",
            "seed": seed
        }
        
    except Exception as e:
        logger.error(f"Text-to-video inference failed: {e}")
        raise e


@router.post("", response_model=Dict[str, Any])
async def create_text_to_video_task(
    request: TextToVideoRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建文生视频任务
    """
    # 1. 检查配额 (视频生成消耗较大，这里假设消耗 5 个积分)
    cost = 5
    allowed, message, remaining = await check_and_update_quota(current_user.id, count=cost)
    if not allowed:
        raise HTTPException(status_code=429, detail=message)
        
    # 2. 创建任务
    task_queue = get_task_queue()
    task_id = await task_queue.add_task(
        task_type="text_to_video",
        params={
            "prompt": request.prompt,
            "negative_prompt": request.negative_prompt,
            "num_frames": request.num_frames,
            "num_inference_steps": request.num_inference_steps,
            "guidance_scale": request.guidance_scale,
            "seed": request.seed,
            "user_id": current_user.id
        },
        user_id=current_user.id
    )
    
    # 3. 记录到数据库
    task_history = TaskHistory(
        task_id=task_id,
        user_id=current_user.id,
        task_type="text_to_video",
        prompt=request.prompt,
        negative_prompt=request.negative_prompt,
        status="pending",
        parameters=json.dumps(request.model_dump()),
    )
    db.add(task_history)
    await db.commit()
    
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "任务已提交队列",
        "quota_remaining": remaining
    }
