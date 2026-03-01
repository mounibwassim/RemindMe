from kivy.config import Config
# Only set window size if not on Android (let Android handle its own size/density mostly, 
# though setting a default reference is okay, avoiding strict 'resizable' is good)
try:
    from kivy.utils import platform
    if platform != 'android':
        Config.set('graphics', 'width', '360')
        Config.set('graphics', 'height', '640')
except ImportError:
    pass

from kivymd.app import MDApp
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.uix.screenmanager import ScreenManager, NoTransition
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.lang import Builder
import os
import sys

from utils.notification_manager import NotificationManager
from backend.scheduler import Scheduler
from utils.helpers import get_asset_path, get_storage_path

from screens.welcome_screen import WelcomeScreen
from screens.login_screen import LoginScreen
from screens.dashboard_screen import DashboardScreen
from screens.create_task_screen import CreateTaskScreen
from screens.analytics_screen import AnalyticsScreen
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

class ReminderApp(MDApp):
    def build(self):
        # Set Mobile Window Size (Portrait) for desktop testing
        if platform != 'android':
            Window.size = (360, 640)
        
        self.title = "RemindMe"
        self.icon = get_asset_path("assets/logo.png")
        
        self.storage_path = get_storage_path()
        self.db_path = None
        self.derived_key = None 
        self.scheduler = None

        # Initialize Notification Manager
        self.notification_manager = NotificationManager()

        self.theme_cls.primary_palette = "Blue"
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
        self.sm.add_widget(SettingsScreen(name="settings"))
        self.sm.add_widget(AuditAnalyticsScreen(name="audit_analytics"))
        self.sm.add_widget(AIAssistantScreen(name="ai_assistant"))
        self.sm.add_widget(ForgotPasswordScreen(name="forgot_password"))
        
        # Determine start screen
        self.sm.current = "welcome"
        
        return self.sm

    def start_scheduler(self):
        """Called after login when DB path and key are available."""
        if self.scheduler:
             self.scheduler.stop_scheduler()
             
        self.scheduler = Scheduler(
            self.db_path, 
            self.derived_key,
            on_notify_callback=self.on_notification
        )
        self.scheduler.start()

    def stop_scheduler(self):
        if self.scheduler:
            self.scheduler.stop_scheduler()
            self.scheduler = None

    def on_notification(self, task_id, title):
        self.notification_manager.show_alert("Reminder", f"Task Due: {title}", task_id)

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
        self.stop_scheduler()

if __name__ == "__main__":
    import logging
    import traceback
    from kivy.resources import resource_add_path

    # Fix Path for Android Bundle and PyInstaller
    if hasattr(sys, '_MEIPASS'):
        resource_add_path(os.path.join(sys._MEIPASS))
    
    # Ensure current dir is in resources
    resource_add_path(os.path.dirname(os.path.abspath(__file__)))
    resource_add_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets'))

    try:
        ReminderApp().run()
    except Exception as e:
        error_msg = traceback.format_exc()
        logging.error(f"CRASH: {error_msg}")
        try:
            from kivy.utils import platform
            if platform == 'android':
                from android.storage import app_storage_path
                log_dir = app_storage_path()
            else:
                log_dir = os.path.dirname(os.path.abspath(__file__))
            log_path = os.path.join(log_dir, 'crash_log.txt')
            with open(log_path, 'w') as f:
                f.write(error_msg)
            print(f"Crash log written to {log_path}")
        except:
            print("Failed to write crash log.")
            print(error_msg)