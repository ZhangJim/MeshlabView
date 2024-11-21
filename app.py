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
import re

app = Flask(__name__)
print("Flask app created")
app.secret_key = 'your-secret-key-here'
CORS(app)

# 配置文件保存路径
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
SCENES_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scenes')
ORIGINAL_IMAGES_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'original_images')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SCENES_FOLDER'] = SCENES_FOLDER
app.config['ORIGINAL_IMAGES_FOLDER'] = ORIGINAL_IMAGES_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# 确保必要的文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SCENES_FOLDER, exist_ok=True)
os.makedirs(ORIGINAL_IMAGES_FOLDER, exist_ok=True)

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
        scene_name = f'scene-{timestamp}'
        
        # 遍历所有临时原图文件,重命名并记录到场景数据中
        original_images = []
        for file in os.listdir(app.config['ORIGINAL_IMAGES_FOLDER']):
            if file.startswith('temp_'):
                match = re.search(r'temp_\d+_model_(\d+)_', file)
                if match:
                    model_index = int(match.group(1))
                    new_filename = file.replace(file[:file.find('_model_')], scene_name)
                    old_path = os.path.join(app.config['ORIGINAL_IMAGES_FOLDER'], file)
                    new_path = os.path.join(app.config['ORIGINAL_IMAGES_FOLDER'], new_filename)
                    os.rename(old_path, new_path)
                    original_images.append({
                        'model_index': model_index,
                        'filename': new_filename
                    })
        
        # 将原图信息添加到场景数据中
        scene_data['original_images'] = original_images
        
        # 保存场景数据
        filepath = os.path.join(app.config['SCENES_FOLDER'], filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(scene_data, f, ensure_ascii=False)
        
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        print(f"保存场景错误: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
            # 获取或创建新的时间戳文件夹名
            timestamp = session.get('current_upload_timestamp')
            if not timestamp:
                current_time = time.localtime()
                timestamp = time.strftime("%y-%m-%d_%H-%M-%S", current_time)
                session['current_upload_timestamp'] = timestamp
                print(f"创建新的时间戳: {timestamp}")
            else:
                print(f"使用现有时间戳: {timestamp}")
            
            folder_path = os.path.join(app.config['UPLOAD_FOLDER'], timestamp)
            os.makedirs(folder_path, exist_ok=True)
            
            filename = secure_filename(file.filename)
            filepath = os.path.join(folder_path, filename)
            
            # 如果是OBJ文件，检查并添加材质声明
            if filename.lower().endswith('.obj'):
                # 先保存文件
                file.save(filepath)
                
                # 读取文件内容
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查是否包含材质声明
                if 'usemtl material_0' not in content:
                    print(f"OBJ文件缺少材质声明，正在添加: {filename}")
                    
                    # 在文件开头添加材质声明（在mtllib行之后）
                    lines = content.split('\n')
                    insert_index = 0
                    
                    # 找到mtllib行的位置
                    for i, line in enumerate(lines):
                        if line.startswith('mtllib'):
                            insert_index = i + 1
                            break
                    
                    # 插入材质声明
                    lines.insert(insert_index, 'usemtl material_0')
                    
                    # 保存修改后的文件
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(lines))
                    
                    print(f"已添加材质声明到文件: {filename}")
            else:
                # 非OBJ文件直接保存
                file.save(filepath)
            
            print(f"文件保存成功: {filepath}")
            
            # 只在上传完整组文件后清除session
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                session.pop('current_upload_timestamp', None)
                print("上传完成，清除时间戳")
            
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

# 添加CORS支
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
            
        # URL解码文件名，处理中文和特殊字符
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
            
        # 读取场景数据以获取原图信息
        with open(old_path, 'r', encoding='utf-8') as f:
            scene_data = json.load(f)
        
        # 重命名场景文件
        os.rename(old_path, new_path)
        
        # 获取旧的和新的场景名（不包含.json后缀）
        old_scene_name = old_filename.replace('.json', '')
        new_scene_name = new_name.replace('.json', '')
        
        # 重命名所有相关的原图文件
        if 'original_images' in scene_data:
            for image in scene_data['original_images']:
                old_image_name = image['filename']
                new_image_name = old_image_name.replace(old_scene_name, new_scene_name)
                old_image_path = os.path.join(app.config['ORIGINAL_IMAGES_FOLDER'], old_image_name)
                new_image_path = os.path.join(app.config['ORIGINAL_IMAGES_FOLDER'], new_image_name)
                if os.path.exists(old_image_path):
                    os.rename(old_image_path, new_image_path)
                    image['filename'] = new_image_name
                    print(f"重命名原图: {old_image_path} -> {new_image_path}")  # 调试日志
        
        # 保存更新后的场景数据
        with open(new_path, 'w', encoding='utf-8') as f:
            json.dump(scene_data, f, ensure_ascii=False)
        
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
    <meta name="keywords" content="3D模型,型对比,{title}">''')
            
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
                    
                    # 检查并添加原图（如果存在）
                    scene_name = base_folder
                    for filename in os.listdir(app.config['ORIGINAL_IMAGES_FOLDER']):
                        if filename.startswith(f"{scene_name}_model_{i-1}_"):
                            original_path = os.path.join(app.config['ORIGINAL_IMAGES_FOLDER'], filename)
                            # 保持原始扩展名
                            original_ext = os.path.splitext(filename)[1]
                            zf.write(original_path, f'{model_folder}/original{original_ext}')
                            break
        
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

@app.route('/upload_original_image', methods=['POST'])
def upload_original_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    scene_name = request.form.get('scene_name')
    model_index = request.form.get('model_index')
    
    print(f"上传原图: scene_name={scene_name}, model_index={model_index}")  # 调试日志
    
    if file and allowed_file(file.filename):
        # 修改这里：使用scene_name作为前缀，而不是temp_timestamp
        filename = f"{scene_name}_model_{model_index}_{secure_filename(file.filename)}"
        
        # 删除已存在的原图
        for existing_file in os.listdir(app.config['ORIGINAL_IMAGES_FOLDER']):
            if existing_file.startswith(f"{scene_name}_model_{model_index}_"):
                os.remove(os.path.join(app.config['ORIGINAL_IMAGES_FOLDER'], existing_file))
        
        file_path = os.path.join(app.config['ORIGINAL_IMAGES_FOLDER'], filename)
        file.save(file_path)
        print(f"保存原图: {filename}")  # 调试日志
        return jsonify({'success': True, 'filename': filename})
    
    return jsonify({'error': 'Invalid file'}), 400

@app.route('/delete_original_image', methods=['POST'])
def delete_original_image():
    scene_name = request.json.get('scene_name')
    model_index = request.json.get('model_index')
    
    for filename in os.listdir(app.config['ORIGINAL_IMAGES_FOLDER']):
        if filename.startswith(f"{scene_name}_model_{model_index}_"):
            os.remove(os.path.join(app.config['ORIGINAL_IMAGES_FOLDER'], filename))
            return jsonify({'success': True})
    
    return jsonify({'error': 'File not found'}), 404

@app.route('/get_original_image/<scene_name>/<model_index>')
def get_original_image(scene_name, model_index):
    scene_name = unquote(scene_name)
    print(f"查找原图: scene_name={scene_name}, model_index={model_index}")  # 调试日志
    
    for filename in os.listdir(app.config['ORIGINAL_IMAGES_FOLDER']):
        print(f"检查文件: {filename}")  # 调试日志
        if filename.startswith(f"{scene_name}_model_{model_index}_"):
            print(f"找到匹配文件: {filename}")  # 调试日志
            return send_from_directory(app.config['ORIGINAL_IMAGES_FOLDER'], filename)
    
    print("未找到匹配的原图")  # 调试日志
    return jsonify({'error': 'Image not found'}), 404

@app.route('/copy_original_image', methods=['POST'])
def copy_original_image():
    try:
        data = request.get_json()
        old_scene_name = data.get('oldSceneName')
        new_scene_name = data.get('newSceneName')
        model_index = data.get('modelIndex')
        
        # 查找旧的原图
        old_image = None
        for filename in os.listdir(app.config['ORIGINAL_IMAGES_FOLDER']):
            if filename.startswith(f"{old_scene_name}_model_{model_index}_"):
                old_image = filename
                break
        
        if old_image:
            # 构建新的文件名
            new_image = old_image.replace(old_scene_name, new_scene_name)
            
            # 复制文件
            old_path = os.path.join(app.config['ORIGINAL_IMAGES_FOLDER'], old_image)
            new_path = os.path.join(app.config['ORIGINAL_IMAGES_FOLDER'], new_image)
            shutil.copy2(old_path, new_path)
            
            # 删除旧文件
            os.remove(old_path)
            
            return jsonify({'success': True})
            
    except Exception as e:
        print(f"复制原图错误: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask server...")
    print(f"上传目录: {UPLOAD_FOLDER}")
    print(f"场景目录: {SCENES_FOLDER}")
    print(f"原始图像目录: {ORIGINAL_IMAGES_FOLDER}")
    
    # 启动服务器
    app.run(debug=True, host='0.0.0.0', port=3000, threaded=True) 