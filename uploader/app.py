import os
import datetime
import shutil
from flask import Flask, request, redirect, render_template

app = Flask(__name__)

destination = "/usr/local/structurizr"

def is_allowed_file(filename: str)->bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'dsl'}

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
    return render_template('base.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)