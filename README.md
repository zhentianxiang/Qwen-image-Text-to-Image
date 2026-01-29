# 造梦AI

> 🚀 **私有化 AI 绘画与修图平台**
>
> 基于 Qwen-Image-2512 文生图和 Qwen-Image-Edit-2511 图像编辑模型的全功能 API 服务与 Web 界面。

![Qwen Image Service](./frontend/public/favicon.svg)

## ✨ 核心特性

- 🎨 **文生图** - 根据文字描述生成高质量图像 (支持 4K 分辨率)。
- ✏️ **图像编辑** - 基于上传图像进行智能编辑。
- 📦 **批量编辑** - 对同一张图像应用多个编辑效果。
- 🔄 **异步任务队列 (Process Isolation)** - 采用进程隔离模式执行推理任务，彻底解决显存泄漏问题，支持多卡负载均衡。
- ⚡ **高性能推理** - 自动启用 VAE Tiling 和 Slicing 优化，NVIDIA A40 单卡即可生成 4K 图像无 OOM。
- 🔐 **安全认证** - 完善的用户系统：
    - JWT Token 认证
    - 邮箱验证与注册 (支持 SMTP)
    - 找回密码流程
    - 接口频率限制 (Rate Limiting) 防止攻击
- 📊 **历史与统计** - 完整的任务历史记录、个人/全局统计分析。
- 💰 **配额管理** - 支持每日/每月生成次数限制。
- 🖥️ **现代化 UI** - 极简风格的 React + Tailwind 前端，支持暗色模式、动态背景、Toast 通知。
- 🐳 **Docker 一键部署** - 开箱即用，支持 NVIDIA GPU。

## 📥 模型下载

使用前请先下载模型文件到 `./models` 目录：

| 模型 | 功能 | 下载地址 |
|------|------|----------|
| **Qwen-Image-2512** | 文生图 | [hf-mirror.com/Qwen/Qwen-Image-2512](https://hf-mirror.com/Qwen/Qwen-Image-2512) |
| **Qwen-Image-Edit-2511** | 图像编辑 | [hf-mirror.com/Qwen/Qwen-Image-Edit-2511](https://hf-mirror.com/Qwen/Qwen-Image-Edit-2511) |

```bash
# 安装 huggingface-cli
pip install huggingface_hub

# 设置镜像源（国内加速）
export HF_ENDPOINT=https://hf-mirror.com

# 下载模型
huggingface-cli download Qwen/Qwen-Image-2512 --local-dir ./models/Qwen-Image-2512
huggingface-cli download Qwen/Qwen-Image-Edit-2511 --local-dir ./models/Qwen-Image-Edit-2511
```

> 💡 **提示**：两个模型合计约 30GB，请确保磁盘空间充足。

## 🚀 快速部署 (Docker)

### 1. 准备环境
确保已安装 [Docker](https://docs.docker.com/engine/install/) 和 [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)。

```bash
# 验证 GPU 支持
docker run --rm --gpus all nvidia/cuda:12.4-base nvidia-smi
```

### 2. 配置
编辑 `config/config.yaml` 文件（可选），主要修改邮件配置以便启用注册验证：

```yaml
email:
  enabled: true
  smtp_server: "smtp.qq.com"
  smtp_port: 587
  smtp_username: "your_qq@qq.com"
  smtp_password: "your_auth_code"
  from_email: "your_qq@qq.com"
```

### 3. 启动服务

```bash
# 构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f
```

**访问地址：**
- **Web 界面**：http://localhost:8000 (前端已集成)
- **API 文档**：http://localhost:8000/docs
- **健康检查**：http://localhost:8000/health

> **注意**：默认管理员账号为 `admin` / `admin123`。

## 🛠️ 配置说明 (`config/config.yaml`)

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `task_queue.execution_mode` | 任务执行模式，`process` 为进程隔离（推荐），`thread` 为线程池 | `process` |
| `task_queue.max_workers` | 并行任务数，设为 1 以避免显存 OOM | `1` |
| `security.rate_limit` | 接口频率限制配置 | 开启 |
| `email` | 邮件服务配置（SMTP） | 关闭 |
| `quota` | 用户配额限制 | 开启 |

## 📚 API 文档

### 认证接口

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/auth/register` | 用户注册 (需邮箱验证) |
| POST | `/auth/login` | 用户登录 (获取 Token) |
| POST | `/auth/forgot-password` | 发送重置密码邮件 |
| POST | `/auth/reset-password` | 重置密码 |
| GET | `/auth/verify-email` | 验证邮箱 Token |

### 生成接口

所有生成接口均支持异步模式（默认），推荐生产环境使用。

#### 1. 文生图
`POST /text-to-image`

**参数：**
- `prompt`: 提示词 (必填)
- `aspect_ratio`: 宽高比 (如 "16:9", "1:1")
- `num_inference_steps`: 推理步数 (默认 50)
- `async_mode`: `true` (返回任务ID) / `false` (等待结果)

#### 2. 图像编辑
`POST /image-edit`

**参数：**
- `images`: 上传图片文件
- `prompt`: 编辑指令

#### 3. 任务管理
- `GET /tasks/{task_id}`: 查询任务状态
- `GET /tasks/{task_id}/result`: 获取生成结果 (图片或 ZIP)
- `GET /tasks/history/me`: 获取我的任务历史

## 💡 常见问题 (FAQ)

**Q: 生成 4K 图片会爆显存吗？**
A: 不会。系统已默认开启 VAE Tiling 优化，即使是 48GB 显存的 A40 也能轻松生成 4K 图片，峰值显存占用已大幅降低。

**Q: 任务状态一直是 Pending？**
A: 请检查 `max_workers` 配置。如果设为 1，任务通过队列串行执行。前一个任务未完成时，后续任务会排队。

**Q: 注册后无法登录？**
A: 如果启用了邮件服务，注册后必须去邮箱点击验证链接。如果没有配置邮件服务 (`email.enabled: false`)，则注册后直接可用。

**Q: 如何重置管理员密码？**
A: 删除 `data/users.db` 文件并重启服务，系统会重新创建默认的 `admin` / `admin123` 账号。

## 📄 License

MIT License