import os, io, re, zipfile
from flask import Flask, render_template, request, send_file, url_for

app = Flask(__name__)
FILES_DIR = os.path.join('static', 'files')

@app.route('/')
def index():
    file_map = {}
    for folder in sorted(os.listdir(FILES_DIR)):
        folder_path = os.path.join(FILES_DIR, folder)
        if not os.path.isdir(folder_path): continue

        m = re.match(r'^\d+_(.+)$', folder)
        cat_display = m.group(1).capitalize() if m else folder.capitalize()
        entries = []
        for fn in sorted(os.listdir(folder_path)):
            display = None
            desc_path = os.path.join('static', 'descriptions', folder, fn.replace('.png', '.txt'))
            if os.path.isfile(desc_path):
                with open(desc_path, encoding='utf-8') as f: display = f.readline().strip()
            if not display:
                m2 = re.match(r'(\w+)_([\w]+)_(\d+)\.png$', fn)
                display = f"{m2.group(1).capitalize()} {m2.group(2).capitalize()}" if m2 else fn

            entries.append({'filename': fn, 'display_name': display, 'folder': folder})
        file_map[cat_display] = entries

    return render_template('index.html', file_map=file_map)

@app.route('/download', methods=['POST'])
def download():
    selected = request.form.getlist('files')
    if not selected: return "No files selected", 400

    memory = io.BytesIO()
    with zipfile.ZipFile(memory, 'w', zipfile.ZIP_DEFLATED) as zf:
        for item in selected:
            cat, fn = item.split('/', 1)
            src = os.path.join(FILES_DIR, cat, fn)
            m = re.match(r'(\w+)_([\w]+)_(\d+)\.png$', fn)
            new_fn = f"{m.group(1)}_{m.group(2)}.png" if m else fn
            arc = os.path.join("assets/cobblemon/textures/pokemon", cat, new_fn)
            if os.path.isfile(src): zf.write(src, arcname=arc)

        mcmeta = '''{
  "pack": {
    "pack_format": 34,
    "description": "giving eeveelutions non-dogshit shinies since right now"
  }
}'''
        zf.writestr("pack.mcmeta", mcmeta)

    memory.seek(0)
    return send_file(memory, download_name="Better Shinies.zip", as_attachment=True, mimetype='application/zip')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
