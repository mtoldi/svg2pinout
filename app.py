from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import subprocess
from werkzeug.utils import secure_filename

app = Flask(__name__)

# === SVG PIN EDITOR ===
SKU_FOLDER = 'static/uploaded'
os.makedirs(SKU_FOLDER, exist_ok=True)
ALLOWED_SVG = {'svg'}

def allowed_svg(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_SVG

@app.route('/editor', methods=['GET', 'POST'])
def editor():
    if request.method == 'POST':
        f = request.files.get('file')
        if f and allowed_svg(f.filename):
            filename = secure_filename("sku.svg")
            f.save(os.path.join(SKU_FOLDER, filename))
            return '', 204  # Let the frontend reload the SVG manually
    return render_template('editor.html')

@app.route('/svg/sku.svg')
def serve_svg():
    return send_from_directory(SKU_FOLDER, 'sku.svg')


# === KICAD TO SVG ===
KICAD_UPLOAD = 'uploads'
SVG_LAYER_FOLDER = 'static/svg_layers'
os.makedirs(KICAD_UPLOAD, exist_ok=True)
os.makedirs(SVG_LAYER_FOLDER, exist_ok=True)
ALLOWED_KICAD = {'kicad_pcb'}

def allowed_kicad(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_KICAD

def export_svg_layers(pcb_path, output_dir):
    subprocess.run([
        "kicad-cli", "pcb", "export", "svg", pcb_path,
        "--layers", "Edge.Cuts,F.Silkscreen,User.Drawings,F.Mask",
        "--mode-multi",
        "--output", output_dir,
        "--black-and-white",
        "--exclude-drawing-sheet",
        "--page-size-mode", "2"
    ])

@app.route('/kicad', methods=['GET', 'POST'])
def kicad():
    svg_files = []

    if request.method == 'POST':
        file = request.files.get('file')
        if file and allowed_kicad(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(KICAD_UPLOAD, filename)
            file.save(path)

            # Clear old layers
            for f in os.listdir(SVG_LAYER_FOLDER):
                os.remove(os.path.join(SVG_LAYER_FOLDER, f))

            export_svg_layers(path, SVG_LAYER_FOLDER)

    svg_files = [f for f in os.listdir(SVG_LAYER_FOLDER) if f.endswith('.svg')]
    return render_template('kicad_index.html', svg_files=svg_files)


@app.route('/kicad/svg/<filename>')
def serve_layer(filename):
    return send_from_directory(SVG_LAYER_FOLDER, filename)


# === COMPOSER ===
COMPOSER_FOLDER = 'static/composer_upload'
os.makedirs(COMPOSER_FOLDER, exist_ok=True)

@app.route('/composer', methods=['GET', 'POST'])
def composer():
    if request.method == 'POST':
        f = request.files.get('file')
        if f and allowed_svg(f.filename):
            filename = secure_filename("composed.svg")
            f.save(os.path.join(COMPOSER_FOLDER, filename))
            return '', 204  # JS will refresh view
    return render_template('composer.html')

@app.route('/composer/svg')
def serve_composer_svg():
    return send_from_directory(COMPOSER_FOLDER, 'composed.svg')


# === HOME ===
@app.route('/')
def home():
    return render_template('homepage.html')
