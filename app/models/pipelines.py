"""
模型管理模块

负责加载和管理AI模型的生命周期
"""

from typing import Optional, Any
import torch

from ..utils.logger import get_logger
from ..config import settings

logger = get_logger(__name__)


class ModelManager:
    """
    模型管理器
    
    单例模式，负责管理文生图、图像编辑、文生视频、图生视频模型的加载和推理。
    核心逻辑：互斥加载 (Lazy Loading + Hot Swapping)
    """
    
    _instance: Optional["ModelManager"] = None
    
    def __new__(cls) -> "ModelManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._text_to_image_pipeline = None
        self._image_edit_pipeline = None
        self._video_pipeline = None # 复用，CogVideoX 的 T2V 和 I2V 管道对象不同
        self._current_video_model_type = None # "text_to_video" or "image_to_video"
        
        self._device = None
        self._dtype = None
        self._initialized = True
    
    @property
    def text_to_image_pipeline(self) -> Optional[Any]:
        return self._text_to_image_pipeline
    
    @property
    def image_edit_pipeline(self) -> Optional[Any]:
        return self._image_edit_pipeline

    @property
    def video_pipeline(self) -> Optional[Any]:
        return self._video_pipeline
    
    @property
    def device(self) -> str:
        if self._device is None:
            if settings.models.device == "cuda" and torch.cuda.is_available():
                self._device = "cuda"
            else:
                self._device = "cpu"
        return self._device
    
    @property
    def dtype(self) -> torch.dtype:
        if self._dtype is None:
            if self.device == "cuda":
                # A40/3090/4090 推荐 bfloat16
                self._dtype = torch.bfloat16
            else:
                self._dtype = torch.float32
        return self._dtype
    
    @property
    def is_text_to_image_loaded(self) -> bool:
        return self._text_to_image_pipeline is not None

    @property
    def is_image_edit_loaded(self) -> bool:
        return self._image_edit_pipeline is not None

    @property
    def is_video_model_loaded(self) -> bool:
        return self._video_pipeline is not None
    
    @property
    def gpu_available(self) -> bool:
        return torch.cuda.is_available()
    
    @property
    def gpu_count(self) -> int:
        return torch.cuda.device_count() if self.gpu_available else 0

    def _unload_all_except(self, keep_type: str = None) -> None:
        """
        卸载除指定类型以外的所有模型
        """
        import gc
        unloaded = False

        # 卸载文生图
        if keep_type != "text_to_image" and self._text_to_image_pipeline is not None:
            logger.info("正在卸载文生图模型以释放显存...")
            del self._text_to_image_pipeline
            self._text_to_image_pipeline = None
            unloaded = True

        # 卸载图像编辑
        if keep_type != "image_edit" and self._image_edit_pipeline is not None:
            logger.info("正在卸载图像编辑模型以释放显存...")
            del self._image_edit_pipeline
            self._image_edit_pipeline = None
            unloaded = True

        # 卸载视频模型
        # 如果 keep_type 是 video 但子类型不同，也要卸载
        is_video_request = keep_type in ["text_to_video", "image_to_video"]
        if self._video_pipeline is not None:
            should_unload_video = True
            if is_video_request and self._current_video_model_type == keep_type:
                should_unload_video = False
            
            if should_unload_video:
                logger.info(f"正在卸载视频模型 ({self._current_video_model_type}) 以释放显存...")
                del self._video_pipeline
                self._video_pipeline = None
                self._current_video_model_type = None
                unloaded = True

        if unloaded and self.gpu_available:
            gc.collect()
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

    async def _load_text_to_image_model(self) -> None:
        """加载文生图模型"""
        if self._text_to_image_pipeline is not None:
            return

        self._unload_all_except("text_to_image")
        
        try:
            logger.info(f"正在加载文生图模型: {settings.models.text_to_image_model}")
            from diffusers import DiffusionPipeline
            
            device_map = None
            if self.device == "cuda" and self.gpu_count > 1:
                device_map = "balanced"
            
            self._text_to_image_pipeline = DiffusionPipeline.from_pretrained(
                settings.models.text_to_image_model,
                torch_dtype=self.dtype,
                trust_remote_code=True,
                device_map=device_map,
            )
            
            if self.device == "cuda":
                # 显存优化
                try:
                    self._text_to_image_pipeline.enable_vae_tiling()
                    self._text_to_image_pipeline.enable_vae_slicing()
                except Exception as e:
                    logger.warning(f"VAE Optimization Warning: {e}")

                if self.gpu_count == 1:
                     # A40 48G 一般不需要 offload Qwen，但为了保险起见，如果不跑视频，可以常驻
                     # 为了极致并发，这里暂时不开启 offload，除非显存真的很小
                     # self._text_to_image_pipeline.enable_model_cpu_offload()
                     pass
                
                # 移动到 GPU (如果是单卡且没开 offload)
                if not device_map:
                    self._text_to_image_pipeline.to(self.device)

            logger.info("✅ 文生图模型加载完成")
            
        except Exception as e:
            logger.error(f"文生图模型加载失败: {e}")
            raise
    
    async def _load_image_edit_model(self) -> None:
        """加载图像编辑模型"""
        if self._image_edit_pipeline is not None:
            return

        self._unload_all_except("image_edit")

        try:
            logger.info(f"正在加载图像编辑模型: {settings.models.image_edit_model}")
            from diffusers import QwenImageEditPlusPipeline
            
            device_map = None
            if self.device == "cuda" and self.gpu_count > 1:
                device_map = "balanced"
            
            self._image_edit_pipeline = QwenImageEditPlusPipeline.from_pretrained(
                settings.models.image_edit_model,
                torch_dtype=self.dtype,
                trust_remote_code=True,
                device_map=device_map,
            )
            
            if self.device == "cuda":
                try:
                    self._image_edit_pipeline.enable_vae_tiling()
                    self._image_edit_pipeline.enable_vae_slicing()
                except Exception:
                    pass
                
                if not device_map:
                    self._image_edit_pipeline.to(self.device)

            logger.info("✅ 图像编辑模型加载完成")
            
        except Exception as e:
            logger.error(f"图像编辑模型加载失败: {e}")
            raise

    async def _load_text_to_video_model(self) -> None:
        """加载文生视频模型 (CogVideoX-5B)"""
        if self._video_pipeline is not None and self._current_video_model_type == "text_to_video":
            return

        self._unload_all_except("text_to_video")

        try:
            logger.info(f"正在加载文生视频模型: {settings.models.text_to_video_model}")
            from diffusers import CogVideoXPipeline
            
            self._video_pipeline = CogVideoXPipeline.from_pretrained(
                settings.models.text_to_video_model,
                torch_dtype=self.dtype
            )

            # A40 优化
            if self.device == "cuda":
                self._video_pipeline.enable_vae_slicing()
                # self._video_pipeline.enable_model_cpu_offload() # A40 不需要 offload 5B 模型
                self._video_pipeline.to(self.device)
            
            self._current_video_model_type = "text_to_video"
            logger.info("✅ 文生视频模型加载完成")

        except Exception as e:
            logger.error(f"文生视频模型加载失败: {e}")
            raise

    async def _load_image_to_video_model(self) -> None:
        """加载图生视频模型 (CogVideoX-5B-I2V)"""
        if self._video_pipeline is not None and self._current_video_model_type == "image_to_video":
            return

        self._unload_all_except("image_to_video")

        try:
            logger.info(f"正在加载图生视频模型: {settings.models.image_to_video_model}")
            from diffusers import CogVideoXImageToVideoPipeline
            
            self._video_pipeline = CogVideoXImageToVideoPipeline.from_pretrained(
                settings.models.image_to_video_model,
                torch_dtype=self.dtype
            )

            if self.device == "cuda":
                self._video_pipeline.enable_vae_slicing()
                # self._video_pipeline.enable_vae_tiling() # 某些版本I2V可能支持
                self._video_pipeline.to(self.device)
            
            self._current_video_model_type = "image_to_video"
            logger.info("✅ 图生视频模型加载完成")

        except Exception as e:
            logger.error(f"图生视频模型加载失败: {e}")
            raise

    async def unload_models(self) -> None:
        """卸载所有模型"""
        self._unload_all_except(keep_type=None)
        logger.info("所有模型已卸载")

    def get_generator(self, seed: int = -1) -> Optional[torch.Generator]:
        if seed == -1:
            return None
        generator = torch.Generator(device=self.device)
        generator.manual_seed(seed)
        return generator

# 全局单例
_model_manager: Optional[ModelManager] = None

def get_model_manager() -> ModelManager:
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager