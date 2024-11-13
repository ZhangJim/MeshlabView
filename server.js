const express = require('express');
const multer = require('multer');
const fs = require('fs-extra');
const path = require('path');

const app = express();
const port = 3000;

// 修改静态文件服务配置
app.use('/', express.static(path.join(__dirname, 'public')));
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// 配置文件上传
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, 'uploads/')
  },
  filename: function (req, file, cb) {
    cb(null, Date.now() + '-' + file.originalname)
  }
});

const upload = multer({ storage: storage });

// 保存场景数据的接口
app.post('/save-scene', (req, res) => {
  try {
    const sceneData = req.body;
    const filename = `scene-${Date.now()}.json`;
    const scenesDir = path.join(__dirname, 'scenes');
    
    // 确保目录存在
    fs.ensureDirSync(scenesDir);
    
    // 写入文件
    fs.writeFileSync(
      path.join(scenesDir, filename),
      JSON.stringify(sceneData, null, 2)
    );
    
    console.log('场景保存成功:', filename); // 添加日志
    res.json({ success: true, filename });
  } catch (error) {
    console.error('保存场景失败:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// 获取场景列表
app.get('/list-scenes', (req, res) => {
    const scenesDir = path.join(__dirname, 'scenes');
    fs.readdir(scenesDir, (err, files) => {
        if (err) {
            console.error('读取场景目录失败:', err);
            return res.status(500).json({ error: '读取场景列表失败' });
        }
        
        const scenes = files
            .filter(file => file.endsWith('.json'))
            .map(filename => ({
                filename,
                path: path.join(scenesDir, filename)
            }));
            
        res.json(scenes);
    });
});

// 删除场景
app.delete('/delete-scene/:filename', (req, res) => {
    const filename = req.params.filename;
    const filepath = path.join(__dirname, 'scenes', filename);
    
    fs.unlink(filepath, (err) => {
        if (err) {
            console.error('删除场景失败:', err);
            return res.status(500).json({ error: '删除场景失败' });
        }
        res.json({ success: true });
    });
});

// 获取特定场景数据
app.get('/scene/:filename', (req, res) => {
    const filename = req.params.filename;
    const filepath = path.join(__dirname, 'scenes', filename);
    
    fs.readFile(filepath, 'utf8', (err, data) => {
        if (err) {
            console.error('读场景数据失败:', err);
            return res.status(500).json({ error: '读取场景数据失败' });
        }
        res.json(JSON.parse(data));
    });
});

// 添加模型文件处理接口
app.get('/model/:filename', (req, res) => {
    const filename = req.params.filename;
    const filepath = path.join(__dirname, 'uploads', filename);
    
    if (fs.existsSync(filepath)) {
        res.sendFile(filepath);
    } else {
        res.status(404).json({ error: '文件不存在' });
    }
});

// 确保必要的目录存在
fs.ensureDirSync(path.join(__dirname, 'uploads'));
fs.ensureDirSync(path.join(__dirname, 'scenes'));

app.listen(port, () => {
  console.log(`服务器运行在端口 ${port}`);
}); 