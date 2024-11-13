class SceneData {
    constructor() {
        this.modelFiles = new Map(); // 存储模型文件的 base64 数据
        this.sceneConfig = {
            models: [], // 存储模型的位置、旋转等信息
            camera: {
                position: null,
                target: null
            },
            timestamp: null
        };
    }

    // 添加模型文件
    addModelFile(fileName, fileData) {
        this.modelFiles.set(fileName, fileData);
    }

    // 设置场景配置
    setSceneConfig(models, camera) {
        this.sceneConfig.models = models.map(model => ({
            fileName: model.fileName,
            position: model.object.position.toArray(),
            rotation: model.object.rotation.toArray(),
            scale: model.object.scale.toArray()
        }));
        
        this.sceneConfig.camera = {
            position: camera.position.toArray(),
            target: camera.target.toArray()
        };
        
        this.sceneConfig.timestamp = Date.now();
    }

    // 序列化场景数据
    serialize() {
        return {
            modelFiles: Object.fromEntries(this.modelFiles),
            sceneConfig: this.sceneConfig
        };
    }

    // 从序列化数据恢复
    static deserialize(data) {
        const sceneData = new SceneData();
        sceneData.modelFiles = new Map(Object.entries(data.modelFiles));
        sceneData.sceneConfig = data.sceneConfig;
        return sceneData;
    }
} 