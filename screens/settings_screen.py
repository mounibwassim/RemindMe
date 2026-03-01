from kivymd.uix.screen import MDScreen
from kivymd.uix.list import OneLineListItem, OneLineAvatarIconListItem, IconLeftWidget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton, MDFillRoundFlatIconButton
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.slider import MDSlider
from kivymd.uix.card import MDCard # Moved to top
from kivymd.uix.menu import MDDropdownMenu
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivy.app import App

from backend.storage import change_passphrase

class SettingsScreen(MDScreen):
    def on_enter(self):
        self.app = App.get_running_app()
        try:
            self.load_view()
        except Exception as e:
            print(f"CRASH PREVENTION: Settings load error: {e}")
            from kivymd.toast import toast
            toast(f"Error loading settings: {e}")

    def load_view(self):
        app = App.get_running_app()
        print(f"DEBUG: Loading Settings View. Theme: {app.theme_cls.theme_style}")
        self.clear_widgets()
        
        # ROOT LAYOUT
        self.root_layout = MDBoxLayout(orientation="vertical")
        self.root_layout.md_bg_color = app.theme_cls.bg_normal
        
        # --- Top Header Frame (Blue) ---
        header_card = MDCard(
            size_hint_y=None, 
            height=dp(80), 
            radius=[0, 0, 20, 20], 
            elevation=4,
            md_bg_color=app.theme_cls.primary_color
        )
        
        h_layout = MDBoxLayout(orientation="horizontal", padding=[dp(10), 0], spacing=dp(5))
        
        # Back Button
        h_layout.add_widget(MDIconButton(
            icon="arrow-left", 
            theme_text_color="Custom", 
            text_color=(1,1,1,1), 
            on_release=self.go_back,
            pos_hint={'center_y': 0.5}
        ))
        
        # Title
        h_layout.add_widget(MDLabel(
            text="Settings", 
            font_style="H5", 
            theme_text_color="Custom", 
            text_color=(1,1,1,1), 
            halign="center",
            valign="center",
            bold=True
        ))
        
        # Spacer for balance (Right side)
        h_layout.add_widget(Widget(size_hint_x=None, width=dp(48))) 
        
        header_card.add_widget(h_layout)
        self.root_layout.add_widget(header_card)
        
        # Content Layout (Scrollable)
        from kivymd.uix.scrollview import MDScrollView
        scroll = MDScrollView()
        layout = MDBoxLayout(orientation="vertical", padding=dp(20), spacing=dp(20), size_hint_y=None, height=dp(600))
        
        # --- Theme Toggle Section ---
        layout.add_widget(MDLabel(text="Theme Toggle Section", font_style="Subtitle1", bold=True, theme_text_color="Primary", size_hint_y=None, height=dp(40)))
        
        theme_row = MDBoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(50))
        
        is_light = (app.theme_cls.theme_style == "Light")
        
        # Light Mode Button
        btn_light = MDFillRoundFlatIconButton(
            text="Light Mode", 
            icon="weather-sunny",
            size_hint_x=0.5,
            on_release=lambda x: self.set_theme("Light")
        )
        if is_light:
            btn_light.md_bg_color = (0.8, 0.8, 0.8, 1)
            btn_light.text_color = (0, 0, 0, 1)
        else:
             btn_light.md_bg_color = (0.2, 0.2, 0.2, 1)
             
        theme_row.add_widget(btn_light)
        
        # Dark Mode Button
        btn_dark = MDFillRoundFlatIconButton(
            text="Dark Mode", 
            icon="weather-night",
            size_hint_x=0.5,
            on_release=lambda x: self.set_theme("Dark")
        )
        if not is_light:
            btn_dark.md_bg_color = (0.3, 0.3, 0.5, 1)
        else:
             btn_dark.md_bg_color = (0.9, 0.9, 0.9, 1)

        theme_row.add_widget(btn_dark)
        layout.add_widget(theme_row)
        
        # --- Audit Analytics Controls ---
        layout.add_widget(MDLabel(text="Audit Analytics Controls", font_style="Subtitle1", bold=True, theme_text_color="Primary", size_hint_y=None, height=dp(40)))
        
        layout.add_widget(MDFillRoundFlatIconButton(
            text="View Audit Analytics", 
            icon="chart-bar",
            on_release=self.go_to_audit, 
            size_hint_x=1
        ))

        # --- Security Section ---
        layout.add_widget(MDLabel(text="Security Section", font_style="Subtitle1", bold=True, theme_text_color="Primary", size_hint_y=None, height=dp(40)))
        
        layout.add_widget(MDFillRoundFlatIconButton(
            text="Change Password", 
            icon="key",
            on_release=self.show_change_pass_dialog, 
            size_hint_x=1
        ))
        
        layout.add_widget(MDLabel()) # Spacer
        
        scroll.add_widget(layout)
        self.root_layout.add_widget(scroll)
        self.add_widget(self.root_layout)

    def set_theme(self, style):
        app = App.get_running_app()
        if app.theme_cls.theme_style == style:
            return
        
        app.theme_cls.theme_style = style
        if hasattr(app, 'update_theme_colors'):
            app.update_theme_colors()
            
        from backend.storage import save_theme_preference
        save_theme_preference(style, app.storage_path)
        
        self.load_view()

    def show_change_pass_dialog(self, instance):
        # Create Text Fields with ID for reference
        self.old_pass = MDTextField(
            hint_text="Old Password", 
            password=True, 
            icon_right="eye-off",
        )
        self.old_pass.bind(on_touch_down=self.toggle_old_pass_visibility)
        
        self.new_pass = MDTextField(
            hint_text="New Password", 
            password=True, 
            icon_right="eye-off"
        )
        self.new_pass.bind(on_touch_down=self.toggle_new_pass_visibility)
        
        content = MDBoxLayout(orientation="vertical", size_hint_y=None, height=dp(150), spacing=dp(10))
        content.add_widget(self.old_pass)
        content.add_widget(self.new_pass)
        
        self.dialog = MDDialog(
            title="Change Password",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(text="Save", on_release=self.do_change_pass),
                MDRaisedButton(text="Cancel", on_release=lambda x: self.dialog.dismiss())
            ]
        )
        self.dialog.open()

    def toggle_old_pass_visibility(self, instance, touch):
        if instance.collide_point(*touch.pos):
            # Check if touch is on the icon area (right side)
            if touch.x > instance.right - dp(40):
                instance.password = not instance.password
                instance.icon_right = "eye" if not instance.password else "eye-off"
                return True
        return False

    def toggle_new_pass_visibility(self, instance, touch):
        if instance.collide_point(*touch.pos):
            if touch.x > instance.right - dp(40):
                instance.password = not instance.password
                instance.icon_right = "eye" if not instance.password else "eye-off"
                return True
        return False
    def do_change_pass(self, instance):
        if getattr(self, "saving_pass", False):
            return
        self.saving_pass = True
        
        old = self.old_pass.text
        new = self.new_pass.text
        
        if not old or not new:
            from kivymd.toast import toast
            toast("Please enter both passwords")
            self.saving_pass = False
            return
            
        try:
            # 0. User Lookup Validation (Transaction Safety)
            from backend.auth_service import get_username_data
            user_norm = self.app.current_user.strip().lower()
            
            # Fetch valid user explicitly before doing anything
            user_data, lookup_error = get_username_data(user_norm)
            if not user_data:
                self.show_error("User not found")
                self.saving_pass = False
                return
                
            email = user_data.get("email")
            if not email:
                email = getattr(self.app, 'current_email', user_norm)
                
            # 1. Verify old password (Auth)
            from backend.firebase_service import sign_in_with_email_password, update_password
            auth_data, error = sign_in_with_email_password(email, old)
            
            if error:
                self.show_error(f"Error: {error}")
                self.saving_pass = False
                return
                
            id_token = auth_data['idToken']
            
            # 2. Update Password (Commit)
            res, error = update_password(id_token, new)
            
            # Validation simulating rowcount check
            if error or not res:
                 self.show_error(f"Password update failed: {error}")
                 self.saving_pass = False
                 return
            
            # 3. SUCCESS UX
            self.dialog.dismiss()
            self.saving_pass = False
            
            from kivymd.uix.dialog import MDDialog
            self.success_dialog = MDDialog(
                title="Success", 
                text="Password changed successfully.",
                buttons=[MDRaisedButton(text="OK", on_release=lambda x: self.success_dialog.dismiss())]
            )
            self.success_dialog.open()
            
        except ValueError as ve:
            # Catch known validation errors from storage
            self.show_error(str(ve))
            self.saving_pass = False
        except Exception as e:
            # Check if this is the "Invalid passphrase" issue
            print("Change pass failed (Unknown):", e)
            self.show_error(f"Error: {e}")
            self.saving_pass = False

    def show_error(self, msg):
        from kivymd.uix.dialog import MDDialog
        self.err_dialog = MDDialog(title="Error", text=msg, buttons=[MDRaisedButton(text="OK", on_release=lambda x: self.err_dialog.dismiss())])
        self.err_dialog.open()

    def go_to_audit(self, instance):
        self.app.switch_screen("audit")

    def go_back(self, instance):
        self.app.switch_screen("dashboard")

    def confirm_clear_analytics(self, instance):
        self.dialog = MDDialog(
            title="Reset Analytics?",
            text="This will reset your productivity analytics (Sent, Opened, Snoozed, Completed). Tasks will not be deleted.\n\nContinue?",
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda x: self.dialog.dismiss()),
                MDRaisedButton(text="RESET", md_bg_color=(0.8, 0.2, 0.2, 1), on_release=self.do_clear_analytics)
            ]
        )
        self.dialog.open()
        
    def do_clear_analytics(self, instance):
        self.dialog.dismiss()
        if self.app.db_path:
            from backend.storage import reset_audit_stats
            reset_audit_stats(self.app.db_path)
            
            # Show toast/feedback
            from kivymd.toast import toast
            toast("Analytics Data Reset")
