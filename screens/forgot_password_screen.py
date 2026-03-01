from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivy.uix.widget import Widget
from kivymd.uix.card import MDCard
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.metrics import dp
from kivy.app import App
from backend.storage import get_email_by_username, save_last_user, resolve_user_case_insensitive
import threading
from kivy.clock import Clock

class ForgotPasswordScreen(MDScreen):
    def on_enter(self):
        self.clear_widgets()
        self.app = App.get_running_app()
        self.dialog = None
        
        # Main Layout
        root = MDFloatLayout()
        
        # 1. Top Header Background (Matching Login)
        header_bg = MDCard(
            size_hint=(1, 0.35),
            pos_hint={"top": 1},
            radius=[0, 0, 0, 80],
            md_bg_color=(0.2, 0.6, 1, 1), # Light Blue
            elevation=0
        )
        self.add_widget(header_bg)
        
        # Header Text
        self.add_widget(MDLabel(
            text="Recovery",
            font_style="H3",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.88},
            halign="center",
            bold=True
        ))
        
        self.add_widget(MDLabel(
            text="Enter your username to reset",
            font_style="Subtitle1",
            theme_text_color="Custom",
            text_color=(0.9, 0.9, 0.9, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.82},
            halign="center"
        ))
        
        # Content Card
        self.card = MDCard(
            size_hint=(0.85, None),
            height=dp(250),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            radius=[20],
            elevation=2,
            padding=dp(20),
            orientation='vertical',
            md_bg_color=App.get_running_app().theme_cls.bg_normal
        )
        
        # Input
        self.username_input = MDTextField(
            hint_text="Username",
            mode="rectangle",
            icon_right="account",
        )
        self.card.add_widget(self.username_input)
        
        # Buttons
        # Buttons
        self.send_btn = MDRaisedButton(
            text="SEND RESET LINK",
            font_size="16sp",
            size_hint_x=1,
            height=dp(50),
            on_release=self.send_reset,
            md_bg_color=(0.2, 0.6, 1, 1)
        )
        self.card.add_widget(self.send_btn)
        
        self.card.add_widget(MDFlatButton(
            text="Back to Login",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=(0.5, 0.5, 0.5, 1),
            on_release=self.go_login
        ))
        
        self.add_widget(self.card)

    def send_reset(self, instance):
        username_input = self.username_input.text.strip()
        if not username_input:
            self.username_input.error = True
            return

        # 1. Disable button to prevent double-click (Expired Token Issue)
        self.send_btn.disabled = True
        
        # 2. Show Loading State
        self.show_dialog("Processing", "Locating account and sending request...")

        # 3. Run logic in Thread
        t = threading.Thread(target=self._reset_logic_thread, args=(username_input,))
        t.start()
        
    def _reset_logic_thread(self, username_input):
        from backend.auth_service import get_username_data
        from backend.firebase_service import reset_password_email
        
        cloud_data, fetch_error = get_username_data(username_input)
        email = None
        if cloud_data:
            email = cloud_data.get("email")
            
        print("Reset email:", email)
        
        if not email:
            Clock.schedule_once(lambda dt: self._enable_btn())
            Clock.schedule_once(lambda dt: self.update_dialog("Username Not Found", "We could not find an email linked to this username in our database."))
            return

        data, error = reset_password_email(email)
        
        if error:
             print("Firebase reset error:", error)
             Clock.schedule_once(lambda dt: self._enable_btn())
             Clock.schedule_once(lambda dt: self.update_dialog("Error", "Could not send email. Please check internet connection."))
        else:
             from backend.storage import save_last_user
             save_last_user(username_input, self.app.storage_path)
             Clock.schedule_once(lambda dt: self.update_dialog("Success", "A password reset link has been successfully sent to your registered email.", self.go_login))

    def _enable_btn(self):
        self.send_btn.disabled = False

    def show_dialog(self, title, text, on_dismiss=None):
        if self.dialog:
            self.dialog.dismiss()
            
        self.dialog = MDDialog(
            title=title,
            text=text,
            # We don't add buttons initially if it's "Processing", but MDDialog needs buttons or auto_dismiss=True
            # Let's make it persistent for "Processing"
            buttons=[],
            auto_dismiss=False
        )
        self.dialog.open()

    def update_dialog(self, title, text, on_dismiss=None):
        if self.dialog:
             self.dialog.dismiss()
             
        # Create new dialog with buttons
        btns = [MDFlatButton(text="OK", on_release=lambda x: self.close_dialog(on_dismiss))]
        
        self.dialog = MDDialog(
            title=title,
            text=text,
            buttons=btns,
            auto_dismiss=True
        )
        self.dialog.open()

    def close_dialog(self, callback):
        if self.dialog:
            self.dialog.dismiss()
        if callback:
            callback()

    def go_login(self, *args):
        self.app.switch_screen("login")
