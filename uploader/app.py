import os
import datetime
import shutil
import filecmp
from flask import Flask, request, redirect, render_template, jsonify, url_for
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
from wtforms import FileField
from wtforms.validators import FileRequired


app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
destination = "/usr/local/structurizr"


csrf = CSRFProtect(app)

class UploadForm(FlaskForm):
    file = FileField('File', validators=[FileRequired()])
    

def is_allowed_file(filename: str)->bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'dsl'}

def get_previous_uploads():
    uploads_dir = 'uploads'
    if not os.path.exists(uploads_dir):
        return []
    return [f for f in os.listdir(uploads_dir) if os.path.isfile(os.path.join(uploads_dir, f))]

def get_file_preview(filename, max_lines=10):
    """Get a preview of the file contents, limited to a specified number of lines."""
    filepath = os.path.join('uploads', filename)
    try:
        with open(filepath, 'r') as file:
            lines = file.readlines()
            preview = ''.join(lines[:max_lines])
            has_more = len(lines) > max_lines
            return preview, has_more
    except Exception as e:
        return f"Error reading file: {str(e)}", False

def get_current_active_file():
    """Determine which uploaded file is currently being used as the active workspace file."""
    workspace_path = os.path.join(destination, 'workspace.dsl')
    if not os.path.exists(workspace_path):
        return None
    
    uploads_dir = 'uploads'
    if not os.path.exists(uploads_dir):
        return None
    
    for filename in os.listdir(uploads_dir):
        file_path = os.path.join(uploads_dir, filename)
        if os.path.isfile(file_path):
            try:
                if filecmp.cmp(file_path, workspace_path, shallow=False):
                    return filename
            except:
                pass
    
    return None

@app.route('/upload', methods=['POST'])
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        file = form.file.data
        if not (file and is_allowed_file(file.filename)):
            return 'Invalid file', 400

    if request.content_length > app.config['MAX_CONTENT_LENGTH']:
        return 'File too large', 413
    
    os.makedirs('uploads', exist_ok=True)
    upload_path = os.path.join('uploads', file.filename)
    file.save(upload_path)

    try:
        workspace_path = os.path.join(destination, 'workspace.dsl')
        if os.path.exists(workspace_path):
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y-%m-%d-%H-%M-%S")
            backup_name = f"workspace-{timestamp}.dsl"
            backup_path = os.path.join('uploads', backup_name)

            shutil.copy2(workspace_path, backup_path)
        shutil.copy2(upload_path, workspace_path)
    except Exception as exception:
        return f"An error occurred: {exception}", 500

    return redirect('/')

@app.route('/set-current/<filename>', methods=['POST'])
def set_current(filename):
    """Set a previously uploaded file as the current workspace file."""
    try:
        # Validate filename exists
        file_path = os.path.join('uploads', filename)
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': 'File not found'}), 404
        
        # Make backup of current workspace file
        workspace_path = os.path.join(destination, 'workspace.dsl')
        if os.path.exists(workspace_path):
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y-%m-%d-%H-%M-%S")
            backup_name = f"workspace-{timestamp}.dsl"
            backup_path = os.path.join('uploads', backup_name)
            shutil.copy2(workspace_path, backup_path)
        
        # Set the new file as current
        shutil.copy2(file_path, workspace_path)
        
        return jsonify({'success': True, 'message': f'Set {filename} as current file'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/delete-upload/<filename>', methods=['POST'])
def delete_upload(filename):
    """Delete a previously uploaded file."""
    try:
        # Check if file is current
        if filename == get_current_active_file():
            return jsonify({
                'success': False, 
                'message': 'Cannot delete the currently active file'
            }), 400
        
        # Validate file exists
        file_path = os.path.join('uploads', filename)
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': 'File not found'}), 404
        
        # Delete the file
        os.remove(file_path)
        
        return jsonify({'success': True, 'message': f'Deleted {filename}'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/')
def index():
    previous_uploads = get_previous_uploads()
    file_previews = {}
    current_active_file = get_current_active_file()
    
    for filename in previous_uploads:
        preview, has_more = get_file_preview(filename)
        file_previews[filename] = {
            'content': preview,
            'has_more': has_more,
            'timestamp': datetime.datetime.fromtimestamp(
                os.path.getmtime(os.path.join('uploads', filename))
            ).strftime("%Y-%m-%d %H:%M:%S"),
            'is_active': filename == current_active_file
        }
    
    return render_template('base.html', 
                          previous_uploads=previous_uploads, 
                          file_previews=file_previews,
                          current_active_file=current_active_file)

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)