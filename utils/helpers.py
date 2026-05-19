import os
import sys

def get_asset_path(path):
    """
    Returns the absolute path to an asset, handling:
    - PyInstaller (_MEIPASS)
    - Normal script execution
    - Android (if assets are in standard location)
    """
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    return os.path.join(base_path, path)

def get_storage_path():
    """
    Returns the writable storage path for the application.
    On Android, this is the App's user_data_dir.
    On Desktop, it resolves securely to %APPDATA%/RemindMe to avoid dropping clutter next to the standalone .exe.
    """
    from kivy.utils import platform
    
    if platform == 'android':
        from kivy.app import App
        try:
             app = App.get_running_app()
             if app:
                 return app.user_data_dir
        except:
             pass
             
    # Route Windows desktop installations to secure hidden AppData scope 
    if platform == 'win':
        base = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'RemindMe')
    else:
        base = os.path.join(os.path.expanduser('~'), '.remindme')
        
    os.makedirs(base, exist_ok=True)
    return base

def copy_bundled_data(storage_path):
    """
    Extracts bundled databases, configs, and crypto bins from read-only APK
    or _MEIPASS into the permanent writable storage directory on first launch.
    """
    import shutil
    import glob
    import logging
    
    source_dir = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Don't copy if source is exactly the storage path (running from IDE directly)
    if os.path.normpath(source_dir) == os.path.normpath(storage_path):
        return
        
    copied_files = 0
    for ext in ("*.db", "*.json", "*.txt", "*.bin"):
        for file_path in glob.glob(os.path.join(source_dir, ext)):
            filename = os.path.basename(file_path)
            dest_path = os.path.join(storage_path, filename)
            
            # Do NOT overwrite if it already exists to prevent data wiping
            if not os.path.exists(dest_path):
                try:
                    # Use shutil.copy instead of copy2 to avoid metadata permission errors on Android
                    shutil.copy(file_path, dest_path)
                    copied_files += 1
                except Exception as e:
                    logging.error(f"Failed to copy bundled asset {filename} to {dest_path}: {e}")
                    # On some Android versions, even simple copy can fail if file exists or is read-only
                    pass 
    if copied_files > 0:
        logging.info(f"Copied {copied_files} essential files to persistent storage.")
