"""
notification_manager.py
Handles OS toast notifications + in-app alert dialog.
All notification attempts are logged with full traceback to:
  %USERPROFILE%\\app_debug.log   (Windows)
  or stdout (other platforms)
"""

import os
import logging
import traceback
from kivy.utils import platform

# ── Logger wired to %USERPROFILE%\app_debug.log ─────────────────────────────
def _get_notif_logger():
    log = logging.getLogger("NotificationManager")
    if log.handlers:
        return log
    log.setLevel(logging.DEBUG)
    fmt = logging.Formatter("[%(asctime)s][%(levelname)s][NotificationManager] %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")
    # File handler — always to app_debug.log
    try:
        log_path = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")),
                                "app_debug.log")
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        log.addHandler(fh)
    except Exception:
        pass
    # Stream handler (console/logcat)
    sh = logging.StreamHandler()
    sh.setLevel(logging.DEBUG)
    sh.setFormatter(fmt)
    log.addHandler(sh)
    return log

logger = _get_notif_logger()

# ── Plyer (Android + fallback) ───────────────────────────────────────────────
plyer_notification = None
if platform != 'win':
    try:
        from plyer import notification as plyer_notification
        logger.debug("plyer imported OK")
    except Exception as e:
        logger.warning(f"plyer import failed: {e}")

# ── win10toast Toast (Windows) ───────────────────────────────────────────────
_win_notifications_available = False
if platform == 'win':
    try:
        from win10toast import ToastNotifier
        _win_notifications_available = True
        logger.debug("win10toast imported OK")
    except Exception as e:
        logger.warning(f"win10toast import failed (Windows notifications disabled): {e}")

