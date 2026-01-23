"""
配置管理模块

支持从YAML配置文件和环境变量加载配置
环境变量优先级高于配置文件
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from functools import lru_cache

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"


def load_yaml_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """加载YAML配置文件"""
    if config_path is None:
        config_path = CONFIG_DIR / "config.yaml"
    
    if not config_path.exists():
        return {}
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class AppSettings(BaseSettings):
    """应用配置"""
    
    # 服务配置
    app_name: str = Field(default="Qwen 多模态图像API服务")
    app_description: str = Field(
        default="集成文生图(Qwen-Image-2512)和图像编辑(Qwen-Image-Edit-2511)功能"
    )
    app_version: str = Field(default="1.0.0")
    host: str = Field(default="0.0.0.0", alias="APP_HOST")
    port: int = Field(default=8000, alias="APP_PORT")
    debug: bool = Field(default=False, alias="APP_DEBUG")
    
    model_config = {"env_prefix": "", "extra": "ignore"}


class ModelSettings(BaseSettings):
    """模型配置"""
    
    text_to_image_model: str = Field(
        default="Qwen/Qwen-Image-2512",
        alias="TEXT_TO_IMAGE_MODEL"
    )
    image_edit_model: str = Field(
        default="Qwen/Qwen-Image-Edit-2511",
        alias="IMAGE_EDIT_MODEL"
    )
    models_dir: str = Field(default="./models", alias="MODELS_DIR")
    device: str = Field(default="cuda", alias="DEVICE")
    
    model_config = {"env_prefix": "", "extra": "ignore"}


class GenerationSettings(BaseSettings):
    """图像生成配置"""
    
    default_num_inference_steps: int = Field(default=50, alias="DEFAULT_NUM_INFERENCE_STEPS")
    default_guidance_scale: float = Field(default=7.5, alias="DEFAULT_GUIDANCE_SCALE")
    default_true_cfg_scale: float = Field(default=4.0, alias="DEFAULT_TRUE_CFG_SCALE")
    default_width: int = Field(default=1024, alias="DEFAULT_WIDTH")
    default_height: int = Field(default=1024, alias="DEFAULT_HEIGHT")
    
    min_inference_steps: int = Field(default=20)
    max_inference_steps: int = Field(default=100)
    max_images_per_request: int = Field(default=4)
    max_batch_prompts: int = Field(default=10)
    
    model_config = {"env_prefix": "", "extra": "ignore"}


class SecuritySettings(BaseSettings):
    """安全配置"""
    
    max_upload_size_mb: int = Field(default=20, alias="MAX_UPLOAD_SIZE_MB")
    allowed_image_types: List[str] = Field(
        default=["image/jpeg", "image/png", "image/webp"]
    )
    
    # CORS
    cors_origins: List[str] = Field(default=["*"])
    cors_allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(default=["*"])
    cors_allow_headers: List[str] = Field(default=["*"])
    
    model_config = {"env_prefix": "", "extra": "ignore"}
    
    def __init__(self, **data):
        import json
        
        # 处理 CORS_ORIGINS 环境变量
        if "CORS_ORIGINS" in os.environ:
            cors_value = os.environ["CORS_ORIGINS"].strip()
            # 尝试解析 JSON 数组格式，如 ["*"] 或 ["http://a.com"]
            if cors_value.startswith("["):
                try:
                    data["cors_origins"] = json.loads(cors_value)
                except json.JSONDecodeError:
                    data["cors_origins"] = [cors_value]
            # 单个 * 或逗号分隔的值
            elif cors_value == "*":
                data["cors_origins"] = ["*"]
            else:
                data["cors_origins"] = [s.strip() for s in cors_value.split(",")]
        
        # 处理 ALLOWED_IMAGE_TYPES 环境变量
        if "ALLOWED_IMAGE_TYPES" in os.environ:
            types_value = os.environ["ALLOWED_IMAGE_TYPES"].strip()
            if types_value.startswith("["):
                try:
                    data["allowed_image_types"] = json.loads(types_value)
                except json.JSONDecodeError:
                    data["allowed_image_types"] = [types_value]
            else:
                data["allowed_image_types"] = [s.strip() for s in types_value.split(",")]
        
        super().__init__(**data)


class LoggingSettings(BaseSettings):
    """日志配置"""
    
    level: str = Field(default="INFO", alias="LOG_LEVEL")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_enabled: bool = Field(default=False)
    file_path: str = Field(default="./logs/app.log")
    
    model_config = {"env_prefix": "", "extra": "ignore"}


class CleanupSettings(BaseSettings):
    """临时文件清理配置"""
    
    enabled: bool = Field(default=True, alias="AUTO_CLEANUP_ENABLED")
    max_age_hours: int = Field(default=24, alias="TEMP_FILE_MAX_AGE_HOURS")
    check_interval_minutes: int = Field(default=60)
    
    model_config = {"env_prefix": "", "extra": "ignore"}


class Settings:
    """统一配置管理类"""
    
    def __init__(self, config_path: Optional[Path] = None):
        # 加载YAML配置
        yaml_config = load_yaml_config(config_path)
        
        # 初始化各子配置
        self.app = AppSettings(**yaml_config.get("app", {}))
        self.models = ModelSettings(**yaml_config.get("models", {}))
        self.generation = GenerationSettings(**yaml_config.get("generation", {}))
        self.security = SecuritySettings(**yaml_config.get("security", {}))
        self.logging = LoggingSettings(**yaml_config.get("logging", {}))
        self.cleanup = CleanupSettings(**yaml_config.get("cleanup", {}))
        
        # 加载宽高比配置
        self._aspect_ratios = yaml_config.get("aspect_ratios", {
            "1:1": [1024, 1024],
            "16:9": [1664, 928],
            "9:16": [928, 1664],
            "4:3": [1472, 1104],
            "3:4": [1104, 1472],
            "3:2": [1584, 1056],
            "2:3": [1056, 1584],
        })
    
    @property
    def aspect_ratios(self) -> Dict[str, Tuple[int, int]]:
        """获取支持的宽高比"""
        return {k: tuple(v) for k, v in self._aspect_ratios.items()}
    
    def get_aspect_ratio_size(self, ratio: str) -> Tuple[int, int]:
        """根据宽高比获取尺寸"""
        if ratio in self._aspect_ratios:
            return tuple(self._aspect_ratios[ratio])
        return (self.generation.default_width, self.generation.default_height)


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 便捷访问
settings = get_settings()
