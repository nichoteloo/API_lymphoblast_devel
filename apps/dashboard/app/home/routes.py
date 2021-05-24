import os
import json
import requests
from app.home import blueprint
from flask import render_template, redirect, request, url_for, flash
from flask_login import login_required, current_user
from app import login_manager
from jinja2 import TemplateNotFound

BASE_URL = 'http://127.0.0.1:8000'

@blueprint.route('/index')
@login_required
def index():
    return render_template('index.html', segment='index')

@blueprint.route('/<template>')
@login_required
def route_template(template):
    try:
        if not template.endswith( '.html' ):
            template += '.html'
        # Detect the current page
        segment = get_segment( request )
        # Serve the file (if exists) from app/templates/FILE.html
        return render_template( template, segment=segment )
    except TemplateNotFound:
        return render_template('page-404.html'), 404
    except:
        return render_template('page-500.html'), 500

# Helper - Extract current page name from request 
def get_segment( request ): 
    try:
        segment = request.path.split('/')[-1]
        if segment == '':
            segment = 'index'
        return segment    
    except:
        return None  

## helper functions 2
def send_image_req(url,data):
    my_img = {'file': open(data, 'rb')}
    response = requests.post(url, files=my_img)
    return response.json()

def serve_endpoint(endpoint):
    return BASE_URL + endpoint


## routing functions
@blueprint.route('/uploaded.html', methods=['GET','POST'])
def upload_img():
    if request.method == 'POST':
        file = request.files.get('file')
        data = file.filename
        response = send_image_req(serve_endpoint('/devel/api/upload'),data)
        saved = response['saved']
        recent_path = serve_endpoint(response['recent_upload'])
        list_upload = [serve_endpoint(x) for x in response['list_upload'].values()]

        if saved:
            flash('Yey image successfully uploaded and predicted. All result shown below')
            return render_template('uploaded.html', recent_path=recent_path, list_upload=list_upload)
        else:    
            flash('Nothing happens so far')
            return render_template("select.html")
    elif request.method == 'GET':
        response = requests.get(serve_endpoint('/storage/uploads')).json()
        list_upload = [serve_endpoint(x) for x in response.values()]
        return render_template('uploaded.html', list_upload=list_upload)
    flash("Your request is not reached")
    return render_template("select.html", messages="Your request is not reached")

@blueprint.route('/preprocess', methods=['POST'])
def preprocess_img():
    if request.method == 'POST':
        if 'delete' in request.form:
            filename = str(os.path.basename(request.form.get('upload_path')))
            response = requests.get(serve_endpoint(f'/api/delete_upload/{filename}')).json()
            if response['delete']:
                list_upload = [serve_endpoint(x) for x in response["list_upload"].values()]
                render_template("uploaded.html", messages=f"Image {filename} success deleted", list_upload=list_upload)
                flash(f"Image {filename} success deleted")
                return redirect(url_for('home_blueprint.upload_img'))
        elif 'close' in request.form:
            response = requests.get(serve_endpoint('/storage/uploads')).json()
            list_upload = [serve_endpoint(x) for x in response.values()]
            render_template('uploaded.html', list_upload=list_upload)
            return redirect(url_for('home_blueprint.upload_img'))
        return 0

@blueprint.route('/result-one.html', methods=['POST'])
def process_result():
    if request.method == 'POST':
        if 'process' in request.form:
            filename = os.path.basename(request.form.get('upload_path'))
            response = requests.get(serve_endpoint(f'/devel2/api/opencv/{filename}')).json()
            result_path = serve_endpoint(response["result_path"])
            upload_path = serve_endpoint(f"/storage/uploads/{filename}")
            return render_template('result-one.html', upload_path=upload_path, result_path=result_path)

@blueprint.route('/extracted.html', methods=['POST'])
def extract_result():
    if request.method == 'POST':
        if 'extract' in request.form:
            filename = os.path.basename(request.form.get('upload_path'))
            response = requests.get(serve_endpoint(f'/devel2/api/opencv/{filename}')).json()
            extract_path = [BASE_URL+x for x in response["extract_path"]]
            upload_path = serve_endpoint(f"/storage/uploads/{filename}")
            return render_template('extracted.html', upload_path=upload_path, extract_path=extract_path)
