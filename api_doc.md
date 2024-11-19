# 3D模型对比工具 API 文档

## 基础信息
- 基础URL: `http://192.168.123.162:3000`
- 所有请求和响应均使用 JSON 格式
- 支持跨域请求 (CORS)

## API 接口列表

### 1. 上传文件
- **接口**: `/upload`
- **方法**: `POST`
- **Content-Type**: `multipart/form-data`
- **说明**: 用于上传模型文件（支持 .obj、.mtl、.jpg/.jpeg/.png 文件）
- **请求参数**:
  ```
  file: 文件对象
  ```
- **响应示例**:
  ```json
  {
    "success": true,
    "filename": "model.obj",
    "filepath": "/uploads/24-11-18_14-30-45/model.obj"
  }
  ```

### 2. 保存场景
- **接口**: `/save-scene`
- **方法**: `POST`
- **Content-Type**: `application/json`
- **请求体示例**:
  ```json
  {
    "models": [
      {
        "objFile": "/uploads/timestamp/model.obj",
        "mtlFile": "/uploads/timestamp/model.mtl",
        "textureFile": "/uploads/timestamp/texture.jpg",
        "position": { "x": 0, "y": 0, "z": 0 },
        "rotation": { "x": 0, "y": 0, "z": 0 },
        "scale": { "x": 1, "y": 1, "z": 1 }
      }
    ],
    "camera": {
      "position": { "x": 0, "y": 2, "z": 5 },
      "rotation": { "x": 0, "y": 0, "z": 0 }
    },
    "settings": {
      "wireframe": false,
      "brightness": 100
    }
  }
  ```
- **响应示例**:
  ```json
  {
    "success": true,
    "filename": "scene-24-11-18_14-30-45.json"
  }
  ```

### 3. 获取场景列表
- **接口**: `/list-scenes`
- **方法**: `GET`
- **响应示例**:
  ```json
  [
    {
      "filename": "scene-24-11-18_14-30-45.json"
    }
  ]
  ```

### 4. 获取场景数据
- **接口**: `/scenes/{filename}`
- **方法**: `GET`
- **参数**: filename - 场景文件名
- **响应**: 返回完整的场景数据

### 5. 删除场景
- **接口**: `/scenes/{filename}`
- **方法**: `DELETE`
- **参数**: filename - 场景文件名
- **响应示例**:
  ```json
  {
    "success": true
  }
  ```

### 6. 重命名场景
- **接口**: `/scenes/{old_filename}/rename`
- **方法**: `POST`
- **Content-Type**: `application/json`
- **请求体示例**:
  ```json
  {
    "newName": "新场景名称"
  }
  ```
- **响应示例**:
  ```json
  {
    "success": true,
    "newFilename": "新场景名称.json"
  }
  ```

### 7. 下载场景
- **接口**: `/scenes/{filename}/download`
- **方法**: `GET`
- **参数**: filename - 场景文件名
- **响应**: 返回 ZIP 文件，包含场景的所有相关文件

### 8. 分享场景
- **接口**: `/share/{filename}`
- **方法**: `GET`
- **参数**: filename - 场景文件名
- **响应**: 返回可直接访问的分享页面 HTML


## 注意事项
1. 上传文件时只能上传 .obj、.mtl、.jpg 文件
2. 所有文件名中的中文字符需要进行 URL 编码
3. 下载场景时会自动打包所有相关文件
4. 分享链接可以直接在浏览器中打开查看
5. 场景数据中，`position`、`rotation`、`scale` 字段的值均为对象，其中的 `x`、`y`、`z` 字段分别表示位置、旋转角度和缩放比例
6. 场景数据中，`wireframe` 字段表示是否显示线框，`brightness` 字段表示模型亮度

## 错误处理
所有接口在发生错误时会返回相应的错误信息：