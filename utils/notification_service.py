"""
notification_service.py — Windows OS Toast Notifications
Uses winotify (no pkg_resources dependency) for Windows Action Center toasts.
Falls back to plyer if winotify is unavailable.
"""
import logging
import threading
import sys
import os
import platform

logger = logging.getLogger("NotificationService")

# Isolate Windows-specific imports
if platform.system() == "Windows":
    try:
        from winotify import Notification, audio
    except ImportError:
        Notification = None
else:
    Notification = None

def _resource_path(relative_path: str) -> str:
    """Get absolute path to a resource, works for dev and PyInstaller --onefile."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', relative_path)


def _set_app_user_model_id():
    """Set Windows AppUserModelID so toast groups correctly and logo shows."""
    if platform.system() != "Windows":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("RemindMe.App")
    except Exception as e:
        logger.debug(f"AppUserModelID: {e}")


def _fire_winotify_toast(title: str, message: str):
    """Fire a Windows native toast using winotify (works in Windows 10/11 Action Center)."""
    if not Notification:
        return False
        
    try:
        # Resolve logo path — logo.png must be an absolute path for winotify
        logo_path = _resource_path(os.path.join("assets", "logo.png"))
        logo_abs = os.path.abspath(logo_path)
        if not os.path.exists(logo_abs):
            logo_abs = None  # Use no icon if logo not found

        toast = Notification(
            app_id="RemindMe",
            title=title,
            msg=message,
            duration="long",          # stays in Action Center longer
            icon=logo_abs or "",
        )
        toast.set_audio(audio.Default, loop=False)
        toast.show()
        logger.info(f"winotify toast shown: {title}")
        return True
    except Exception as e:
        logger.warning(f"winotify failed: {e}")
        return False


def _fire_plyer_toast(title: str, message: str):
    """Fallback: fire a notification via plyer."""
    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            timeout=10,
            app_name="RemindMe"
        )
        logger.info(f"plyer notification sent: {title}")
        return True
    except Exception as e:
        logger.error(f"plyer also failed: {e}")
        return False


def _toast_worker(title: str, message: str):
    """Background worker: try winotify, fall back to plyer."""
    _set_app_user_model_id()
    if not _fire_winotify_toast(title, message):
        _fire_plyer_toast(title, message)


def send_os_notification(title: str, message: str):
    """
    Fire a Windows system-level toast notification in a daemon thread.
    Non-blocking — never freezes the UI thread.
    Works even when the app is minimized.
    """
    t = threading.Thread(target=_toast_worker, args=(title, message), daemon=True)
    t.start()


def start_scheduler(get_tasks_function, update_task_callback=None):
    """Legacy simple scheduler wrapper (used by utils.notification_service callers)."""
    import time
    from datetime import datetime

    def worker():
        while True:
            now = datetime.now()
            try:
                tasks = get_tasks_function()
                for task in tasks:
                    if not task.get("notified", False) and task.get("datetime") <= now:
                        send_os_notification("RemindMe", task.get("title", "Task Reminder"))
                        task["notified"] = True
                        if update_task_callback:
                            update_task_callback(task)
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            time.sleep(30)

    threading.Thread(target=worker, daemon=True).start()
