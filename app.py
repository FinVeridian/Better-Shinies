import os, io, re, zipfile
from flask import Flask, render_template, request, send_file, url_for

app = Flask(__name__)
FILES_DIR = os.path.join('static', 'files')

@app.route('/')
def index():
    file_map = {}
    for folder in sorted(os.listdir(FILES_DIR)):
        folder_path = os.path.join(FILES_DIR, folder)
        if not os.path.isdir(folder_path):
            continue

        m = re.match(r'^\d+_(.+)$', folder)
        cat_display = m.group(1).capitalize() if m else folder.capitalize()
        entries = []
        seen_bases = set()
        extended_map = {}

        for fn in sorted(os.listdir(folder_path)):
            full_path = os.path.join(folder_path, fn)
            if not os.path.isfile(full_path) or not fn.endswith('.png'):
                continue

            m_base = re.match(r'(\w+)_([\w]+)_(\d+)\.png$', fn)
            m_ext = re.match(r'(\w+)_([\w]+)_([\w]+)_(\d+)\.png$', fn)

            if m_base:
                base_key = f"{m_base.group(1)}_{m_base.group(2)}_{m_base.group(3)}"
                seen_bases.add(base_key)
            elif m_ext:
                ext_base_key = f"{m_ext.group(1)}_{m_ext.group(2)}_{m_ext.group(4)}"
                extended_map[ext_base_key] = fn

        for fn in sorted(os.listdir(folder_path)):
            full_path = os.path.join(folder_path, fn)
            if not os.path.isfile(full_path) or not fn.endswith('.png'):
                continue

            m_base = re.match(r'(\w+)_([\w]+)_(\d+)\.png$', fn)
            m_ext = re.match(r'(\w+)_([\w]+)_([\w]+)_(\d+)\.png$', fn)

            # Skip extended files if their base version exists
            if m_ext:
                ext_base_key = f"{m_ext.group(1)}_{m_ext.group(2)}_{m_ext.group(4)}"
                if ext_base_key in seen_bases:
                    continue

            # Only show file if it hasn't already been skipped
            display = None
            desc_path = os.path.join('static', 'descriptions', folder, fn.replace('.png', '.txt'))
            if os.path.isfile(desc_path):
                with open(desc_path, encoding='utf-8') as f:
                    display = f.readline().strip()
            if not display:
                m2 = re.match(r'(\w+)_([\w]+)_(\d+)\.png$', fn)
                display = f"{m2.group(1).capitalize()} {m2.group(2).capitalize()}" if m2 else fn

            entries.append({'filename': fn, 'display_name': display, 'folder': folder})

        file_map[cat_display] = entries

    return render_template('index.html', file_map=file_map)


@app.route('/download', methods=['POST'])
def download():
    selected = request.form.getlist('files')
    if not selected:
        return "No files selected", 400

    memory = io.BytesIO()
    with zipfile.ZipFile(memory, 'w', zipfile.ZIP_DEFLATED) as zf:
        for item in selected:
            cat, fn = item.split('/', 1)
            folder_path = os.path.join(FILES_DIR, cat)
            src = os.path.join(folder_path, fn)

            # Base file renaming
            m = re.match(r'(\w+)_([\w]+)_(\d+)\.png$', fn)
            if m:
                new_fn = f"{m.group(1)}_{m.group(2)}.png"
            else:
                new_fn = fn

            arc = os.path.join("assets/cobblemon/textures/pokemon", cat, new_fn)

            if os.path.isfile(src):
                zf.write(src, arcname=arc)

            # Add extended file if it exists
            if m:
                base_1, base_2, number = m.group(1), m.group(2), m.group(3)
                for ext_file in os.listdir(folder_path):
                    m_ext = re.match(rf'^{base_1}_{base_2}_(\w+?)_{number}\.png$', ext_file)
                    if m_ext:
                        ext_src = os.path.join(folder_path, ext_file)
                        # Strip number from extended filename: keep thing1_thing2_thing3
                        new_ext_fn = f"{base_1}_{base_2}_{m_ext.group(1)}.png"
                        ext_arc = os.path.join("assets/cobblemon/textures/pokemon", cat, new_ext_fn)
                        if os.path.isfile(ext_src):
                            zf.write(ext_src, arcname=ext_arc)

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
