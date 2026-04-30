try:
    from jnius import autoclass # type: ignore
except ImportError:
    autoclass = None

try:
    from android.storage import app_storage_path # type: ignore
except ImportError:
    app_storage_path = None

try:
    from plyer import notification
except ImportError:
    notification = None
import os
import time
import sqlite3
import datetime

POLL_INTERVAL = 60

def get_current_db_path():
    if not app_storage_path:
        return None
    storage = app_storage_path()
    last_user_file = os.path.join(storage, "last_user.txt")
    if os.path.exists(last_user_file):
        try:
            with open(last_user_file, "r") as f:
                username = f.read().strip()
                if username:
                    return os.path.join(storage, f"tasks_{username}.db")
        except:
            pass
    return None

def run_service():
    if not autoclass:
        print("Jnius (autoclass) not available, service cannot initialize native components.")
        # But we continue the loop for polling if possible, or exit
    
    try:
        if autoclass:
            PythonService = autoclass('org.kivy.android.PythonService')
            # 🔴 CRITICAL: Android 12+ requires startForeground to be called by the service itself
            NotificationBuilder = autoclass('android.app.Notification$Builder')
            NotificationChannel = autoclass('android.app.NotificationChannel')
            NotificationManager = autoclass('android.app.NotificationManager')
            Context = autoclass('android.content.Context')
            
            # Use the same channel as main app
            channel_id = 'remindme_service_channel'
            channel = NotificationChannel(channel_id, 'RemindMe Background Service', 2) # Importance LOW
            
            notification_service = PythonService.mService.getSystemService(Context.NOTIFICATION_SERVICE)
            notification_service.createNotificationChannel(channel)
            
            # Create a minimal notification for the service
            notification_builder = NotificationBuilder(PythonService.mService, channel_id)
            notification_builder.setContentTitle("RemindMe Scheduler")
            notification_builder.setContentText("Monitoring your upcoming tasks...")
            notification_builder.setSmallIcon(PythonService.mService.getApplicationInfo().icon)
            
            # ID must be > 0
            PythonService.mService.startForeground(1001, notification_builder.build())
            PythonService.mService.setAutoRestartService(True)
            print("Foreground Service Notification Started")
    except Exception as e:
        print(f"Failed to start foreground notification: {e}")
    
    while True:
        try:
            db_path = get_current_db_path()
            if db_path and os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                # Use UTC strictly to avoid timezone issues
                now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
                
                cur.execute("SELECT id FROM tasks WHERE notified=0 AND status='open' AND due_iso <= ?", (now_utc,))
                due_tasks = cur.fetchall()
                
                for task_id in due_tasks:
                    try:
                        notification.notify(
                            title="RemindMe ⏰",
                            message="You have a task due right now!",
                            app_name="RemindMe",
                            timeout=10
                        )
                        cur.execute("UPDATE tasks SET notified=1 WHERE id=?", (task_id[0],))
                    except Exception as e:
                        print(f"Service Notification Error: {e}")
                
                conn.commit()
                conn.close()
        except Exception as e:
            print(f"Service Error: {e}")
            
        time.sleep(POLL_INTERVAL)

if __name__ == '__main__':
    run_service()
