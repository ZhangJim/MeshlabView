from flask import Flask, request, jsonify, send_from_directory, send_file, session
import os
import json
import shutil
from werkzeug.utils import secure_filename
import time
from flask_cors import CORS
from urllib.parse import unquote
import zipfile
import io

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
CORS(app)

# 配置文件保存路径
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
SCENES_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scenes')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SCENES_FOLDER'] = SCENES_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# 确保必要的文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SCENES_FOLDER, exist_ok=True)

# 允许的文件类型
ALLOWED_EXTENSIONS = {'obj', 'mtl', 'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 主页路由
@app.route('/')
def index():
    return send_file('public/index.html')

@app.route('/save-scene', methods=['POST'])
def save_scene():
    try:
        if not request.is_json:
            return jsonify({'error': '无效的请求格式'}), 400
            
        scene_data = request.get_json()
        
        # 生成格式化的场景文件名: YY-MM-DD_HH-mm-ss
        timestamp = time.strftime("%y-%m-%d_%H-%M-%S", time.localtime())
        filename = f'scene-{timestamp}.json'
        
        # 保存场景数据
        filepath = os.path.join(app.config['SCENES_FOLDER'], filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(scene_data, f, ensure_ascii=False)
        
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        print(f"保存场景错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/scenes/<filename>', methods=['GET'])
def get_scene(filename):
    try:
        filepath = os.path.join(app.config['SCENES_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '场景不存在'}), 404
            
        with open(filepath, 'r', encoding='utf-8') as f:
            scene_data = json.load(f)
        return jsonify(scene_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/scenes/<path:filename>', methods=['DELETE'])
def delete_scene(filename):
    try:
        # URL解码文件名，处理中文和特殊字符
        decoded_filename = unquote(filename)
        
        filepath = os.path.join(app.config['SCENES_FOLDER'], decoded_filename)
        print(f"尝试删除文件: {filepath}")  # 调试日志
        
        # 即使文件不存在也返回成功
        if not os.path.exists(filepath):
            print(f"文件不存在: {filepath}")  # 调试日志
            return jsonify({'success': True})  # 修改这里，总是返回成功
            
        try:
            # 删除场景文件
            os.remove(filepath)
            print(f"成功删除文件: {filepath}")  # 调试日志
            return jsonify({'success': True})
        except Exception as e:
            print(f"删除文件失败: {filepath}, 错误: {str(e)}")  # 调试日志
            return jsonify({'success': True})  # 即使删除失败也返回成功
            
    except Exception as e:
        print(f"删除场景错误: {str(e)}")  # 调试日志
        return jsonify({'success': True})  # 所有情况都返回成功

@app.route('/list-scenes', methods=['GET'])
def list_scenes():
    try:
        scenes = []
        for filename in sorted(os.listdir(app.config['SCENES_FOLDER']), reverse=True):
            if filename.endswith('.json'):
                scenes.append({'filename': filename})
        return jsonify(scenes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        print("接收到上传请求")
        print("请求文件:", request.files)
        
        if 'file' not in request.files:
            print("没有文件在请求中")
            return jsonify({'error': '没有文件'}), 400
            
        file = request.files['file']
        print(f"文件名: {file.filename}")
        
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
            
        if file and allowed_file(file.filename):
            # 清除旧的session时间戳
            session.pop('current_upload_timestamp', None)
            
            # 获取或创建新的时间戳文件夹名
            timestamp = session.get('current_upload_timestamp')
            if not timestamp:
                current_time = time.localtime()
                # 使用原来的格式 YY-MM-DD_HH-MM-SS
                timestamp = time.strftime("%y-%m-%d_%H-%M-%S", current_time)
                session['current_upload_timestamp'] = timestamp
            
            folder_path = os.path.join(app.config['UPLOAD_FOLDER'], timestamp)
            os.makedirs(folder_path, exist_ok=True)
            
            filename = secure_filename(file.filename)
            filepath = os.path.join(folder_path, filename)
            print(f"保存路径: {filepath}")
            
            file.save(filepath)
            print(f"文件保存成功: {filepath}")
            
            # 如果是jpg文件，说明是最后一个文件，清除session中的时间戳
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                session.pop('current_upload_timestamp', None)
            
            return jsonify({
                'success': True, 
                'filename': filename,
                'filepath': f'/uploads/{timestamp}/{filename}'
            })
        
        return jsonify({'error': '不支持的文件类型'}), 400
    except Exception as e:
        print(f"上传处理错误: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<path:filepath>')
def uploaded_file(filepath):
    try:
        # 从路径中分离文件夹和文件
        folder = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], folder), filename)
    except Exception as e:
        print(f"文件访问错误: {str(e)}")
        return jsonify({'error': str(e)}), 404

# 添加CORS支持
@app.after_request
def after_request(response):
    response.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Allow-Credentials': 'true',
    })
    return response

# 添加静态文件路由
@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('public', filename)

# 修改重命名接口
@app.route('/scenes/<path:old_filename>/rename', methods=['POST'])
def rename_scene(old_filename):
    try:
        if not request.is_json:
            return jsonify({'error': '无效的请求格式'}), 400
            
        new_name = request.json.get('newName')
        if not new_name:
            return jsonify({'error': '新文件名不能为空'}), 400
            
        # 确保新文件名以 .json 结尾
        if not new_name.endswith('.json'):
            new_name += '.json'
            
        # URL解码文名，处理中文和特字符
        old_filename = unquote(old_filename)
            
        old_path = os.path.join(app.config['SCENES_FOLDER'], old_filename)
        new_path = os.path.join(app.config['SCENES_FOLDER'], new_name)
        
        print(f"重命名: {old_path} -> {new_path}")  # 调试日志
        
        if not os.path.exists(old_path):
            print(f"原文件不存在: {old_path}")  # 调试日志
            return jsonify({'success': True})  # 即使文件不存在也返回成功
            
        if os.path.exists(new_path) and old_path != new_path:
            print(f"新文件名已存在: {new_path}")  # 调试日志
            return jsonify({'error': '文件名已存在'}), 400
            
        os.rename(old_path, new_path)
        print(f"重命名成功")  # 调试日志
        
        return jsonify({'success': True, 'newFilename': new_name})
    except Exception as e:
        print(f"重命名错误: {str(e)}")  # 调试日志
        return jsonify({'error': str(e)}), 500

@app.route('/share/<path:filename>')
def share_scene(filename):
    try:
        # URL解码文件名，处理中文和特殊字符
        decoded_filename = unquote(filename)
        filepath = os.path.join(app.config['SCENES_FOLDER'], decoded_filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': '场景不存在'}), 404
            
        # 读取场景数据以获取标题
        with open(filepath, 'r', encoding='utf-8') as f:
            scene_data = json.load(f)
            
        # 创建HTML内容，包含动态标题
        title = decoded_filename.replace('.json', '')
        
        # 读取原始index.html文件
        with open('public/index.html', 'r', encoding='utf-8') as f:
            original_html = f.read()
            
        # 在 <head> 标签后立即插入新的 meta 标签
        modified_html = original_html.replace('<head>', f'''<head>
    <title>{title} - 模型对比</title>
    <meta charset="utf-8">
    <meta property="og:title" content="{title} - 模型对比">
    <meta property="og:description" content="查看 {title} 的3D模型对比">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{request.url}">
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{title} - 模型对比">
    <meta name="twitter:description" content="查看 {title} 的3D模型对比">
    <meta name="description" content="查看 {title} 的3D模型对比">
    <meta name="keywords" content="3D模型,模型对比,{title}">''')
            
        return modified_html
        
    except Exception as e:
        print(f"分享场景错误: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/scenes/<path:filename>/download')
def download_scene(filename):
    try:
        # URL解码文件名
        decoded_filename = unquote(filename)
        scene_path = os.path.join(app.config['SCENES_FOLDER'], decoded_filename)
        
        if not os.path.exists(scene_path):
            return jsonify({'error': '场景不存在'}), 404
            
        # 读取场景数据
        with open(scene_path, 'r', encoding='utf-8') as f:
            scene_data = json.load(f)
            
        # 创建内存中的ZIP文件
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 使用场景名称作为主文件夹名（移除.json后缀）
            base_folder = os.path.splitext(decoded_filename)[0]
            
            # 添加所有模型文件
            if 'models' in scene_data:
                for i, model in enumerate(scene_data['models'], 1):
                    # 在主文件夹下创建模型子文件夹
                    model_folder = f'{base_folder}/模型{i}'
                    
                    # 添加OBJ文件
                    if 'objFile' in model:
                        obj_path = os.path.join(app.root_path, model['objFile'].lstrip('/'))
                        if os.path.exists(obj_path):
                            zf.write(obj_path, f'{model_folder}/{os.path.basename(obj_path)}')
                    
                    # 添加MTL文件
                    if 'mtlFile' in model:
                        mtl_path = os.path.join(app.root_path, model['mtlFile'].lstrip('/'))
                        if os.path.exists(mtl_path):
                            zf.write(mtl_path, f'{model_folder}/{os.path.basename(mtl_path)}')
                    
                    # 添加贴图文件
                    if 'textureFile' in model:
                        texture_path = os.path.join(app.root_path, model['textureFile'].lstrip('/'))
                        if os.path.exists(texture_path):
                            zf.write(texture_path, f'{model_folder}/{os.path.basename(texture_path)}')
        
        # 将文件指针移到开始
        memory_file.seek(0)
        
        # 使用时间戳作为下载文件名
        timestamp = time.strftime("%y-%m-%d_%H-%M-%S", time.localtime())
        
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'{timestamp}.zip'
        )
        
    except Exception as e:
        print(f"下载场景错误: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print(f"上传目录: {UPLOAD_FOLDER}")
    print(f"场景目录: {SCENES_FOLDER}")
    
    # 启动服务器
    app.run(debug=True, host='0.0.0.0', port=3000, threaded=True) 