import os
from flask import Flask, request, redirect, render_template

app = Flask(__name__)

def is_allowed_file(filename: str)->bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'dsl'}

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if not (file and is_allowed_file(file.filename)):
        return 'Invalid file', 400
    file.save(os.path.join('uploads', file.filename))
    return redirect('/')

@app.route('/')
def index():
    return render_template('base.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)