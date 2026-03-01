import sys
import os
import logging
import traceback
import ctypes
# 🔴 CRITICAL: Fix for PyInstaller windowed mode (no stdout/stderr)
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

# 🔴 CRITICAL: SET Crash Logger immediately
log_file = os.path.join(os.getcwd(), "crash_debug.log")

def excepthook(exc_type, exc_value, exc_traceback):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))

sys.excepthook = excepthook
# 🔴 CRITICAL: SET AppUserModelID for Windows Toast Notifications
# This must be done at the very beginning of the process.
if sys.platform == 'win32':
    try:
        AUMID = "RemindMe.App"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(AUMID)
        print(f"✅ AppUserModelID set to: {AUMID} (Enabled)")

        from kivy.config import Config
        from kivy.core.window import Window
        def resource_path(relative_path):
            if hasattr(sys, '_MEIPASS'):
                return os.path.join(sys._MEIPASS, relative_path)
            return os.path.abspath(relative_path)
            
        icon_override = resource_path("app.png")
        Config.set('kivy', 'window_icon', icon_override)
        Window.set_icon(icon_override)

        # Ensure Start Menu Shortcut exists with AUMID (Required for WinRT)
        def ensure_shortcut():
            try:
                import winshell
                from win32com.client import Dispatch
                
                app_data = os.environ.get('APPDATA')
                shortcut_path = os.path.join(app_data, 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'RemindMe.lnk')
                
                if not os.path.exists(shortcut_path):
                    print("Creating Start Menu shortcut for AUMID support...")
                    target = sys.executable 
                    # If running as python script, target is python.exe, which is fine for testing
                    # If running as EXE, target is the EXE path.
                    
                    shell = Dispatch('WScript.Shell')
                    shortcut = shell.CreateShortCut(shortcut_path)
                    shortcut.Targetpath = target
                    shortcut.WorkingDirectory = os.path.dirname(target)
                    shortcut.IconLocation = target
                    # This is the "secret sauce" for Windows Toasts
                    shortcut.Description = "RemindMe Application"
                    shortcut.Save()
                    
                    # Apply AUMID to the shortcut via powershell if needed or assume shell32 handles it
                    # Most modern methods use a specific COM property, but usually 
                    # SetCurrentProcessExplicitAppUserModelID handles the active process.
                    # Registration in Start Menu is primarily for the Action Center.
                    print(f"✅ Shortcut created at: {shortcut_path}")
            except Exception as e:
                print(f"⚠️ Shortcut creation failed: {e}")

        ensure_shortcut()
        # pass
    except Exception as e:
        print(f"❌ Failed to set AppUserModelID: {e}")

print("====================================")
print("RemindMe App - Version 2.0")
print("Phase: Notification Hardening & Architecture Enforcement")
print("====================================")

import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)

APP_VERSION = "2.1"

# Fix for "NoneType has no attribute 'write'" in windowed apps
class DummyStream:
    def write(self, *args, **kwargs): pass
    def flush(self, *args, **kwargs): pass

if sys.stdout is None: sys.stdout = DummyStream()
if sys.stderr is None: sys.stderr = DummyStream()

# Configure basic logging to stdout only for early startup
from kivy.logger import Logger
Logger.setLevel(logging.DEBUG)

from kivy.config import Config
# Only set window size if not on Android
try:
    from kivy.utils import platform
    if platform != 'android':
        Config.set('graphics', 'width', '360')
        Config.set('graphics', 'height', '640')
except ImportError:
    pass

# Base Kivy imports - these must work for the crash screen to show
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, NoTransition
from kivy.core.text import LabelBase
from kivy.core.window import Window

from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

# Global error capture
startup_error = None

# hazardous_imports
try:
    from kivymd.uix.floatlayout import MDFloatLayout
    from utils.notification_manager import NotificationManager
    from backend.scheduler import Scheduler
    from utils.helpers import get_asset_path, get_storage_path
    
    from screens.welcome_screen import WelcomeScreen
    from screens.login_screen import LoginScreen
    from screens.dashboard_screen import DashboardScreen
    from screens.create_task_screen import CreateTaskScreen
    from screens.analytics_screen import AnalyticsScreen
    from screens.calendar_month_screen import CalendarMonthScreen
    from screens.calendar_day_screen import CalendarDayScreen
    from screens.settings_screen import SettingsScreen
    from screens.audit_analytics_screen import AuditAnalyticsScreen
    from screens.ai_assistant_screen import AIAssistantScreen
    from screens.forgot_password_screen import ForgotPasswordScreen

    # Register Custom Fonts
    LabelBase.register(
        name="Montserrat",
        fn_regular=get_asset_path("assets/fonts/Montserrat/static/Montserrat-Regular.ttf"),
        fn_bold=get_asset_path("assets/fonts/Montserrat/static/Montserrat-Bold.ttf"),
        fn_italic=get_asset_path("assets/fonts/Montserrat/static/Montserrat-Italic.ttf"),
        fn_bolditalic=get_asset_path("assets/fonts/Montserrat/static/Montserrat-BoldItalic.ttf"),
    )

