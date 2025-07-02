from flask import Flask, render_template, request, send_file
import os
import zipfile
import io
import re

app = Flask(__name__)
FILES_DIR = os.path.join('static', 'files')

@app.route('/')
def index():
    file_map = {}  # display_category_name -> list of file dicts

    for folder in os.listdir(FILES_DIR):
        folder_path = os.path.join(FILES_DIR, folder)
        if not os.path.isdir(folder_path):
            continue

        # Extract category display name from folder
        match = re.match(r'^\d+_(.+)$', folder)
        if match:
            display_category = match.group(1).capitalize()
        else:
            display_category = folder.capitalize()

        entries = []
        for file in os.listdir(folder_path):
            display_name = None

            # Description file logic
            desc_path = os.path.join('static', 'descriptions', folder, file.replace('.png', '.txt'))
            if os.path.isfile(desc_path):
                with open(desc_path, 'r', encoding='utf-8') as f:
                    display_name = f.readline().strip()

            # Fallback to parsed name
            if not display_name:
                match = re.match(r'(\w+)_([\w]+)_(\d+)\.png$', file)
                if match:
                    thing1, thing2, _ = match.groups()
                    display_name = f"{thing1.capitalize()} {thing2.capitalize()}"
                else:
                    display_name = file  # fallback

            entries.append({
                'filename': file,
                'display_name': display_name,
                'folder': folder  # keep original folder name for paths
            })

        file_map[display_category] = entries

    return render_template('index.html', file_map=file_map)



@app.route('/download', methods=['POST'])
def download():
    selected_files = request.form.getlist('files')
    if not selected_files:
        return "No files selected", 400

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for full_path in selected_files:
            category, filename = full_path.split('/', 1)
            source_path = os.path.join(FILES_DIR, category, filename)

            # Parse new name for inside the zip
            match = re.match(r'(\w+)_([\w]+)_(\d+)\.png$', filename)
            if match:
                thing1, thing2, _ = match.groups()
                new_filename = f"{thing1}_{thing2}.png"
            else:
                new_filename = filename  # fallback if not matching pattern

            zip_path = os.path.join(
                "assets", "cobblemon", "textures", "pokemon", category, new_filename
            )
            if os.path.isfile(source_path):
                zf.write(source_path, arcname=zip_path)

        # Add pack.mcmeta
        mcmeta_content = '''{
  "pack": {
    "pack_format": 34,
    "description": "giving eeveelutions non-dogshit shinies since right now"
  }
}'''
        zf.writestr("pack.mcmeta", mcmeta_content)

    memory_file.seek(0)
    return send_file(
        memory_file,
        download_name="Better Shinies.zip",
        as_attachment=True,
        mimetype='application/zip'
    )

if __name__ == '__main__':
    app.run(debug=True)
