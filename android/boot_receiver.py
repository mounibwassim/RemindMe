from jnius import autoclass
from android.storage import app_storage_path
import os

def on_boot_completed():
    print("Android Boot Completed — Restarting Scheduler Service")
    try:
        PythonService = autoclass('org.kivy.android.PythonService')
        Intent = autoclass('android.content.Intent')
        mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
        
        service_intent = Intent(mActivity, PythonService)
        mActivity.startForegroundService(service_intent)
    except Exception as e:
        print(f"Boot Restart Error: {e}")
