let scene, camera, renderer, controls, transformControls;
let selectedModel = null; // 当前选中的模型
let models = []; // 存储所有模型

// 初始化场景管理器
const sceneManager = new SceneManager();
const sceneLoader = new SceneLoader(renderer, camera, controls);

// 在文件开头添加
const sceneManager = new SceneManager();

// 修改保存场景事件处理
document.getElementById('save-scene').addEventListener('click', function() {
    if (models.length === 0) {
        alert('请先加载模型！');
        return;
    }

    const sceneId = sceneManager.saveCurrentScene(models, camera.position, controls.target);
    const shareUrl = `${window.location.origin}${window.location.pathname}?scene=${sceneId}`;
    
    // 更新场景列表
    updateSceneList();
    
    // 显示保存成功和分享链接
    alert(`场景已保存！\n分享链接：${shareUrl}`);
});

// 添加更新场景列表的函数
function updateSceneList() {
    const sceneList = document.getElementById('scene-list');
    if (!sceneList) return;

    sceneList.innerHTML = '';
    const scenes = sceneManager.getAllScenes();
    
    scenes.forEach(scene => {
        const sceneElement = document.createElement('div');
        sceneElement.className = 'saved-scene';
        const date = new Date(scene.timestamp).toLocaleString();
        
        sceneElement.innerHTML = `
            <div>保存时间: ${date}</div>
            <div>模型数量: ${scene.modelCount}</div>
            <a href="?scene=${scene.id}" target="_blank">打开场景</a>
        `;
        
        sceneList.appendChild(sceneElement);
    });
}

// 在页面加载时初始化场景列表
window.addEventListener('load', function() {
    updateSceneList();
    
    // 检查 URL 参数是否包含场景 ID
    const urlParams = new URLSearchParams(window.location.search);
    const sceneId = urlParams.get('scene');
    if (sceneId) {
        const sceneData = sceneManager.loadScene(sceneId);
        if (sceneData) {
            // TODO: 加载场景数据
            console.log('加载场景:', sceneData);
        }
    }
});

function init() {
    try {
        console.log('开始初始化场景');
        scene = new THREE.Scene();
        scene.background = new THREE.Color(0xf0f0f0);

        camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(0, 2, 5);
        console.log('相机位置:', camera.position);

        renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        document.body.appendChild(renderer.domElement);

        controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;

        const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
        scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
        directionalLight.position.set(1, 1, 1);
        scene.add(directionalLight);

        const gridHelper = new THREE.GridHelper(10, 10, 0x444444, 0x888888);
        scene.add(gridHelper);

        const axesHelper = new THREE.AxesHelper(5);
        scene.add(axesHelper);

        // 初始化变换控制器
        transformControls = new THREE.TransformControls(camera, renderer.domElement);
        transformControls.setMode('translate'); // 设置为移动模式
        scene.add(transformControls);

        // 当拖拽时禁用轨道控制器
        transformControls.addEventListener('dragging-changed', function(event) {
            controls.enabled = !event.value;
        });

        // 添加点击选择功能
        renderer.domElement.addEventListener('pointerdown', function(event) {
            if (event.button !== 0) return; // 只响应左键点击

            const raycaster = new THREE.Raycaster();
            const mouse = new THREE.Vector2();

            // 计算鼠标位置
            mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
            mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

            raycaster.setFromCamera(mouse, camera);
            const intersects = raycaster.intersectObjects(scene.children, true);

            if (intersects.length > 0) {
                // 找到最顶层的模型
                let modelRoot = intersects[0].object;
                while (modelRoot.parent && modelRoot.parent !== scene) {
                    modelRoot = modelRoot.parent;
                }
                transformControls.attach(modelRoot);
            } else {
                // 点击空白处取消选择
                transformControls.detach();
            }
        });

        // 添加键盘快捷键
        window.addEventListener('keydown', function(event) {
            if (!selectedModel) return;

            switch(event.key.toLowerCase()) {
                case 'g': // 移动模式
                    transformControls.setMode('translate');
                    break;
                case 'r': // 旋转模式
                    transformControls.setMode('rotate');
                    break;
                case 's': // 缩放模式
                    transformControls.setMode('scale');
                    break;
                case 'escape': // 取消选择
                    transformControls.detach();
                    selectedModel = null;
                    break;
            }
        });

        console.log('场景初始化完成');
        animate();
    } catch (error) {
        console.error('初始化错误:', error);
    }
}

function animate() {
    requestAnimationFrame(animate);
    if (controls) controls.update();
    if (renderer && scene && camera) {
        renderer.render(scene, camera);
    }
}

