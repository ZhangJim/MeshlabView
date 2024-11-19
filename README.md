# 项目名称

## 简介
这是一个用于查看和管理 3D 模型的 Web 应用程序。用户可以上传、查看、保存和重命名 3D 模型场景。
技术栈
后端: Flask (Python)
前端: HTML, CSS, JavaScript
其他: Three.js 用于 3D 模型渲染
### 文件结构

项目根目录/
│
├── app.py                  # Flask 后端应用
├── server.js               # 可能用于其他服务
├── public/
│   ├── index.html          # 前端 HTML 文件
│   └── ...                 # 其他前端资源
├── scenes/                 # 场景数据存储目录
│   └── ...                 # 场景 JSON 文件
└── uploads/                # 上传的模型文件存储目录

### 安装与运行

#### 前提条件
Python 3.x
Node.js (如果使用 server.js)
安装步骤
1. 克隆项目到本地：
   git clone <项目仓库地址>
   cd 项目目录

2. 创建虚拟环境：python -m venv venv

3. 激活虚拟环境：.\venv\Scripts\activate

4. 安装 Python 依赖：
   pip install -r requirements.txt

5. 运行 Flask 应用：
   python app.py

6. 在浏览器中打开 http://localhost:3000 查看应用。

## 功能
上传模型: 支持 .obj, .mtl, .jpg 文件
查看模型: 使用 Three.js 渲染 3D 模型
保存场景: 保存当前模型场景
重命名场景: 双击场景名称进行重命名
删除场景: 删除不需要的场景
使用说明
添加模型: 点击“添加新模型”按钮上传模型文件
调整位置: 通过模型列表中的 X/Y/Z 坐标调整模型位置
场景管理:
保存场景: 点击“保存场景”按钮
加载场景: 点击场景列表中的“加载”按钮
重命名: 双击场景名称可以重命名
删除场景: 点击场景列表中的“删除”按钮
分享场景: 点击场景列表中的“分享”按钮
下载场景: 点击场景列表中的“下载”按钮
视图控制:
亮度调节: 使用亮度滑块调整场景亮度
白模显示: 切换开关显示白模效果

## 贡献
欢迎提交问题和请求合并。请确保在提交前运行所有测试。

## 许可证
此项目使用 MIT 许可证。