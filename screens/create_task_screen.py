from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDRoundFlatIconButton, MDFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.pickers import MDDatePicker, MDTimePicker
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.dialog import MDDialog
from kivymd.uix.card import MDCard
from kivymd.uix.list import OneLineListItem, OneLineAvatarIconListItem, IconLeftWidget, IconRightWidget, MDList, OneLineAvatarIconListItem, IconLeftWidget, IconRightWidget
from kivymd.uix.scrollview import MDScrollView
from kivy.uix.widget import Widget
from datetime import datetime, timedelta

from kivy.metrics import dp
from kivy.app import App

from backend.crypto import encrypt_bytes
from backend.storage import save_task, update_task
from backend.audit import write_audit

class CreateTaskScreen(MDScreen):
    class CategoryChip(MDIconButton):
        def __init__(self, cat, icon, screen, **kwargs):
            super().__init__(**kwargs)
            self.icon = icon
            self.cat = cat
            self.screen = screen
            self.theme_text_color = "Custom"
            self.text_color = (0.5, 0.5, 0.5, 1)
            self.user_font_size = "24sp"
            
        def on_release(self):
            self.screen.set_category(self.cat)
            
    def on_enter(self):
        try:
            print("Entering Create Task Screen...")
            self.app = App.get_running_app()
            # Check if we are in modify mode
            if hasattr(self.app, 'modify_task_data') and self.app.modify_task_data:
                self.mode = "modify"
                self.task_data = self.app.modify_task_data
                self.app.modify_task_data = None # Clear after consuming
            else:
                self.mode = "create"
                self.task_data = None
                
            self.load_view()
        except Exception as e:
            print(f"Error in CreateTaskScreen.on_enter: {e}")
            import traceback
            traceback.print_exc()

    def load_view(self):
        self.clear_widgets()
        
        # Root Container (Vertical)
        root_box = MDBoxLayout(orientation="vertical")
        root_box.md_bg_color = App.get_running_app().theme_cls.bg_normal
        
        # --- HEADER (Blue Frame) ---
        header = MDCard(
            size_hint_y=None, height=dp(80),
            radius=[0, 0, 20, 20], elevation=4,
            md_bg_color=self.app.theme_cls.primary_color
        )
        h_box = MDBoxLayout(padding=[dp(10), 0], spacing=dp(5))
        
        # Back Button (White)
        from kivymd.uix.button import MDIconButton
        h_box.add_widget(MDIconButton(
            icon="arrow-left", 
            theme_text_color="Custom", 
            text_color=(1,1,1,1),
            on_release=lambda x: setattr(self.manager, 'current', 'dashboard'),
            pos_hint={'center_y': 0.5}
        ))
        
        # Title (White)
        title_text = "Create New Task" if self.mode == "create" else "Modify Task"
        h_box.add_widget(MDLabel(
            text=title_text, 
            font_style="H5", 
            theme_text_color="Custom", 
            text_color=(1,1,1,1),
            halign="center", 
            valign="center",
            bold=True,
            pos_hint={'center_y': 0.5}
        ))
        
        # Spacer for balance
        h_box.add_widget(Widget(size_hint_x=None, width=dp(48)))
        
        header.add_widget(h_box)
        root_box.add_widget(header)
        
        # --- CONTENT (Scrollable) ---
        scroll = MDScrollView()
        layout = MDBoxLayout(orientation="vertical", spacing=dp(15), padding=[dp(20), dp(20)], size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))

        # Task Title Input
        self.title_input = MDTextField(
            hint_text="Task Title",
            mode="rectangle"
        )
        layout.add_widget(self.title_input)

        # Description Input
        self.desc_input = MDTextField(
            hint_text="Description (Optional)",
            mode="rectangle",
            multiline=True,
            size_hint_y=None,
            height=dp(100)
        )
        layout.add_widget(self.desc_input)

        # Date & Time Pickers Row
        dt_row = MDBoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(50))
        
        self.date_btn = MDRoundFlatIconButton(
            text="Select Date",
            icon="calendar",
            on_release=self.show_date_picker
        )
        self.time_btn = MDRoundFlatIconButton(
            text="Select Time",
            icon="clock",
            on_release=self.show_time_picker
        )
        
        dt_row.add_widget(self.date_btn)
        dt_row.add_widget(self.time_btn)
        layout.add_widget(dt_row)
        
        # Priority Section
        layout.add_widget(MDLabel(text="Priority", font_style="Subtitle1", size_hint_y=None, height=dp(30)))
        prio_row = MDBoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(50))
        
        self.prio_low = MDRaisedButton(text="Low", md_bg_color=(0.9, 0.9, 0.9, 1), on_release=lambda x: self.set_priority(3))
        self.prio_med = MDRaisedButton(text="Medium", md_bg_color=(0.9, 0.9, 0.9, 1), on_release=lambda x: self.set_priority(2))
        self.prio_high = MDRaisedButton(text="High", md_bg_color=(0.9, 0.9, 0.9, 1), on_release=lambda x: self.set_priority(1))
        
        prio_row.add_widget(self.prio_low)
        prio_row.add_widget(self.prio_med)
        prio_row.add_widget(self.prio_high)
        layout.add_widget(prio_row)
        
        self.selected_priority = 3 # Default Low

        # Wrap everything in ScrollView for Mobile Visibility
        # Note: We must ensure 'scroll' and 'root_box' are wired correctly at the end.
        
        # Category Section
        layout.add_widget(MDLabel(text="Category", font_style="Subtitle1", size_hint_y=None, height=dp(30)))
        cat_grid = MDGridLayout(cols=3, spacing=dp(10), size_hint_y=None, height=dp(300))
        
        # Categories: Work, Study, Travel, Personal, General, Other, Health, Gym, Shopping
        self.categories = {
            "Work": "briefcase",
            "Study": "school",
            "Travel": "airplane",
            "Personal": "account",
            "General": "star",
            "Health": "heart-pulse",
            "Gym": "dumbbell",
            "Shopping": "cart",
            "Other": "circle-outline"
        }
        self.cat_buttons = {}
        
        # Helper to create label
        def create_cat_item(cat, icon):
            box = MDBoxLayout(orientation="vertical", spacing=dp(2), size_hint=(1, None), height=dp(60))
            chip = self.CategoryChip(cat, icon, self)
            self.cat_buttons[cat] = chip
            
            box.add_widget(chip)
            
            # Simple English Label
            box.add_widget(MDLabel(text=cat, halign="center", font_style="Caption", theme_text_color="Custom", text_color=(0.5, 0.5, 0.5, 1)))
            return box

        for cat, icon in self.categories.items():
            cat_grid.add_widget(create_cat_item(cat, icon))
            
        layout.add_widget(cat_grid)
        self.selected_category = "Work"

        # Spacer
        layout.add_widget(Widget(size_hint_y=None, height=dp(40)))

        # Sound Section (Modern List)
        # Sound removed
        
        # Container for list
        sound_box = MDBoxLayout(orientation="vertical", size_hint_y=None, height=dp(40))
        
        self.sound_list = MDList()
        self.sound_items = {} # name -> widget
        

        
        if False: # loop removed
            # Custom Item: IconLeft(Play), Text, IconRight(Check if selected)
            item = OneLineAvatarIconListItem(
                text=s,
                on_release=lambda x, name=s: self.select_sound(name)
            )
            
            # Play Icon (Left)
            play_icon = IconLeftWidget(icon="play-circle-outline")
            play_icon.bind(on_release=lambda x, name=s: self.preview_sound(name))
            item.add_widget(play_icon)
            
            check_icon = IconRightWidget(icon="check", theme_text_color="Custom", text_color=(0, 0.7, 0, 1))
            check_icon.opacity = 0 # Hidden by default
            
            item.add_widget(check_icon)
            self.sound_items[s] = check_icon
            
            self.sound_list.add_widget(item)

        # Sound UI removed
        self.selected_sound = "Default"

        # Action Buttons
        action_row = MDBoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(50))
        
        btn_text = "Create Task" if self.mode == "create" else "Update Task"
        action_row.add_widget(
            MDRaisedButton(
                text=btn_text,
                on_release=self.save_task
            )
        )
        
        action_row.add_widget(
            MDFlatButton(
                text="Cancel",
                on_release=self.go_back
            )
        )
        layout.add_widget(action_row)
        
        layout.add_widget(Widget(size_hint_y=None, height=dp(20))) # Spacer
        
        # Finish Layout Wiring
        scroll.add_widget(layout)
        root_box.add_widget(scroll)
        self.add_widget(root_box)
        
        # Pre-fill if modify
        if self.mode == "modify":
            self.prefill_data()
        else:
            # Defaults
            self.selected_date = datetime.now().date()
                
            self.selected_time = datetime.now().time()
            self.update_dt_labels()
            self.set_priority(3)
            self.set_category("Work")
            self.set_sound("Default")

    def prefill_data(self):
        # task_data = (id, title, due_iso, priority, category) OR (..., category, sound)
        # We need to handle variable length from modify_task_data tuple passed from dashboard
        # Dashboard passes: (task_id, title, due, prio, category, sound) if sound exists
        
        # Let's assume dashboard passes correct tuple or we handle it
        # For now, let's unpack safely
        data = self.task_data
        tid = data[0]
        title = data[1]
        due_iso = data[2]
        prio = data[3]
        cat = data[4]
        sound = data[5] if len(data) > 5 else "Default"
        desc = data[6] if len(data) > 6 else ""
        
        self.title_input.text = title
        self.desc_input.text = desc
        
        try:
            dt = datetime.fromisoformat(due_iso)
            self.selected_date = dt.date()
            self.selected_time = dt.time()
        except:
            self.selected_date = datetime.now().date()
            self.selected_time = datetime.now().time()
            
        self.update_dt_labels()
        self.set_priority(prio)
        self.set_category(cat if cat else "Work")
        self.set_sound(sound)

    def set_priority(self, priority):
        self.selected_priority = priority
        # Reset colors to grey
        self.prio_low.md_bg_color = (0.9, 0.9, 0.9, 1)
        self.prio_med.md_bg_color = (0.9, 0.9, 0.9, 1)
        self.prio_high.md_bg_color = (0.9, 0.9, 0.9, 1)
        self.prio_low.text_color = (0, 0, 0, 1) # Black text
        self.prio_med.text_color = (0, 0, 0, 1)
        self.prio_high.text_color = (0, 0, 0, 1)
        
        if priority == 3:
            self.prio_low.md_bg_color = (0, 1, 0, 1) # Green
            self.prio_low.text_color = (1, 1, 1, 1) # White text
        elif priority == 2:
            self.prio_med.md_bg_color = (1, 1, 0, 1) # Yellow
            self.prio_med.text_color = (0, 0, 0, 1) # Black text for yellow
        elif priority == 1:
            self.prio_high.md_bg_color = (1, 0, 0, 1) # Red
            self.prio_high.text_color = (1, 1, 1, 1) # White text

    def set_category(self, category):
        self.selected_category = category
        # Reset all
        for cat, btn in self.cat_buttons.items():
            btn.text_color = (0.5, 0.5, 0.5, 1)
        
        # Highlight selected
        if category in self.cat_buttons:
            self.cat_buttons[category].text_color = (0, 0, 1, 1) # Blue active

    def update_dt_labels(self):
        self.date_btn.text = self.selected_date.strftime("%Y-%m-%d")
        self.time_btn.text = self.selected_time.strftime("%H:%M")

    def show_date_picker(self, instance):
        from kivy.core.window import Window
        
        class ResponsiveDatePicker(MDDatePicker):
            def on_device_orientation(self, inst, orientation):
                super().on_device_orientation(inst, "portrait")

        date_dialog = ResponsiveDatePicker(primary_color=self.app.theme_cls.primary_color)
        date_dialog.size_hint = (0.9, 0.8)
        date_dialog.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        date_dialog.bind(on_save=self.on_date_save)
        date_dialog.open()

    def on_date_save(self, instance, value, date_range):
        if value < datetime.now().date():
            self.show_error("Cannot select a past date.")
            return
        self.selected_date = value
        self.update_dt_labels()

    def show_time_picker(self, instance):
        from kivy.core.window import Window
        
        class ResponsiveTimePicker(MDTimePicker):
            def _update_pos_size(self, orientation, anim=False):
                super()._update_pos_size("portrait", anim)

        time_dialog = ResponsiveTimePicker(primary_color=self.app.theme_cls.primary_color)
        time_dialog.size_hint = (0.9, 0.8)
        time_dialog.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        time_dialog.bind(on_save=self.on_time_save)
        time_dialog.open()

    def on_time_save(self, instance, value):
        self.selected_time = value
        self.update_dt_labels()

    def set_sound(self, sound):
        # Kept for compatibility with prefill, but internal UI is gone
        self.selected_sound = "Default"

    def save_task(self, instance):
        title = self.title_input.text
        desc = self.desc_input.text
        
        if not title:
            self.title_input.error = True
            return
            
        if not self.selected_date or not self.selected_time:
            self.show_error("Please select both a date and a time.")
            return

        # Combine date and time
        try:
            due_dt = datetime.combine(self.selected_date, self.selected_time).replace(second=0, microsecond=0)
        except Exception as e:
            self.show_error(f"Invalid date/time selection: {e}")
            return
        
        # Validation
        if due_dt < datetime.now():
            self.show_error("Cannot create this task because the time has already passed. Please choose a future date/time.")
            return
            
        due_iso = due_dt.isoformat()
        
        # Encrypt title
        ct, nonce = encrypt_bytes(title.encode("utf-8"), self.app.derived_key)
        if self.mode == "create":
            save_task(
                self.app.db_path,
                ct,
                nonce,
                due_iso,
                self.selected_priority,
                datetime.utcnow().isoformat(),
                self.selected_category,
                self.selected_sound,
                desc,
                user_uid=self.app.current_uid
            )
            write_audit(self.app.db_path, 0, "created", user_uid=self.app.current_uid, task_title=title)
        else:
            # Update
            tid = self.task_data[0]
            update_task(
                self.app.db_path,
                tid,
                ct,
                nonce,
                due_iso,
                self.selected_priority,
                self.selected_category,
                self.selected_sound,
                desc,
                user_uid=self.app.current_uid
            )
            write_audit(self.app.db_path, tid, "updated", user_uid=self.app.current_uid, task_title=title)
            
        self.app.switch_screen("dashboard")

    def show_error(self, message):
        self.dialog = MDDialog(
            title="Error",
            text=message,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: self.dialog.dismiss()
                )
            ]
        )
        self.dialog.open()

    def go_back(self, instance):
        self.app.switch_screen("dashboard")