function loadOBJFile(objFile, mtlFile, textureFiles) {
    console.log('开始加载文件:', objFile.name);
    const mtlLoader = new THREE.MTLLoader();
    const objLoader = new THREE.OBJLoader();
    
    // 清除之前的模型
    scene.children = scene.children.filter(child => {
        return child.isLight || child.isHelper;
    });

    function loadOBJ(file) {
        const reader = new FileReader();
        reader.onload = function(event) {
            console.log('OBJ文件读取完成');
            const object = objLoader.parse(event.target.result);
            
            // 调整模型位置和大小
            const box = new THREE.Box3().setFromObject(object);
            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3());
            const maxDim = Math.max(size.x, size.y, size.z);
            const scale = 2 / maxDim;
            
            object.scale.multiplyScalar(scale);
            object.position.copy(center).multiplyScalar(-1 * scale);
            
            // 确保所有材质都是双面的
            object.traverse(function(child) {
                if (child.isMesh) {
                    child.material.side = THREE.DoubleSide;
                    child.material.needsUpdate = true;
                }
            });

            // 设置模型位置（根据已有模型数量计算偏移）
            const offset = models.length * 3; // 每个模型间隔3个单位
            object.position.x = offset;
            
            // 添加到场景和模型列表
            scene.add(object);
            models.push(object);
            
            // 自动选中新添加的模型
            selectedModel = object;
            transformControls.attach(object);
            console.log('模型已添加到场景');
            
            // 调整相机位置以适应模型
            camera.position.set(0, maxDim * 0.5, maxDim);
            camera.lookAt(0, 0, 0);
            controls.update();
        };
        reader.onerror = function(error) {
            console.error('读取OBJ文件错误:', error);
        };
        reader.readAsText(file);
    }

    if (mtlFile) {
        const reader = new FileReader();
        reader.onload = function(event) {
            console.log('MTL文件读取完成');
            const mtlContent = event.target.result;
            const mtlBlob = new Blob([mtlContent], { type: 'text/plain' });
            const mtlURL = URL.createObjectURL(mtlBlob);
            
            mtlLoader.load(mtlURL, function(materials) {
                console.log('材质加载成功');
                materials.preload();
                
                // 处理纹理
                if (textureFiles.length > 0) {
                    const textureLoader = new THREE.TextureLoader();
                    Object.values(materials.materials).forEach(material => {
                        if (material.map) {
                            const textureFile = textureFiles.find(f => f.name === material.map.name);
                            if (textureFile) {
                                const textureURL = URL.createObjectURL(textureFile);
                                material.map = textureLoader.load(textureURL);
                                material.needsUpdate = true;
                            }
                        }
                    });
                }
                
                objLoader.setMaterials(materials);
                loadOBJ(objFile);
                URL.revokeObjectURL(mtlURL);
            });
        };
        reader.onerror = function(error) {
            console.error('读取MTL文件错误:', error);
            loadOBJ(objFile);
        };
        reader.readAsText(mtlFile);
    } else {
        loadOBJ(objFile);
    }
}

// 文件输入监听器
document.getElementById('file-input').addEventListener('change', function(event) {
    const files = Array.from(event.target.files);
    console.log('选择文件:', files.map(f => f.name));
    
    const objFile = files.find(f => f.name.toLowerCase().endsWith('.obj'));
    const mtlFile = files.find(f => f.name.toLowerCase().endsWith('.mtl'));
    const textureFiles = files.filter(f => /\.(jpg|jpeg|png|gif)$/i.test(f.name));
    
    if (objFile) {
        loadOBJFile(objFile, mtlFile, textureFiles);
    }
});

// 检查URL参数是否包含场景ID
async function checkSceneParam() {
    const urlParams = new URLSearchParams(window.location.search);
    const sceneId = urlParams.get('scene');
    if (sceneId) {
        const sceneData = await sceneManager.loadScene(sceneId);
        if (sceneData) {
            const loadedModels = await sceneLoader.loadModels(sceneData.models);
            sceneLoader.setCamera(sceneData.camera.position, sceneData.camera.target);
            // 更新场景
            models = loadedModels;
            updateModelList();
        }
    }
}

// 初始化时检查场景参数
checkSceneParam();

// 初始化场景
init();

// 窗口大小改变监听器
window.addEventListener('resize', function() {
    if (camera && renderer) {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    }
});

// 保存场景
async function saveScene() {
    if (models.length === 0) {
        alert('请先加载模型！');
        return;
    }

    // 收集当前场景的所有文件和数据
    const sceneId = await sceneManager.saveCurrentScene(
        models.map(model => ({
            ...model,
            file: model.originalFile, // 需要在加载模型时保存原始文件
            fileName: model.fileName
        })),
        camera.position,
        controls.target
    );

    const shareUrl = `${window.location.origin}${window.location.pathname}?scene=${sceneId}`;
    alert(`场景已保存！\n分享链接：${shareUrl}`);
}

// 加载场景
async function loadScene(sceneId) {
    const sceneData = await sceneManager.loadScene(sceneId);
    if (!sceneData) return;

    // 清除当前场景
    clearScene();

    // 加载所有模型
    for (const modelConfig of sceneData.sceneConfig.models) {
        const fileData = sceneData.modelFiles.get(modelConfig.fileName);
        const file = dataURLtoFile(fileData, modelConfig.fileName);
        
        // 加载模型
        await loadOBJFile(file, modelConfig.position);
    }

    // 恢复相机位置
    camera.position.fromArray(sceneData.sceneConfig.camera.position);
    controls.target.fromArray(sceneData.sceneConfig.camera.target);
    controls.update();
} 