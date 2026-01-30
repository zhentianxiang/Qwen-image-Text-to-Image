"""
图生视频路由
"""

from typing import Dict, Any, Optional
import json
import uuid
from datetime import datetime
import os
import shutil

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import get_db, TaskHistory
from ..schemas.requests import ImageToVideoRequest
from ..services.auth import get_current_user
from ..services.task_queue import get_task_queue
from ..utils.logger import get_logger
from ..config import settings
from ..models.database import User
from ..services.task_history import check_and_update_quota, get_task_history_by_id

logger = get_logger(__name__)
router = APIRouter(prefix="/generate/image-to-video", tags=["图生视频"])

def _run_image_to_video_inference(
    prompt: str,
    image_path: str,
    negative_prompt: str = "",
    num_frames: int = 49,
    num_inference_steps: int = 50,
    guidance_scale: float = 6.0,
    seed: int = -1,
    **kwargs
) -> Dict[str, Any]:
    """
    运行图生视频推理 (由 Worker 进程调用)
    """
    try:
        from ..models.pipelines import get_model_manager
        from diffusers.utils import export_to_video, load_image
        
        manager = get_model_manager()
        pipe = manager.video_pipeline
        
        if pipe is None:
            raise RuntimeError("Video pipeline not initialized")
            
        generator = manager.get_generator(seed)
        
        # 加载源图片
        if not os.path.exists(image_path):
             raise FileNotFoundError(f"Source image not found: {image_path}")
        
        source_image = load_image(image_path)
        
        logger.info(f"Starting image-to-video generation: {prompt}")
        
        frames = pipe(
            prompt=prompt,
            image=source_image,
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
        
        user_id = kwargs.get("user_id")
        if user_id and settings.storage.organize_by_user:
             output_dir = os.path.join(output_dir, f"user_{user_id}")
             
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"i2v_{uuid.uuid4().hex}.mp4"
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
        logger.error(f"Image-to-video inference failed: {e}")
        raise e


@router.post("", response_model=Dict[str, Any])
async def create_image_to_video_task(
    prompt: str = Form(...),
    negative_prompt: str = Form(""),
    num_frames: int = Form(49),
    num_inference_steps: int = Form(50),
    guidance_scale: float = Form(6.0),
    seed: int = Form(-1),
    image: Optional[UploadFile] = File(None),
    source_task_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建图生视频任务
    
    支持两种方式提供图片：
    1. 上传图片文件 (image)
    2. 使用之前的任务结果 (source_task_id)
    """
    # 1. 检查配额 (假设消耗 5 积分)
    cost = 5
    allowed, message, remaining = await check_and_update_quota(current_user.id, count=cost)
    if not allowed:
        raise HTTPException(status_code=429, detail=message)
    
    # 2. 处理图片源
    image_path = None
    
    if source_task_id:
        # 从历史任务获取
        task = await get_task_history_by_id(source_task_id)
        if not task:
            raise HTTPException(status_code=404, detail="源任务不存在")
        if task.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="无权使用此任务结果")
        if not task.result_path or not os.path.exists(task.result_path):
            raise HTTPException(status_code=404, detail="源任务结果文件不存在")
        image_path = task.result_path
    
    elif image:
        # 保存上传的图片
        temp_dir = os.path.join(settings.storage.output_dir, "temp_uploads")
        os.makedirs(temp_dir, exist_ok=True)
        filename = f"upload_{uuid.uuid4().hex}_{image.filename}"
        image_path = os.path.join(temp_dir, filename)
        
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
            
    else:
        raise HTTPException(status_code=400, detail="必须提供 image 或 source_task_id")

    # 3. 创建任务
    task_queue = get_task_queue()
    task_id = await task_queue.add_task(
        task_type="image_to_video",
        params={
            "prompt": prompt,
            "image_path": image_path,
            "negative_prompt": negative_prompt,
            "num_frames": num_frames,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "seed": seed,
            "user_id": current_user.id
        },
        user_id=current_user.id
    )
    
    # 4. 记录到数据库
    task_history = TaskHistory(
        task_id=task_id,
        user_id=current_user.id,
        task_type="image_to_video",
        prompt=prompt,
        negative_prompt=negative_prompt,
        status="pending",
        parameters=json.dumps({
            "prompt": prompt,
            "source": "upload" if image else source_task_id,
            "num_frames": num_frames,
            "steps": num_inference_steps
        }),
    )
    db.add(task_history)
    await db.commit()
    
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "任务已提交队列",
        "quota_remaining": remaining
    }
