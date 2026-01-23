# Qwen Image Service - API 文档

> 版本: 1.0.0  
> 基础URL: `http://<host>:8000`

---

## 目录

- [概述](#概述)
- [认证](#认证)
- [通用说明](#通用说明)
- [API端点](#api端点)
  - [文生图](#1-文生图)
  - [图像编辑](#2-图像编辑)
  - [批量编辑](#3-批量编辑)
  - [健康检查](#4-健康检查)
  - [模型信息](#5-模型信息)
  - [宽高比查询](#6-宽高比查询)
- [错误处理](#错误处理)
- [示例代码](#示例代码)

---

## 概述

Qwen Image Service 提供以下功能：

| 功能 | 端点 | 描述 |
|------|------|------|
| 文生图 | `POST /text-to-image` | 根据文本描述生成图像 |
| 图像编辑 | `POST /image-edit` | 基于上传图像进行编辑 |
| 批量编辑 | `POST /image-edit/batch` | 对同一图像应用多个编辑 |

---

## 认证

当前版本不需要认证。如需添加认证，请在请求头中添加：

```
Authorization: Bearer <token>
```

---

## 通用说明

### 请求格式

- **Content-Type**: `multipart/form-data`（包含文件上传的端点）
- **Content-Type**: `application/x-www-form-urlencoded`（纯表单数据）

### 响应格式

| 场景 | Content-Type | 描述 |
|------|--------------|------|
| 单张图像 | `image/png` | 直接返回PNG图像 |
| 多张图像 | `application/zip` | 返回ZIP压缩包 |
| JSON数据 | `application/json` | 系统信息等 |
| 错误 | `application/json` | 包含错误详情 |

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

---

## API端点

### 1. 文生图

根据文本描述生成图像。

```
POST /text-to-image
```

#### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `prompt` | string | ✅ | - | 生成图像的描述文本 |
| `negative_prompt` | string | ❌ | `""` | 不希望出现在图像中的内容 |
| `aspect_ratio` | string | ❌ | `"1:1"` | 图像宽高比，见[支持的宽高比](#支持的宽高比) |
| `num_inference_steps` | int | ❌ | `50` | 推理步数 (20-100)，越大质量越高但越慢 |
| `true_cfg_scale` | float | ❌ | `4.0` | CFG尺度 (1.0-10.0)，控制与提示的匹配程度 |
| `seed` | int | ❌ | `-1` | 随机种子，-1表示随机，固定值可复现结果 |
| `num_images` | int | ❌ | `1` | 生成图像数量 (1-4) |

#### 响应

- **成功 (单张)**: `200 OK` - 返回 `image/png`
- **成功 (多张)**: `200 OK` - 返回 `application/zip`
- **失败**: `500 Internal Server Error` - JSON错误信息

#### 示例

**请求**:
```bash
curl -X POST "http://localhost:8000/text-to-image" \
  -F "prompt=一只可爱的橘猫在阳光下打盹" \
  -F "negative_prompt=模糊,低质量" \
  -F "aspect_ratio=16:9" \
  -F "num_inference_steps=50" \
  -F "seed=42" \
  --output cat.png
```

**响应**:
```
HTTP/1.1 200 OK
Content-Type: image/png
Content-Disposition: attachment; filename="generated_a1b2c3d4.png"

<二进制图像数据>
```

---

### 2. 图像编辑

基于上传的图像进行编辑。

```
POST /image-edit
```

#### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `images` | file[] | ✅ | - | 上传的图像文件（1-2张） |
| `prompt` | string | ✅ | - | 编辑图像的描述文本 |
| `negative_prompt` | string | ❌ | `""` | 不希望出现在图像中的内容 |
| `num_inference_steps` | int | ❌ | `40` | 推理步数 (20-100) |
| `true_cfg_scale` | float | ❌ | `4.0` | CFG尺度 (1.0-10.0) |
| `guidance_scale` | float | ❌ | `1.0` | 指导尺度 (1.0-10.0) |
| `seed` | int | ❌ | `-1` | 随机种子 |
| `num_images` | int | ❌ | `1` | 生成图像数量 (1-4) |

#### 文件限制

- **最大文件大小**: 20MB
- **支持的格式**: `image/jpeg`, `image/png`, `image/webp`
- **最大文件数量**: 2

#### 响应

- **成功 (单张)**: `200 OK` - 返回 `image/png`
- **成功 (多张)**: `200 OK` - 返回 `application/zip`
- **失败**: `400 Bad Request` / `500 Internal Server Error`

#### 示例

**请求**:
```bash
curl -X POST "http://localhost:8000/image-edit" \
  -F "images=@original.jpg" \
  -F "prompt=把背景换成海滩" \
  -F "num_inference_steps=40" \
  --output edited.png
```

**多图合成请求**:
```bash
curl -X POST "http://localhost:8000/image-edit" \
  -F "images=@person.jpg" \
  -F "images=@background.jpg" \
  -F "prompt=把人物放到这个背景中" \
  --output composite.png
```

---

### 3. 批量编辑

对同一张图像应用多个编辑提示，返回所有结果的ZIP包。

```
POST /image-edit/batch
```

#### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `image` | file | ✅ | - | 上传的单张图像文件 |
| `prompts` | string | ✅ | - | 多个编辑提示，用 `\|` 分隔 |
| `negative_prompt` | string | ❌ | `""` | 不希望出现在图像中的内容 |
| `num_inference_steps` | int | ❌ | `40` | 推理步数 (20-100) |
| `true_cfg_scale` | float | ❌ | `4.0` | CFG尺度 (1.0-10.0) |
| `seed` | int | ❌ | `-1` | 随机种子 |

#### 限制

- **最大提示数量**: 10

#### 响应

- **成功**: `200 OK` - 返回 `application/zip`，包含所有编辑结果
- **失败**: `400 Bad Request` / `500 Internal Server Error`

#### 示例

**请求**:
```bash
curl -X POST "http://localhost:8000/image-edit/batch" \
  -F "image=@portrait.jpg" \
  -F "prompts=添加太阳镜|改变发色为金色|添加帽子" \
  -F "num_inference_steps=40" \
  --output batch_results.zip
```

**响应**:
```
HTTP/1.1 200 OK
Content-Type: application/zip
Content-Disposition: attachment; filename="batch_edit_a1b2c3d4.zip"

<ZIP文件，包含 batch_0_*.png, batch_1_*.png, batch_2_*.png>
```

---

### 4. 健康检查

检查服务状态和模型加载情况。

```
GET /health
```

#### 响应

```json
{
  "status": "healthy",
  "text_to_image_model_loaded": true,
  "image_edit_model_loaded": true,
  "gpu_available": true,
  "gpu_count": 1
}
```

#### 响应字段

| 字段 | 类型 | 描述 |
|------|------|------|
| `status` | string | 服务状态，`healthy` 表示正常 |
| `text_to_image_model_loaded` | bool | 文生图模型是否已加载 |
| `image_edit_model_loaded` | bool | 图像编辑模型是否已加载 |
| `gpu_available` | bool | GPU是否可用 |
| `gpu_count` | int | 可用GPU数量 |

---

### 5. 模型信息

获取可用模型的详细信息。

```
GET /models
```

#### 响应

```json
{
  "text_to_image": {
    "name": "Qwen/Qwen-Image-2512",
    "description": "Qwen-Image-2512 文生图模型",
    "capabilities": ["text-to-image", "image generation"],
    "status": "loaded"
  },
  "image_edit": {
    "name": "Qwen/Qwen-Image-Edit-2511",
    "description": "Qwen-Image-Edit-2511 图像编辑模型",
    "capabilities": ["image-to-image", "image editing", "multi-image composition"],
    "status": "loaded"
  }
}
```

---

### 6. 宽高比查询

获取支持的图像宽高比及其对应尺寸。

```
GET /aspect-ratios
```

#### 响应

```json
{
  "1:1": [1024, 1024],
  "16:9": [1664, 928],
  "9:16": [928, 1664],
  "4:3": [1472, 1104],
  "3:4": [1104, 1472],
  "3:2": [1584, 1056],
  "2:3": [1056, 1584]
}
```

---

## 错误处理

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

### HTTP状态码

| 状态码 | 描述 |
|--------|------|
| `200` | 成功 |
| `400` | 请求参数错误 |
| `500` | 服务器内部错误 |
| `503` | 模型未加载 |

### 常见错误

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| `文生图模型未加载` | 模型未成功加载 | 检查 `/health` 端点，等待模型加载完成 |
| `不支持的文件类型` | 上传了不支持的图片格式 | 使用 JPEG、PNG 或 WebP 格式 |
| `文件大小超过限制` | 文件超过20MB | 压缩图像后重试 |
| `最多上传2张图像` | 图像编辑上传了超过2张图 | 减少上传图像数量 |

---

## 示例代码

### Python

```python
import requests

# 文生图
def text_to_image(prompt, output_path="output.png"):
    response = requests.post(
        "http://localhost:8000/text-to-image",
        data={
            "prompt": prompt,
            "aspect_ratio": "16:9",
            "num_inference_steps": 50,
        }
    )
    
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"图像已保存到 {output_path}")
    else:
        print(f"错误: {response.json()}")

# 图像编辑
def edit_image(image_path, prompt, output_path="edited.png"):
    with open(image_path, "rb") as f:
        response = requests.post(
            "http://localhost:8000/image-edit",
            files={"images": f},
            data={"prompt": prompt}
        )
    
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"编辑后的图像已保存到 {output_path}")
    else:
        print(f"错误: {response.json()}")

# 健康检查
def health_check():
    response = requests.get("http://localhost:8000/health")
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 检查服务状态
    status = health_check()
    print(f"服务状态: {status}")
    
    # 生成图像
    text_to_image("一只可爱的橘猫在阳光下打盹", "cat.png")
    
    # 编辑图像
    edit_image("cat.png", "给猫戴上一顶帽子", "cat_with_hat.png")
```

### JavaScript (Node.js)

```javascript
const fs = require('fs');
const FormData = require('form-data');
const axios = require('axios');

const BASE_URL = 'http://localhost:8000';

// 文生图
async function textToImage(prompt, outputPath = 'output.png') {
  const formData = new FormData();
  formData.append('prompt', prompt);
  formData.append('aspect_ratio', '16:9');
  formData.append('num_inference_steps', '50');

  const response = await axios.post(`${BASE_URL}/text-to-image`, formData, {
    headers: formData.getHeaders(),
    responseType: 'arraybuffer'
  });

  fs.writeFileSync(outputPath, response.data);
  console.log(`图像已保存到 ${outputPath}`);
}

// 图像编辑
async function editImage(imagePath, prompt, outputPath = 'edited.png') {
  const formData = new FormData();
  formData.append('images', fs.createReadStream(imagePath));
  formData.append('prompt', prompt);

  const response = await axios.post(`${BASE_URL}/image-edit`, formData, {
    headers: formData.getHeaders(),
    responseType: 'arraybuffer'
  });

  fs.writeFileSync(outputPath, response.data);
  console.log(`编辑后的图像已保存到 ${outputPath}`);
}

// 健康检查
async function healthCheck() {
  const response = await axios.get(`${BASE_URL}/health`);
  return response.data;
}

// 使用示例
(async () => {
  const status = await healthCheck();
  console.log('服务状态:', status);
  
  await textToImage('一只可爱的橘猫在阳光下打盹', 'cat.png');
})();
```

### cURL

```bash
# 健康检查
curl http://localhost:8000/health

# 文生图
curl -X POST http://localhost:8000/text-to-image \
  -F "prompt=一只可爱的橘猫" \
  -F "aspect_ratio=1:1" \
  --output cat.png

# 图像编辑
curl -X POST http://localhost:8000/image-edit \
  -F "images=@input.jpg" \
  -F "prompt=把背景换成海滩" \
  --output edited.png

# 批量编辑
curl -X POST http://localhost:8000/image-edit/batch \
  -F "image=@portrait.jpg" \
  -F "prompts=添加太阳镜|改变发色|添加帽子" \
  --output batch.zip
```

---

## 更新日志

### v1.0.0

- 初始版本
- 支持文生图、图像编辑、批量编辑
- 支持多种宽高比
- GPU加速支持
