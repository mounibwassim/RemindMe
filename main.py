# 1. TOP-LEVEL GLOBAL CONFIG (MUST BE FIRST)
from kivy.config import Config
Config.set('graphics', 'multisamples', '0')
Config.set('graphics', 'vsync', '0')
Config.set('kivy', 'log_level', 'warning')
Config.set('kivy', 'log_enable', '0')

import sys
import os
import logging
import traceback
import ctypes
from datetime import datetime
from kivy.utils import platform

# 2. WINDOWS-ONLY INITIALIZATION (Encapsulated)
def setup_windows_env():
    if sys.platform != 'win32':
        return
    try:
        # AUMID for Toasts
        AUMID = "RemindMe.App"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(AUMID)
        
        # Shortcut creation
        import winshell
        from win32com.client import Dispatch
        app_data = os.environ.get('APPDATA')
        shortcut_path = os.path.join(app_data, 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'RemindMe.lnk')
        
        if not os.path.exists(shortcut_path):
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = sys.executable 
            shortcut.WorkingDirectory = os.path.dirname(sys.executable)
            shortcut.IconLocation = sys.executable
            shortcut.Description = "RemindMe Application"
            shortcut.Save()
    except Exception as e:
        print(f"Windows init notice: {e}")

setup_windows_env()

# 3. BASE IMPORTS (No UI Widgets yet)
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, NoTransition
from kivy.core.text import LabelBase
from kivy.lang import Builder

# Global error capture
startup_error = None

# 4. CUSTOM FONT REGISTRATION (Safe scope)
def register_fonts():
    try:
        from utils.helpers import get_asset_path
        LabelBase.register(
            name="Montserrat",
            fn_regular=get_asset_path("assets/fonts/Montserrat/static/Montserrat-Regular.ttf"),
            fn_bold=get_asset_path("assets/fonts/Montserrat/static/Montserrat-Bold.ttf"),
            fn_italic=get_asset_path("assets/fonts/Montserrat/static/Montserrat-Italic.ttf"),
            fn_bolditalic=get_asset_path("assets/fonts/Montserrat/static/Montserrat-BoldItalic.ttf"),
        )
    except Exception as e:
        logging.error(f"Font registration failed: {e}")

register_fonts()


class ReminderApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scheduler = None
        
        # 🔴 CRITICAL: Force MDApp to use RemindMe logo instead of Kivy defaults
        try:
            from utils.helpers import get_asset_path
            icon_path = get_asset_path("assets/logo.png")
            if os.path.exists(icon_path):
                self.icon = icon_path
        except:
            pass
        
    def build(self):
        # 1. Check for startup errors
        if startup_error:
            return self.build_crash_screen(startup_error)

        # 2. Late Imports (Lazy Loading to prevent Adreno crash)
        try:
            from utils.helpers import get_storage_path, copy_bundled_data, get_asset_path
            from utils.notification_manager import NotificationManager
            from kivy.core.window import Window
            
            # 3. Setup Window
            if platform != 'android':
                Window.size = (360, 640)
            self.title = "RemindMe"
            
            # 4. Storage & Logging
            self.storage_path = get_storage_path()
            log_file = os.path.join(self.storage_path, 'app_debug.log')
            fh = logging.FileHandler(log_file, encoding='utf-8')
            fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logging.getLogger().addHandler(fh)
            
            # 5. Data Extraction
            copy_bundled_data(self.storage_path)
            
            # 6. Initialize Components
            self.notification_manager = NotificationManager()
            
            # 7. Lazy Load Screens
            self.load_screens_lazy()
            
            # 8. Theme Configuration
            from backend.storage import get_theme_preference
            self.theme_cls.primary_palette = "Blue"
            self.theme_cls.theme_style = get_theme_preference(self.storage_path)
            self.update_theme_colors()
            self.setup_typography()
            
            # 9. Main Navigation
            self.root = ScreenManager(transition=NoTransition())
            # Add all screens to manager (Lazy loaded classes)
            self.root.add_widget(WelcomeScreen(name='welcome'))
            self.root.add_widget(LoginScreen(name='login'))
            self.root.add_widget(DashboardScreen(name='dashboard'))
            self.root.add_widget(CreateTaskScreen(name='create_task'))
            self.root.add_widget(AnalyticsScreen(name='analytics'))
            self.root.add_widget(CalendarMonthScreen(name='calendar_month'))
            self.root.add_widget(CalendarDayScreen(name='calendar_day'))
            self.root.add_widget(SettingsScreen(name='settings'))
            self.root.add_widget(AuditAnalyticsScreen(name='audit'))
            self.root.add_widget(AIAssistantScreen(name='ai'))
            self.root.add_widget(ForgotPasswordScreen(name='forgot_password'))

            self.root.current = 'welcome'
            return self.root

        except Exception as e:
            logging.error(f"BUILD ERROR: {traceback.format_exc()}")
            return self.build_crash_screen(traceback.format_exc())

    def load_screens_lazy(self):
        """Import screens only when build() is called."""
        global WelcomeScreen, LoginScreen, DashboardScreen, CreateTaskScreen
        global AnalyticsScreen, CalendarMonthScreen, CalendarDayScreen
        global SettingsScreen, AuditAnalyticsScreen, AIAssistantScreen, ForgotPasswordScreen
        
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

    def setup_typography(self):
        """Configure font styles safely."""
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
            "Overline": ["Roboto", 10, False, 1.5],
        })

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
                from android.permissions import request_permissions # type: ignore
                request_permissions([
                    'android.permission.POST_NOTIFICATIONS',
                    'android.permission.WAKE_LOCK',
                    'android.permission.RECEIVE_BOOT_COMPLETED',
                    'android.permission.VIBRATE',
                    'android.permission.SCHEDULE_EXACT_ALARM',
                    'android.permission.FOREGROUND_SERVICE'
                ])
                # Explicitly init channel for Android 8+
                self.init_android_notifications()
                
                # Check and Request Exact Alarm Permission (Android 13+)
                self.check_exact_alarm_permission()
                
                # Start Foreground Service for logic/scheduling
                try:
                    from jnius import autoclass
                    PythonService = autoclass('org.kivy.android.PythonService')
                    Intent = autoclass('android.content.Intent')
                    mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
                    
                    service_intent = Intent(mActivity, PythonService)
                    mActivity.startForegroundService(service_intent)
                    print("Android Foreground Service Started")
                except Exception as e:
                    print(f"Failed to start Android service: {e}")
                    
            except ImportError:
                print("Android permissions/jnius module not available (testing on desktop?)")

    def check_exact_alarm_permission(self):
        """Checks if the app has permission to schedule exact alarms (Android 13+)."""
        try:
            from jnius import autoclass # type: ignore
            VERSION = autoclass('android.os.Build$VERSION')
            
            if VERSION.SDK_INT >= 33: # Android 13
                AlarmManager = autoclass('android.app.AlarmManager')
                Context = autoclass('android.content.Context')
                Settings = autoclass('android.provider.Settings')
                Uri = autoclass('android.net.Uri')
                Intent = autoclass('android.content.Intent')
                mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
                
                alarm_manager = mActivity.getSystemService(Context.ALARM_SERVICE)
                if not alarm_manager.canScheduleExactAlarms():
                    print("Requesting Exact Alarm Permission...")
                    intent = Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM)
                    intent.setData(Uri.parse(f"package:{mActivity.getPackageName()}"))
                    mActivity.startActivity(intent)
        except Exception as e:
            print(f"Exact Alarm Check Failed: {e}")


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
        # 1. In-app notification (dashboard banner)
        self.notification_manager.show_alert("Reminder", f"Task Due: {title}", task_id)

        # 2. Windows OS-level toast notification (Action Center) — fires in daemon thread
        try:
            from utils.notification_service import send_os_notification
            send_os_notification("RemindMe ⏰", title)
        except Exception as e:
            logging.error(f"OS notification failed: {e}")

        # 3. Force UI refresh
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
            if hasattr(self, 'root'):
                for screen in self.root.screens:
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