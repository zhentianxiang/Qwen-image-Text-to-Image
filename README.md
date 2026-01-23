# Qwen Image Service

> 多模态图像生成与编辑 API 服务，集成 Qwen-Image-2512 文生图和 Qwen-Image-Edit-2511 图像编辑功能。

## ✨ 功能特性

- 🎨 **文生图** - 根据文字描述生成高质量图像
- ✏️ **图像编辑** - 基于上传图像进行智能编辑
- 📦 **批量编辑** - 对同一张图像应用多个编辑效果
- 🖥️ **Web 前端** - 现代化的图形操作界面
- 🐳 **Docker 部署** - 一键部署，开箱即用

## 📥 模型下载

使用前请先下载模型文件到 `./models` 目录：

| 模型 | 功能 | 下载地址 |
|------|------|----------|
| **Qwen-Image-2512** | 文生图 | [hf-mirror.com/Qwen/Qwen-Image-2512](https://hf-mirror.com/Qwen/Qwen-Image-2512) |
| **Qwen-Image-Edit-2511** | 图像编辑 | [hf-mirror.com/Qwen/Qwen-Image-Edit-2511](https://hf-mirror.com/Qwen/Qwen-Image-Edit-2511) |

### 下载方式

```bash
# 安装 huggingface-cli
pip install huggingface_hub

# 设置镜像源（国内加速）
export HF_ENDPOINT=https://hf-mirror.com

# 下载文生图模型
huggingface-cli download Qwen/Qwen-Image-2512 --local-dir ./models/Qwen-Image-2512

# 下载图像编辑模型
huggingface-cli download Qwen/Qwen-Image-Edit-2511 --local-dir ./models/Qwen-Image-Edit-2511
```

> 💡 **模型大小**：两个模型合计约 30GB，请确保有足够磁盘空间

## 📁 项目结构

```
qwen-image/
├── app/                          # 后端应用
│   ├── __init__.py
│   ├── main.py                   # FastAPI应用入口
│   ├── config.py                 # 配置管理模块
│   ├── models/                   # 模型管理
│   │   ├── __init__.py
│   │   └── pipelines.py          # 模型加载和管理
│   ├── routers/                  # API路由
│   │   ├── __init__.py
│   │   ├── text_to_image.py      # 文生图端点
│   │   ├── image_edit.py         # 图像编辑端点
│   │   └── info.py               # 系统信息端点
│   ├── schemas/                  # 数据模型
│   │   ├── __init__.py
│   │   └── requests.py           # 请求/响应模型
│   └── utils/                    # 工具模块
│       ├── __init__.py
│       ├── logger.py             # 日志配置
│       └── image_utils.py        # 图像处理工具
├── frontend/                     # 前端应用
│   ├── index.html               # 主页面
│   ├── style.css                # 样式
│   ├── app.js                   # 交互逻辑
│   ├── nginx.conf               # Nginx配置
│   └── Dockerfile               # 前端容器
├── config/
│   └── config.yaml               # 主配置文件
├── models/                       # 模型目录（需下载）
│   ├── Qwen-Image-2512/
│   └── Qwen-Image-Edit-2511/
├── .env.example                  # 环境变量示例
├── requirements.txt              # Python依赖
├── Dockerfile                    # Docker镜像构建
├── docker-compose.yml            # Docker Compose编排
├── API.md                        # API文档
└── README.md                     # 本文件
```

## 🚀 快速开始

### 方式一：Docker部署（推荐）

```bash
# 1. 下载模型到 ./models 目录（见上方说明）

# 2. 使用 Docker Compose 启动（需要 NVIDIA Docker）
docker-compose up -d --build

# 3. 查看日志
docker-compose logs -f

# 4. 停止服务
docker-compose down
```

**访问地址：**
- 前端界面：http://localhost:3000
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

> 💡 Docker镜像使用中科大镜像源加速构建，HuggingFace使用 hf-mirror.com 加速模型下载

### 方式二：本地运行

#### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 2. 配置

##### 方式A：使用环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑 .env 文件
vim .env
```

##### 方式B：使用配置文件

编辑 `config/config.yaml` 文件。

> 💡 环境变量优先级高于配置文件

#### 3. 启动服务

```bash
# 方式一：使用模块运行
python -m app.main

# 方式二：使用uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 开发模式（自动重载）
uvicorn app.main:app --reload
```

#### 4. 访问API

- API文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

## 🖼️ 前端界面

项目包含一个现代化的 Web 前端，支持：

- 📝 文生图 - 输入描述文字生成图像
- ✂️ 图像编辑 - 上传图片 + 描述进行编辑
- 🔄 批量编辑 - 一张图应用多个编辑效果
- ⚙️ 参数调节 - 宽高比、推理步数、CFG、种子等
- 📡 状态监控 - 实时显示后端服务状态

**首次使用**：点击左下角「设置」，配置后端 API 地址。

## 📚 API端点

详细文档请查看 [API.md](./API.md)

### 文生图

```bash
POST /text-to-image
```

参数：
- `prompt` (必填): 生成图像的描述文本
- `negative_prompt`: 不希望出现的内容
- `aspect_ratio`: 宽高比 (1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3)
- `num_inference_steps`: 推理步数 (20-100)
- `true_cfg_scale`: CFG尺度 (1.0-10.0)
- `seed`: 随机种子 (-1为随机)
- `num_images`: 生成数量 (1-4)

### 图像编辑

```bash
POST /image-edit
```

参数：
- `images` (必填): 上传的图像文件（1-2张）
- `prompt` (必填): 编辑描述
- `negative_prompt`: 不希望出现的内容
- `num_inference_steps`: 推理步数
- `true_cfg_scale`: CFG尺度
- `guidance_scale`: 指导尺度
- `seed`: 随机种子
- `num_images`: 生成数量

### 批量编辑

```bash
POST /image-edit/batch
```

参数：
- `image` (必填): 上传的单张图像
- `prompts` (必填): 多个编辑提示，用`|`分隔
- `negative_prompt`: 不希望出现的内容
- `num_inference_steps`: 推理步数
- `seed`: 随机种子

### 系统信息

```bash
GET /health          # 健康检查
GET /models          # 模型信息
GET /aspect-ratios   # 支持的宽高比
```

### 快速测试

```bash
# 健康检查
curl http://localhost:8000/health

# 文生图
curl -X POST http://localhost:8000/text-to-image \
  -F "prompt=一只可爱的橘猫在阳光下打盹" \
  -F "negative_prompt=模糊,低质量" \
  -F "aspect_ratio=1:1" \
  --output cat.png

# 图像编辑
curl -X POST http://localhost:8000/image-edit \
  -F "images=@cat.png" \
  -F "prompt=给猫戴上一顶帽子" \
  --output cat_hat.png
```

## ⚙️ 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `APP_HOST` | 0.0.0.0 | 服务监听地址 |
| `APP_PORT` | 8000 | 服务端口 |
| `APP_DEBUG` | false | 调试模式 |
| `TEXT_TO_IMAGE_MODEL` | Qwen/Qwen-Image-2512 | 文生图模型 |
| `IMAGE_EDIT_MODEL` | Qwen/Qwen-Image-Edit-2511 | 图像编辑模型 |
| `DEVICE` | cuda | 计算设备 (cuda/cpu) |
| `LOG_LEVEL` | INFO | 日志级别 |
| `MAX_UPLOAD_SIZE_MB` | 20 | 最大上传文件大小 |
| `CORS_ORIGINS` | ["*"] | CORS允许的源 |

### 支持的宽高比

| 宽高比 | 尺寸 (宽×高) |
|--------|-------------|
| `1:1` | 1024 × 1024 |
| `16:9` | 1664 × 928 |
| `9:16` | 928 × 1664 |
| `4:3` | 1472 × 1104 |
| `3:4` | 1104 × 1472 |
| `3:2` | 1584 × 1056 |
| `2:3` | 1056 × 1584 |

### GPU内存优化

服务默认启用以下优化：
- `enable_model_cpu_offload()`: 自动将未使用的模型部分卸载到CPU
- `enable_attention_slicing()`: 减少注意力层内存占用

## 🔧 开发

### 代码结构

- `app/config.py`: 配置管理，支持YAML和环境变量
- `app/models/pipelines.py`: 模型单例管理器
- `app/routers/`: 按功能分离的API路由
- `app/utils/`: 通用工具函数

### 添加新功能

1. 在 `app/routers/` 创建新路由文件
2. 在 `app/routers/__init__.py` 导出路由
3. 在 `app/main.py` 注册路由

## 🐳 Docker说明

### 镜像加速

Dockerfile 已配置以下中国镜像源：

| 类型 | 镜像源 |
|------|--------|
| APT | mirrors.ustc.edu.cn |
| PyPI | mirrors.ustc.edu.cn/pypi/web/simple |
| HuggingFace | hf-mirror.com |

### GPU支持

Docker Compose 已配置 NVIDIA GPU 支持，需要：

1. 安装 [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
2. 确保 `nvidia-smi` 命令可用

```bash
# 验证GPU支持
docker run --rm --gpus all nvidia/cuda:12.4-base nvidia-smi
```

### 数据持久化

| 路径 | 说明 |
|------|------|
| `./models:/app/models` | 模型文件目录 |
| `./config:/app/config` | 配置文件目录 |
| `./logs:/app/logs` | 日志文件目录 |
| `huggingface_cache` | 模型缓存，避免重启后重新下载 |

## 📝 注意事项

1. **GPU内存**: 两个模型同时加载需要较大显存，建议使用24GB以上GPU
2. **首次启动**: 首次运行会下载模型，可能需要较长时间
3. **生产环境**: 请修改CORS配置，不要使用`["*"]`
4. **临时文件**: 服务会自动清理24小时前的生成文件
5. **Docker健康检查**: start_period 设为120秒，等待模型加载

## 🔗 相关链接

- [Qwen-Image-2512 模型页面](https://hf-mirror.com/Qwen/Qwen-Image-2512)
- [Qwen-Image-Edit-2511 模型页面](https://hf-mirror.com/Qwen/Qwen-Image-Edit-2511)
- [Qwen-Image 技术报告](https://arxiv.org/abs/2508.02324)
- [Qwen 官方 GitHub](https://github.com/QwenLM)

## 📄 License

MIT License
