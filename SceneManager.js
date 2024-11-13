class SceneManager {
    constructor() {
        this.baseUrl = '/saved_scenes/'; // 存储基础路径
    }

    async saveCurrentScene(models, cameraPosition, controlsTarget) {
        const sceneId = this.generateSceneId();
        const scenePath = `${this.baseUrl}scene_${sceneId}`;
        
        // 创建场景目录结构
        await this.createDirectory(scenePath);
        await this.createDirectory(`${scenePath}/models`);

        // 保存模型文件
        const modelPaths = await Promise.all(models.map(async (model, index) => {
            const files = {
                obj: model.objFile,
                mtl: model.mtlFile,
                texture: model.textureFile
            };
            
            const paths = {};
            for (const [type, file] of Object.entries(files)) {
                if (file) {
                    const fileName = `model${index}_${file.name}`;
                    const filePath = `${scenePath}/models/${fileName}`;
                    await this.saveFile(file, filePath);
                    paths[type] = fileName;
                }
            }
            
            return {
                ...paths,
                position: model.object.position.toArray(),
                rotation: model.object.rotation.toArray(),
                scale: model.object.scale.toArray()
            };
        }));

        // 保存场景配置
        const sceneConfig = {
            models: modelPaths,
            camera: {
                position: cameraPosition.toArray(),
                target: controlsTarget.toArray()
            },
            timestamp: Date.now()
        };

        await this.saveJSON(sceneConfig, `${scenePath}/scene.json`);
        
        // 生成预览页面
        await this.generatePreviewPage(sceneId, sceneConfig);

        return sceneId;
    }

    async generatePreviewPage(sceneId, sceneConfig) {
        const html = `
<!DOCTYPE html>
<html>
<head>
    <title>Scene ${sceneId}</title>
    <script src="scene.json"></script>
    <script>
        // 加载场景配置
        const sceneConfig = ${JSON.stringify(sceneConfig)};
        
        // 初始化场景
        window.onload = function() {
            // ... 初始化 Three.js 场景 ...
            // ... 加载模型和材质 ...
        }
    </script>
</head>
<body>
    <!-- 预览页面内容 -->
</body>
</html>`;

        await this.saveFile(
            new Blob([html], { type: 'text/html' }),
            `${this.baseUrl}scene_${sceneId}/index.html`
        );
    }

    // 辅助方法：创建目录
    async createDirectory(path) {
        // 实现目录创建逻辑
    }

    // 辅助方法：保存文件
    async saveFile(file, path) {
        // 实现文件保存逻辑
    }

    // 辅助方法：保存 JSON
    async saveJSON(data, path) {
        await this.saveFile(
            new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }),
            path
        );
    }

    // 生成唯一场景ID
    generateSceneId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
} 