# ── Public API ───────────────────────────────────────────────────────────────
class NotificationManager:
    def __init__(self):
        self.dialog = None

    def show_alert(self, title, message, task_id=None):
        """
        Entry point called by the scheduler callback (always on main thread via
        Clock.schedule_once in main.py).
        Fires OS notification + in-app dialog.
        """
        logger.info(f"show_alert called | title={title!r} | platform={platform!r} | task_id={task_id}")

        from kivy.clock import Clock
        # OS notification — schedule even if already on main thread to be safe
        Clock.schedule_once(lambda dt: self._fire_os_notify(title, message), 0)
        # In-app dialog
        Clock.schedule_once(lambda dt: self.show_dialog(title, message, task_id), 0)

    # ── OS notification dispatch ─────────────────────────────────────────────

    def _fire_os_notify(self, title, message):
        logger.info(f"_fire_os_notify | platform={platform!r} | title={title!r}")
        try:
            if platform == 'win':
                self._notify_windows(title, message)
            elif platform == 'android':
                self._notify_android(title, message)
            else:
                self._notify_plyer(title, message)
        except Exception:
            logger.error(f"_fire_os_notify unhandled exception:\n{traceback.format_exc()}")

    def _notify_windows(self, title, message):
        """Primary path: Windows SDK (winrt). Fallback: plyer."""
        from kivy.clock import Clock
        # Enforce main thread execution for UI/Toast interactions
        Clock.schedule_once(lambda dt: self._do_notify_windows_native(title, message))

    def _do_notify_windows_native(self, title, message):
        logger.info(f"[_do_notify_windows_native] Entering | win10toast_available={_win_notifications_available}")
        if _win_notifications_available:
            try:
                import ctypes
                try:
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("RemindMe.App")
                except:
                    pass
                
                from win10toast import ToastNotifier
                import os
                import sys

                def notify_resource_path(relative_path):
                    if hasattr(sys, '_MEIPASS'):
                        return os.path.join(sys._MEIPASS, relative_path)
                    return os.path.abspath(relative_path)

                toaster = ToastNotifier()
                toaster.show_toast(
                    title,
                    message,
                    icon_path=notify_resource_path("app.ico"),
                    duration=5,
                    threaded=True
                )
                logger.info("✅ SUCCESS: win10toast native toast dispatched successfully")
                
            except Exception as e:
                logger.error(f"❌ win10toast FAILED: {e}\n{traceback.format_exc()}")
        else:
            logger.warning("win10toast not available — no OS notification will be shown on Windows")

    def _notify_android(self, title, message):
        """Android path: Native NotificationManager via pyjnius."""
        logger.info(f"[AndroidNotification] Attempting pyjnius dispatch | title={title!r} | channel=remindme_alerts")
        try:
            from jnius import autoclass
            Context = autoclass('android.content.Context')
            app_context = autoclass('org.kivy.android.PythonActivity').mActivity
            
            NotificationManager = autoclass('android.app.NotificationManager')
            notification_service = app_context.getSystemService(Context.NOTIFICATION_SERVICE)
            
            # Use appropriate Builder based on Android version
            try:
                NotificationCompatBuilder = autoclass('androidx.core.app.NotificationCompat$Builder')
            except Exception:
                NotificationCompatBuilder = autoclass('android.app.Notification$Builder')
                
            String = autoclass('java.lang.String')
            channel_id = String('remindme_alerts')
            
            builder = NotificationCompatBuilder(app_context, channel_id)
            builder.setContentTitle(String(title))
            builder.setContentText(String(message))
            
            # Resolve Icon
            try:
                appInfo = app_context.getApplicationInfo()
                builder.setSmallIcon(appInfo.icon)
            except Exception as ei:
                logger.error(f"[AndroidNotification] Icon extract err: {ei}")
                R_drawable = autoclass('android.R$drawable')
                builder.setSmallIcon(R_drawable.ic_dialog_info) # Fallback system icon

            builder.setPriority(4) # IMPORTANCE_HIGH
            builder.setAutoCancel(True)
            
            # Dispatch
            notification_service.notify(1001, builder.build())
            logger.info("[AndroidNotification] ✅ Native pyjnius notification dispatched successfully")
        except Exception as e:
            logger.error(f"[AndroidNotification] ❌ pyjnius dispatch FAILED:\n{traceback.format_exc()}")
            logger.info("[AndroidNotification] Attempting plyer fallback")
            if plyer_notification:
                try:
                    plyer_notification.notify(
                        title=title,
                        message=message,
                        app_name="RemindMe",
                        timeout=10
                    )
                    logger.info("[AndroidNotification] ✅ plyer fallback OK")
                except Exception as ef:
                    logger.error(f"[AndroidNotification] ❌ plyer fallback FAILED: {ef}")

    def _notify_plyer(self, title, message):
        """Generic plyer fallback (Linux/macOS + Windows fallback)."""
        logger.info("_notify_plyer fallback")
        if plyer_notification:
            try:
                plyer_notification.notify(
                    title=title,
                    message=message,
                    app_name="RemindMe",
                    timeout=10
                )
                logger.info("plyer fallback notification dispatched OK")
            except Exception:
                logger.error(f"plyer fallback FAILED:\n{traceback.format_exc()}")
        else:
            logger.error("plyer not available — no OS notification will be shown")

    # ── In-app dialog ────────────────────────────────────────────────────────

    def show_dialog(self, title, text, task_id=None):
        if hasattr(self, 'dialog') and self.dialog:
            try:
                self.dialog.dismiss()
            except Exception:
                pass

        def do_snooze(mins):
            try:
                from kivymd.app import MDApp
                app = MDApp.get_running_app()
                from backend.storage import snooze_task
                snooze_task(app.db_path, task_id, mins)
                self.dialog.dismiss()
                from kivymd.toast import toast
                toast(f"Task snoozed for {mins} minutes.")
                from kivy.clock import Clock
                def refresh_ui(dt):
                    try:
                        if app.root.has_screen('dashboard'):
                            app.root.get_screen('dashboard').refresh_tasks()
                        if app.root.has_screen('calendar_day'):
                            app.root.get_screen('calendar_day').fetch_and_render_tasks()
                    except Exception:
                        pass
                Clock.schedule_once(refresh_ui, 0.1)
            except Exception:
                logger.error(f"do_snooze failed:\n{traceback.format_exc()}")

        def do_dismiss():
            try:
                from kivymd.app import MDApp
                app = MDApp.get_running_app()
                from backend.storage import dismiss_notification
                dismiss_notification(app.db_path, task_id)
                self.dialog.dismiss()
                from kivymd.toast import toast
                toast("Task alert dismissed.")
                from kivy.clock import Clock
                def refresh_ui(dt):
                    try:
                        if app.root.has_screen('dashboard'):
                            app.root.get_screen('dashboard').refresh_tasks()
                        if app.root.has_screen('calendar_day'):
                            app.root.get_screen('calendar_day').fetch_and_render_tasks()
                    except Exception:
                        pass
                Clock.schedule_once(refresh_ui, 0.1)
            except Exception:
                logger.error(f"do_dismiss failed:\n{traceback.format_exc()}")

        try:
            from kivymd.uix.button import MDFlatButton, MDRaisedButton
            from kivymd.uix.boxlayout import MDBoxLayout
            from kivymd.uix.label import MDLabel
            from kivymd.uix.dialog import MDDialog
            from kivy.metrics import dp

            content = MDBoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None)
            content.bind(minimum_height=content.setter('height'))
            content.add_widget(MDLabel(
                text=text, theme_text_color="Secondary",
                size_hint_y=None, height=dp(40)
            ))

            buttons = [MDFlatButton(
                text="CLOSE",
                theme_text_color="Primary",
                on_release=lambda x: self.dialog.dismiss()
            )]

            if task_id:
                snooze_row = MDBoxLayout(orientation="horizontal", spacing=dp(10),
                                        size_hint_y=None, height=dp(40))
                snooze_row.add_widget(MDFlatButton(
                    text="SNOOZE 5M", on_release=lambda x: do_snooze(5), size_hint_x=0.5))
                snooze_row.add_widget(MDFlatButton(
                    text="SNOOZE 10M", on_release=lambda x: do_snooze(10), size_hint_x=0.5))
                content.add_widget(snooze_row)
                content.add_widget(MDRaisedButton(
                    text="DISMISS",
                    md_bg_color=(0.9, 0.1, 0.1, 1),
                    on_release=lambda x: do_dismiss(),
                    size_hint_x=1,
                    size_hint_y=None,
                    height=dp(40)
                ))

            self.dialog = MDDialog(
                title=title,
                type="custom",
                content_cls=content,
                buttons=buttons
            )
            self.dialog.open()
            logger.info("In-app dialog opened OK")
        except Exception:
            logger.error(f"show_dialog FAILED:\n{traceback.format_exc()}")
