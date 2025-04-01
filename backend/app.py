import os
import uuid
import subprocess
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import shutil

app = Flask(__name__)

# 获取当前文件的绝对路径
BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
# 项目根目录
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
# 图片存储根目录
IMG_ROOT = os.path.join(BACKEND_DIR, 'img')
app.config['UPLOAD_FOLDER'] = IMG_ROOT
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB最大限制

# 虚拟环境Python解释器路径
VENV_PYTHON = os.path.join(PROJECT_ROOT, '.venv', 'Scripts', 'python.exe')

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"创建目录: {directory}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    
    # 创建唯一ID和目录
    session_id = str(uuid.uuid4())
    upload_dir_a = os.path.join(IMG_ROOT, session_id, 'upload', 'testA')
    upload_dir_b = os.path.join(IMG_ROOT, session_id, 'upload', 'testB')
    result_dir = os.path.join(IMG_ROOT, session_id, 'result')
    
    ensure_dir(upload_dir_a)
    ensure_dir(upload_dir_b)
    ensure_dir(result_dir)
    
    # 保存文件到testA和testB目录
    filename = secure_filename(str(file.filename))
    file_path_a = os.path.join(upload_dir_a, filename)
    file_path_b = os.path.join(upload_dir_b, filename)
    
    file.save(file_path_a)
    # 为testB创建副本
    shutil.copy(file_path_a, file_path_b)
    
    # 运行GAN模型
    try:
        # 准备绝对路径
        dataroot_path = os.path.join(IMG_ROOT, session_id, 'upload')
        results_path = os.path.join(IMG_ROOT, session_id, 'result')
        
        cmd = [
            VENV_PYTHON,
            os.path.join(PROJECT_ROOT, 'test.py'),
            '--dataroot', dataroot_path,
            '--name', 'maps_cyclegan',
            '--model', 'cycle_gan',
            '--phase', 'test',
            '--num_test', '100',
            '--direction', 'AtoB',
            '--results_dir', results_path
        ]
        
        print("执行命令:", " ".join(cmd))
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        print("标准输出:", stdout.decode('utf-8'))
        print("标准错误:", stderr.decode('utf-8'))
        
        if process.returncode != 0:
            return f"运行模型时出错: {stderr.decode('utf-8')}"
        
        # 查找fake_B结果文件
        result_file = None
        result_web_dir = os.path.join(result_dir, 'maps_cyclegan', 'test_latest', 'images')
        if os.path.exists(result_web_dir):
            for f in os.listdir(result_web_dir):
                if f.endswith('_fake_B.png'):
                    result_file = f
                    break
        
        if result_file:
            return redirect(url_for('show_result', session_id=session_id, filename=result_file))
        else:
            return "转换完成，但找不到结果文件。"
            
    except Exception as e:
        import traceback
        return f"发生错误: {str(e)}<br>详细信息:<pre>{traceback.format_exc()}</pre>"

@app.route('/result/<session_id>/<filename>')
def show_result(session_id, filename):
    result_path = os.path.join(app.config['UPLOAD_FOLDER'], session_id, 'result', 'maps_cyclegan', 'test_latest', 'images', filename)
    original_filename = filename.replace('_fake_B.png', '')
    
    return render_template('result.html', 
                         result_image=f'/image/{session_id}/{filename}',
                         original_filename=original_filename)

@app.route('/image/<session_id>/<filename>')
def get_image(session_id, filename):
    image_dir = os.path.join(app.config['UPLOAD_FOLDER'], session_id, 'result', 'maps_cyclegan', 'test_latest', 'images')
    return send_from_directory(image_dir, filename)

if __name__ == '__main__':
    # 确保img目录存在
    ensure_dir(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