except Exception:
    startup_error = traceback.format_exc()
    logging.error(f"STARTUP ERROR: {startup_error}")


class ReminderApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scheduler = None
        
        # 🔴 CRITICAL: Force MDApp to use RemindMe logo instead of Kivy defaults
        try:
            from utils.helpers import get_asset_path
            self.icon = get_asset_path("app.png")
        except:
            pass
        
    def build(self):
        # 1. Check for startup errors first
        if startup_error:
            return self.build_crash_screen(startup_error)

        # 2. Normal Build
        try:
            # Set Mobile Window Size (Portrait) for desktop testing
            if platform != 'android':
                Window.size = (360, 640)
            
            self.title = "RemindMe"
            # Window icon is globally initialized at the top level of the script
            
            self.storage_path = get_storage_path()
            
            # Setup file logging in writable storage_path
            log_file = os.path.join(self.storage_path, 'app_debug.log')
            fh = logging.FileHandler(log_file, encoding='utf-8')
            fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logging.getLogger().addHandler(fh)
            logging.info(f"Logging initialized at {log_file}")
            
            # DEPLOYMENT FIX: Extract bundled databases/files to writable storage
            try:
                from utils.helpers import copy_bundled_data
                copy_bundled_data(self.storage_path)
            except Exception as e:
                logging.error(f"Bundle copy failed: {e}")
                
            self.db_path = None
            self.derived_key = None 
            self.current_user = None
            self.current_uid = None
            self.scheduler = None

            # Initialize Notification Manager
            self.notification_manager = NotificationManager()

            self.theme_cls.primary_palette = "Blue"
            
            # Late import to depend on storage path
            from backend.storage import get_theme_preference
            self.theme_cls.theme_style = get_theme_preference(self.storage_path)
            self.update_theme_colors()
            
            # Override Typography
            self.theme_cls.font_styles.update({
                "H1": ["Montserrat", 96, False, -1.5],
                "H2": ["Montserrat", 60, False, -0.5],
                "H3": ["Montserrat", 48, False, 0],
                "H4": ["Montserrat", 34, False, 0.25],
                "H5": ["Montserrat", 24, False, 0],
                "H6": ["Montserrat", 20, False, 0.15],
                "Subtitle1": ["Roboto", 16, False, 0.15],
                "Subtitle2": ["Roboto", 14, True, 0.1],
                "Body1": ["Roboto", 16, False, 0.5],
                "Body2": ["Roboto", 14, False, 0.25],
                "Button": ["Roboto", 14, True, 1.25],
                "Caption": ["Roboto", 12, False, 0.4],
                "Overline": ["Roboto", 10, True, 1.5],
            })
            
            # Screen Manager
            self.sm = ScreenManager(transition=NoTransition())
            self.sm.app_ref = self
            
            self.sm.add_widget(WelcomeScreen(name="welcome"))
            self.sm.add_widget(LoginScreen(name="login"))
            self.sm.add_widget(DashboardScreen(name="dashboard"))
            self.sm.add_widget(CreateTaskScreen(name="create_task"))
            self.sm.add_widget(AnalyticsScreen(name="analytics"))
            self.sm.add_widget(CalendarMonthScreen(name="calendar_month"))
            self.sm.add_widget(CalendarDayScreen(name="calendar_day"))
            self.sm.add_widget(SettingsScreen(name="settings"))
            self.sm.add_widget(AuditAnalyticsScreen(name="audit"))
            self.sm.add_widget(AIAssistantScreen(name="ai"))
            self.sm.add_widget(ForgotPasswordScreen(name="forgot_password"))
            
            # Determine start screen
            self.sm.current = "welcome"
            
            return self.sm
            
        except Exception:
            # Catch errors during build()
            err = traceback.format_exc()
            return self.build_crash_screen(err)

    def switch_screen(self, screen_name):
        """Safely switch screens with error handling."""
        try:
            if self.root and self.root.has_screen(screen_name):
                self.root.current = screen_name
            else:
                print(f"Navigation Error: Screen '{screen_name}' not found!")
        except Exception as e:
            print(f"Navigation System Failure: {e}")
            traceback.print_exc()

    def on_start(self):
        """Perform startup tasks like permission requests on Android."""
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.POST_NOTIFICATIONS,
                    Permission.WAKE_LOCK,
                    Permission.RECEIVE_BOOT_COMPLETED,
                    Permission.VIBRATE
                ])
                # Explicitly init channel for Android 8+
                self.init_android_notifications()
            except ImportError:
                print("Android permissions module not available (testing on desktop?)")

    def init_android_notifications(self):
        """Ensure notification channel exists for Android 8+."""
        try:
            from jnius import autoclass
            Context = autoclass('android.content.Context')
            NotificationManager = autoclass('android.app.NotificationManager')
            NotificationChannel = autoclass('android.app.NotificationChannel')
            
            app_context = autoclass('org.kivy.android.PythonActivity').mActivity
            notification_service = app_context.getSystemService(Context.NOTIFICATION_SERVICE)
            
            channel_id = 'remindme_alerts'
            channel_name = 'Task Reminders'
            # IMPORTANCE_HIGH = 4
            channel = NotificationChannel(channel_id, channel_name, 4)
            channel.setDescription('Alerts for your scheduled tasks')
            
            notification_service.createNotificationChannel(channel)
            print("Android Notification Channel Created")
        except Exception as e:
            print(f"Android Channel Init Failed: {e}")

    def build_crash_screen(self, error_msg):
        """Displays a simple screen with the error message."""
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        lbl = Label(
            text="APP CRASHED!",
            font_size='24sp',
            color=(1, 0, 0, 1),
            size_hint_y=None,
            height=50,
            bold=True
        )
        
        # Scrollable text input for the error
        txt = TextInput(
            text=error_msg,
            readonly=True,
            foreground_color=(1, 0, 0, 1),
            background_color=(0.1, 0.1, 0.1, 1),
            font_size='12sp'
        )
        
        layout.add_widget(lbl)
        layout.add_widget(txt)
        return layout

    def start_scheduler(self):
        """Called after login when DB path and key are available."""
        if getattr(self, 'scheduler_started', False):
            return
        if not self.db_path or not self.derived_key:
            print("Scheduler: Cannot start — db_path or derived_key missing.")
            return
            
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY,
                    ciphertext TEXT,
                    nonce TEXT,
                    due_iso TEXT,
                    priority INTEGER,
                    notified INTEGER,
                    created_iso TEXT,
                    completed_iso TEXT,
                    category TEXT,
                    sound TEXT,
                    description TEXT,
                    status TEXT,
                    notification_status TEXT,
                    is_overdue INTEGER
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"CRITICAL: Schema validation failed. Halting Scheduler: {e}")
            return
            
        from backend.scheduler import Scheduler
        from kivy.clock import Clock
        
        def on_notify_callback(task_id, title):
            """Called from scheduler thread when a task is due."""
            # Schedule UI work on main Kivy thread
            Clock.schedule_once(lambda dt: self.on_notification(task_id, title), 0)
        
        tts_enabled = getattr(self, 'tts_enabled', False)
        self.scheduler = Scheduler(
            db_path=self.db_path,
            key=self.derived_key,
            on_notify_callback=on_notify_callback,
            tts_enabled=tts_enabled
        )
        self.scheduler.start()
        self.scheduler_started = True
        print("Scheduler started successfully.")

    def stop_scheduler(self):
        # New scheduler is a daemon thread, terminates with app.
        pass

    def on_notification(self, task_id, title):
        self.notification_manager.show_alert("Reminder", f"Task Due: {title}", task_id)
        # Force UI refresh in dashboard to show 'notified' (RED) state immediately
        try:
            if self.root.has_screen('dashboard'):
                self.root.get_screen('dashboard').refresh_tasks(None)
            if self.root.has_screen('calendar_day'):
                self.root.get_screen('calendar_day').fetch_and_render_tasks()
        except Exception as e:
            logging.error(f"UI refresh on notification failed: {e}")

    def update_theme_colors(self):
        try:
            target_bg = self.theme_cls.bg_normal
            if hasattr(self, 'sm'):
                for screen in self.sm.screens:
                    if hasattr(screen, "md_bg_color"):
                        screen.md_bg_color = target_bg
        except Exception as e:
            print(f"Error updating theme colors: {e}")

    def on_stop(self):
        if hasattr(self, 'scheduler') and self.scheduler:
            self.stop_scheduler()

if __name__ == "__main__":
    from kivy.resources import resource_add_path
    
    # Fix Path for Android Bundle and PyInstaller
    if hasattr(sys, '_MEIPASS'):
        resource_add_path(os.path.join(sys._MEIPASS))
    
    # Ensure current dir is in resources
    resource_add_path(os.path.dirname(os.path.abspath(__file__)))
    try:
        resource_add_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets'))
    except:
        pass

    try:
        ReminderApp().run()
    except Exception as e:
        # This catch is for errors AFTER build() has returned, or main loop errors
        # We can't easily show UI here if the loop died, but we can try to print
        print(traceback.format_exc())