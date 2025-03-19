import os
import datetime
import shutil
import filecmp
from flask import Flask, request, redirect, render_template

app = Flask(__name__)

destination = "/usr/local/structurizr"

def is_allowed_file(filename: str)->bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'dsl'}

def get_previous_uploads():
    uploads_dir = 'uploads'
    if not os.path.exists(uploads_dir):
        return []
    return [filename for filename in os.listdir(uploads_dir) if os.path.isfile(os.path.join(uploads_dir, filename))]

def get_file_preview(filename, max_lines=10)->tuple[str, bool]:
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
    
def get_current_active_file()->str|None:
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
    file = request.files['file']
    if not (file and is_allowed_file(file.filename)):
        return 'Invalid file', 400
    
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

@app.route('/')
def index():
    previous_uploads = get_previous_uploads()
    file_previews = {}
    
    for filename in previous_uploads:
        preview, has_more = get_file_preview(filename)
        file_previews[filename] = {
            'content': preview,
            'has_more': has_more,
            'timestamp': datetime.datetime.fromtimestamp(
                os.path.getmtime(os.path.join('uploads', filename))
            ).strftime("%Y-%m-%d %H:%M:%S"),
        }
    
    return render_template('base.html', 
                          previous_uploads=previous_uploads, 
                          file_previews=file_previews,
                          current_active_file=get_current_active_file()
                          )

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)