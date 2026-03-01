import os
import zipfile

def create_zip(output_filename):
    print(f"Creating {output_filename}...")
    
    # Files/Dirs to include
    includes = [
        'main.py',
        'buildozer.spec',
        'assets',
        'libs',
        'screens',
        'widgets',
        'utils',
        'backend',
        'requirements.txt',
        'README.md'
    ]
    
    # Also find all .json and .db files in root
    for file in os.listdir('.'):
        if file.endswith('.json') or file.endswith('.db') or file.endswith('.sh'):
            includes.append(file)

    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in includes:
            if os.path.isdir(item):
                for root, dirs, files in os.walk(item):
                    # Skip __pycache__
                    if '__pycache__' in dirs:
                        dirs.remove('__pycache__')
                    
                    for file in files:
                        if file.endswith('.pyc'): continue
                        
                        file_path = os.path.join(root, file)
                        # Archive name should be relative to project root
                        arcname = os.path.relpath(file_path, '.')
                        print(f"Adding {arcname}")
                        zipf.write(file_path, arcname)
            elif os.path.isfile(item):
                print(f"Adding {item}")
                zipf.write(item, item)
            else:
                print(f"Skipping {item} (not found)")

    if os.path.exists(output_filename):
        size = os.path.getsize(output_filename)
        print(f"\n✅ Success! Created {output_filename} ({size/1024:.2f} KB)")
    else:
        print("\n❌ Failed to create zip file.")

if __name__ == "__main__":
    create_zip("RemindMe_Source.zip")
