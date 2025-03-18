import os
import datetime 
from flask import Flask, request, redirect, render_template

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    file.save(os.path.join('uploads', file.filename))
    return redirect('/')

@app.route('/')
def index():
    return render_template('base.html')

if __name__ == '__main__':
    app.run(debug=True)