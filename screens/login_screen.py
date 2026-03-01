from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivy.clock import mainthread
from kivy.metrics import dp
from kivy.app import App
from kivy.uix.widget import Widget

from backend.storage import ensure_account, load_accounts_meta, get_last_user, save_last_user, get_email_by_username, resolve_user_case_insensitive
from backend.audit import write_audit

class LoginScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        self.menu = None
        self.mode = "login" # Initialize mode to prevent AttributeError

    def on_enter(self):
        self.app = App.get_running_app()
        self.clear_widgets()
        
        # Main Layout (White Background)
        from kivymd.uix.floatlayout import MDFloatLayout
        from kivymd.uix.card import MDCard
        
        # 1. Top Blue "Wave" Background
        header_bg = MDCard(
            size_hint=(1, 0.35),
            pos_hint={"top": 1},
            radius=[0, 0, 0, 80],
            md_bg_color=(0.2, 0.6, 1, 1), # Light Blue
            elevation=0
        )
        self.add_widget(header_bg)
        
        # Header Text (Welcome!)
        self.add_widget(MDLabel(
            text="RemindMe",
            font_style="H3",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.92}, # Moved UP significantly
            halign="center",
            bold=True
        ))
        
        self.add_widget(MDLabel(
            text="Sign in to continue",
            font_style="Subtitle1",
            theme_text_color="Custom",
            text_color=(0.9, 0.9, 0.9, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.86}, # Moved UP to be clearly visible
            halign="center"
        ))
        
        # Content Card
        self.card = MDCard(
            orientation="vertical",
            size_hint=(0.85, None),
            height=dp(400),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            radius=[20],
            elevation=1,
            padding=dp(20),
            md_bg_color=App.get_running_app().theme_cls.bg_normal
        )
        
        last_user = get_last_user(App.get_running_app().storage_path)
        
        # Username Field
        self.username_field = MDTextField(
            hint_text="Username",
            text=last_user if "@" not in last_user else "",
            mode="rectangle",
            icon_right="account",
            write_tab=False
        )
        self.card.add_widget(self.username_field)
        
        # Email (Hidden by default)
        self.email_field = MDTextField(
            hint_text="Email",
            mode="rectangle",
            icon_right="email",
            opacity=0,
            size_hint_y=None,
            height=0,
            disabled=True
        )
        self.card.add_widget(self.email_field)
        
        # Passphrase
        self.passphrase = MDTextField(
            hint_text="Password",
            password=True,
            mode="rectangle",
            icon_right="eye-off",
            write_tab=False
        )
        self.passphrase.bind(on_touch_down=self.toggle_password_visibility)
        self.card.add_widget(self.passphrase)

        # Forgot Password Link
        self.forgot_btn = MDFlatButton(
            text="Forgot Password?",
            font_size="12sp",
            theme_text_color="Custom",
            text_color=(0.5, 0.5, 0.5, 1),
            pos_hint={"right": 1},
            on_release=lambda x: setattr(self.manager, 'current', 'forgot_password')
        )
        self.card.add_widget(self.forgot_btn)
        
        # Buttons
        self.card.add_widget(Widget(size_hint_y=None, height=dp(10)))
        
        self.login_btn = MDRaisedButton(
            text="LOG IN",
            font_size="18sp",
            size_hint_x=1,
            height=dp(50),
            on_release=self.on_login,
            md_bg_color=(0.2, 0.6, 1, 1)
        )
        self.card.add_widget(self.login_btn)
        
        self.create_btn = MDFlatButton(
            text="Create New Account",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=(0.5, 0.5, 0.5, 1),
            on_release=self.toggle_mode
        )
        self.card.add_widget(self.create_btn)
        
        self.add_widget(self.card)

        # Always start empty
        if hasattr(self, 'username_field'):
            self.username_field.text = ""
        if hasattr(self, 'passphrase'):
            self.passphrase.text = ""
        if hasattr(self, 'email_field'):
            self.email_field.text = ""
        
        self.mode = "login"
        if hasattr(self, 'login_btn'):
            self.login_btn.text = "LOG IN"
        if hasattr(self, 'create_btn'):
            self.create_btn.text = "Create New Account"
        if hasattr(self, 'email_field'):
            self.email_field.opacity = 0
            self.email_field.height = 0
            self.email_field.disabled = True
            if hasattr(self.email_field, 'size_hint_y'):
                self.email_field.size_hint_y = None
        if hasattr(self, 'forgot_btn'):
            self.forgot_btn.opacity = 1
            self.forgot_btn.disabled = False

    def toggle_password_visibility(self, instance, touch):
        if instance.collide_point(*touch.pos):
            if touch.x > instance.right - dp(40):
                instance.password = not instance.password
                instance.icon_right = "eye" if not instance.password else "eye-off"
                return True
        return False

    def toggle_mode(self, instance):
        if self.mode == "login":
            self.mode = "register"
            self.login_btn.text = "REGISTER"
            self.create_btn.text = "Back to Login"
            
            # Show Email
            self.email_field.opacity = 1
            self.email_field.height = dp(60) # Standard height
            self.email_field.disabled = False
            self.email_field.size_hint_y = None
            
            # Hide Forgot Password
            self.forgot_btn.opacity = 0
            self.forgot_btn.disabled = True
            
        else:
            self.mode = "login"
            self.login_btn.text = "LOG IN"
            self.create_btn.text = "Create New Account"
            
            # Hide Email
            self.email_field.opacity = 0
            self.email_field.height = 0
            self.email_field.disabled = True
            self.email_field.size_hint_y = None
            
            # Show Forgot Password
            self.forgot_btn.opacity = 1
            self.forgot_btn.disabled = False

    @mainthread
    def on_login(self, instance):
        username = self.username_field.text.strip()
        pw = self.passphrase.text.strip()
        
        if not username or not pw:
            self.show_error("Please enter both username and password.")
            return

        from backend.firebase_service import (
            sign_in_with_email_password, 
            sign_up_with_email_password, 
            update_profile
        )
        
        from backend.auth_service import get_username_data, save_username_mapping
        from backend.storage import get_email_by_username, ensure_account, save_last_user
        
        print(f"DEBUG: Attempting {self.mode} for user: {username}")
        
        try:
            if self.mode == "register":
                email = self.email_field.text.strip()
                if not email:
                    self.show_error("Email address is required for registration.")
                    return

                # 1. Check if Username exists in Cloud Mapping first
                username_data, _ = get_username_data(username)
                if username_data:
                    self.show_error("Username is already taken.")
                    return

                # 2. Register with Firebase
                data, error = sign_up_with_email_password(email, pw)
                
                if error:
                    if "EMAIL_EXISTS" in error:
                        print("DEBUG: Email exists. Attempting ownership verification...")
                        data, heal_err = sign_in_with_email_password(email, pw)
                        if heal_err:
                            self.show_error("Email already registered with a different password.")
                            return
                    else:
                        print(f"DEBUG: Firebase registration error: {error}")
                        self.show_error(self.map_error(error))
                        return
                
                if not data or "localId" not in data:
                    print(f"DEBUG: Invalid Firebase registration response: {data}")
                    self.show_error("Registration failed. Please try again.")
                    return
                
                uid = data.get("localId")
                id_token = data.get("idToken")
                
                # 3. Setup Local encryption
                dek, db_path, metadata = ensure_account(username, pw, create_if_missing=True, path=self.app.storage_path, email=email)
                
                # 4. Store Mapping
                mapping_ok, m_error = save_username_mapping(username, email, uid, metadata=metadata)
                if not mapping_ok:
                    print(f"DEBUG: Cloud mapping failed: {m_error}")
                    self.show_error("Failed to sync account to cloud.")
                    return

                update_profile(id_token, username)
                write_audit(db_path, 0, "REGISTER", "New Account Created", user_uid=uid)
            
            else:
                # Login Mode
                cloud_data, fetch_error = get_username_data(username)
                
                if fetch_error or not cloud_data:
                    print(f"DEBUG: User lookup failed: {fetch_error}")
                    self.show_error("Incorrect username or password.")
                    return
                
                email = cloud_data.get("email")
                metadata = cloud_data.get("metadata") 
                uid = cloud_data.get("uid")

                data, error = sign_in_with_email_password(email, pw)
                if error:
                    print(f"DEBUG: Firebase login error: {error}")
                    self.show_error("Incorrect username or password.")
                    return
                
                if not data or "localId" not in data:
                    print(f"DEBUG: Invalid Firebase login response: {data}")
                    self.show_error("Login failed. Please try again.")
                    return
                
                uid = data.get("localId") or uid
                
                try:
                    dek, db_path = ensure_account(username, pw, create_if_missing=False, path=self.app.storage_path, email=email, metadata=metadata)
                except Exception as e:
                    print(f"DEBUG: Critical Local DB unlock failed: {e}")
                    self.show_error(f"Local Account Encryption Error: {str(e)}")
                    return

            # Success
            print(f"DEBUG: Login successful for {username}. Navigating to dashboard.")
            self.app.current_user = username 
            self.app.current_uid = uid
            self.app.current_email = email
            self.app.derived_key = dek
            self.app.db_path = db_path
            
            save_last_user(username, self.app.storage_path)
            self.app.start_scheduler()
            self.app.switch_screen("dashboard")
            
        except Exception as e:
            print("CRITICAL LOGIN ERROR:")
            import traceback
            traceback.print_exc()
            self.show_error(f"Unexpected error: {str(e)}")

    def map_error(self, error_code):
        if "EMAIL_NOT_FOUND" in error_code or "USER_NOT_FOUND" in error_code:
            return "Account does not exist."
        if "INVALID_PASSWORD" in error_code or "INVALID_LOGIN_CREDENTIALS" in error_code:
            return "Incorrect email or password."
        if "EMAIL_EXISTS" in error_code:
            return "This email is already registered."
        if "INVALID_EMAIL" in error_code:
            return "Invalid email format."
        if "WEAK_PASSWORD" in error_code:
            return "Password is too weak (min 6 characters)."
        if "TOO_MANY_ATTEMPTS" in error_code:
             return "Too many failed attempts. Try later."
        return f"Authentication Failed: {error_code}"

    def show_error(self, message):
        from kivymd.uix.dialog import MDDialog
        self.dialog = MDDialog(
            title="Authentication Error",
            text=str(message),
            buttons=[MDFlatButton(text="OK", on_release=lambda x: self.dialog.dismiss())]
        )
        self.dialog.open()
