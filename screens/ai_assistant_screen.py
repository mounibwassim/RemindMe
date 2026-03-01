from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDIconButton, MDRaisedButton, MDFlatButton, MDFillRoundFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.list import MDList
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog
from kivy.clock import Clock
from datetime import datetime
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivy.app import App

from backend.ai_assistant import detect_intent, clean_title_only, validate_date, validate_time, infer_category, extract_task_details
from backend.storage import save_task
from backend.crypto import encrypt_bytes

class AIAssistantScreen(MDScreen):
    STATE_TITLE = 0
    STATE_DATE = 1
    STATE_TIME = 2
    STATE_PRIORITY = 3
    
    session_token = 0

    def on_pre_enter(self):
        # Definitively clear history for a clean session
        if hasattr(self, 'chat_list'):
            self.chat_list.clear_widgets()
        self.session_token = datetime.now().timestamp()
        self.reset_flow()

    def on_enter(self):
        self.app = App.get_running_app()
        self.md_bg_color = self.app.theme_cls.bg_normal
        # load_view already clears but let's be safe
        self.load_view()
        
    def reset_flow(self):
        self.cur_state = self.STATE_TITLE
        self.task_draft = {}
        # Unlock input
        if hasattr(self, 'input_field'):
            self.input_field.disabled = False
        
    def load_view(self):
        self.clear_widgets()
        layout = MDBoxLayout(orientation="vertical", spacing=0, padding=0)
        layout.md_bg_color = self.app.theme_cls.bg_normal
        
        # --- HEADER ---
        header_card = MDCard(size_hint_y=None, height=dp(80), elevation=4)
        header_card.radius = [0, 0, 20, 20]
        header_card.md_bg_color = self.app.theme_cls.primary_color
        
        h_box = MDBoxLayout(padding=[dp(10), 0], spacing=dp(5))
        
        h_box.add_widget(MDIconButton(
            icon="arrow-left", theme_text_color="Custom", text_color=(1,1,1,1),
            on_release=self.go_back, pos_hint={'center_y': 0.5}
        ))
        
        h_box.add_widget(MDLabel(
            text="AI Task Assistant", font_style="H5", theme_text_color="Custom", text_color=(1,1,1,1),
            halign="center", bold=True, pos_hint={'center_y': 0.5}
        ))
        h_box.add_widget(Widget(size_hint_x=None, width=dp(48)))
        header_card.add_widget(h_box)
        layout.add_widget(header_card)
        
        # --- CHAT AREA ---
        content_box = MDBoxLayout(orientation="vertical", spacing=dp(10), padding=dp(20))
        self.scroll = MDScrollView(do_scroll_x=False)
        self.chat_list = MDList()
        self.scroll.add_widget(self.chat_list)
        content_box.add_widget(self.scroll)
        
        # --- INPUT AREA ---
        input_row = MDBoxLayout(size_hint_y=None, height=dp(80), spacing=dp(10))
        self.input_field = MDTextField(
            hint_text="Type your message...",
            helper_text="Example: Buy milk tomorrow at 9 am",
            helper_text_mode="persistent",
            mode="rectangle",
            size_hint_x=0.85
        )
        # Bind enter key
        self.input_field.bind(on_text_validate=self.on_input_confirm)
        
        send_btn = MDIconButton(
            icon="send",
            on_release=self.on_input_confirm,
            theme_text_color="Custom",
            text_color=self.app.theme_cls.primary_color,
            pos_hint={'center_y': 0.5}
        )
        
        input_row.add_widget(self.input_field)
        input_row.add_widget(send_btn)
        content_box.add_widget(input_row)
        
        layout.add_widget(content_box)
        self.add_widget(layout)
        
        # Initial Greeting (Only if empty history)
        if not self.chat_list.children:
             self.add_message("AI", "Hi! I’m here to help you create a task. Please tell me what task you want to add.", token=self.session_token)

    def go_back(self, instance):
        # Reset again just in case
        self.session_token = 0
        self.app.switch_screen("dashboard")

    def add_message(self, sender, text, token=None):
        # If a token is provided, verify it matches current session to prevent stale messages
        if token and token != self.session_token:
            return
            
        is_user = (sender == "User")
        is_dark = (self.app.theme_cls.theme_style == "Dark")
        
        if is_user:
            align = "right"
            if is_dark:
                bg_color = (0.2, 0.3, 0.4, 1) # Darker Blue/Grey for User
                text_color = (1, 1, 1, 1)
            else:
                bg_color = (0.9, 0.95, 1, 1) # Light Blue
                text_color = (0, 0, 0, 1)
            title_text = "You"
        else:
            align = "left"
            if is_dark:
                bg_color = (0.15, 0.15, 0.15, 1) # Dark Grey for AI
                text_color = (1, 1, 1, 1)
            else:
                bg_color = (0.95, 0.95, 0.95, 1) # Light Grey
                text_color = (0, 0, 0, 1)
            title_text = "AI Assistant"

        # Create Chat Bubble Card
        card = MDCard(
            orientation="vertical", 
            padding=dp(12), 
            spacing=dp(8),
            size_hint=(0.8, None)
        )
        card.md_bg_color = bg_color
        card.radius = [12]

        title_lbl = MDLabel(
            text=title_text, 
            font_style="Caption", 
            theme_text_color="Custom", 
            text_color=(0.8, 0.8, 0.8, 1) if is_dark else (0.4, 0.4, 0.4, 1),
            size_hint_y=None, 
            height=dp(20)
        )
        card.add_widget(title_lbl)
        
        main_text = MDLabel(
            text=text, 
            theme_text_color="Custom", 
            text_color=text_color,
            size_hint_y=None
        )
        # Bind text_size to width minus padding to force text wrap
        main_text.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))
        
        card.add_widget(main_text)
        
        # Manually bound card and label height to texture size
        def update_heights(*args):
             main_text.height = main_text.texture_size[1]
             card.height = title_lbl.height + main_text.height + dp(32) # include padding/spacing
        main_text.bind(texture_size=update_heights)
        
        # Create Container
        container = MDBoxLayout(orientation="horizontal", size_hint_y=None, padding=[0, dp(5), 0, dp(5)])
        container.bind(minimum_height=container.setter('height'))
        if is_user:
            container.add_widget(Widget())
            container.add_widget(card)
        else:
            container.add_widget(card)
            container.add_widget(Widget())
            
        self.chat_list.add_widget(container)
        Clock.schedule_once(lambda _dt: self.scroll.scroll_to(container))

    def run_logic(self, text, token=None):
        # 2. State Machine Logic
        if self.cur_state == self.STATE_TITLE:
            self.handle_title(text, token=token)
            
        elif self.cur_state == self.STATE_DATE:
            self.handle_date(text, token=token)
            
        elif self.cur_state == self.STATE_TIME:
            self.handle_time(text, token=token)
            
        elif self.cur_state == self.STATE_PRIORITY:
            self.handle_priority(text, token=token)

    def handle_title(self, text, token=None):
        # Use smart extraction
        title, dt, has_time, error = extract_task_details(text)
        
        if not title:
             Clock.schedule_once(lambda _dt: self.add_message("AI", "I didn't catch that. What is the task title?", token=token))
             return

        self.task_draft['title'] = title
        
        category, icon = infer_category(title)
        self.task_draft['category'] = category
        self.task_draft['icon'] = icon
        self.task_draft['has_time'] = has_time
        if has_time and dt:
             self.task_draft['due_iso'] = dt.isoformat()
        
        # LOGIC BRANCHING
        if error == "past_time":
            Clock.schedule_once(lambda _dt: self.add_message("AI", f"Creating '{title}', but that date is in the past. Please select a future date and time.", token=token))
            self.cur_state = self.STATE_DATE
            return
            
        if isinstance(dt, dict) and dt.get("status") == "incomplete":
            msg = "I need a clearer date or time. Please specify when clearly (e.g., 'Tomorrow at 5pm')."
            Clock.schedule_once(lambda _dt: self.add_message("AI", msg, token=token))
            self.cur_state = self.STATE_DATE
            return
            
        if error == "missing_date" or not dt:
            # Case A: Title Only -> Ask Date
            Clock.schedule_once(lambda _dt: self.add_message("AI", f"Creating '{title}'. Please select the task date (e.g., Tomorrow, Monday).", token=token))
            self.cur_state = self.STATE_DATE
            return
            
        # We have a valid date (either provided or Today-by-default)
        if isinstance(dt, float):
             dt = datetime.fromtimestamp(dt)
        self.task_draft['date_obj'] = dt
        
        if has_time and dt:
             self.cur_state = self.STATE_PRIORITY
             msg = f"Got it: '{title}' for {dt.strftime('%b %d at %I:%M %p')}. What priority? (Low, Medium, High)"
             Clock.schedule_once(lambda _dt: self.add_message("AI", msg, token=token))
             Clock.schedule_once(lambda _dt: self.show_priority_buttons(), 0.5)
        else:
             self.cur_state = self.STATE_TIME
             Clock.schedule_once(lambda _dt: self.add_message("AI", f"Got the date ({dt.strftime('%b %d')}). What exact time? (e.g. 5pm)", token=token))

    def handle_date(self, text, token=None):
        _, dt, has_time, error = extract_task_details(text)
        
        if isinstance(dt, dict) and dt.get("status") == "incomplete":
             msg = "I still couldn't understand that format. Please use a clear time like '5pm' or '17:00'."
             Clock.schedule_once(lambda _dt: self.add_message("AI", msg, token=token))
             return
             
        if error == "missing_date" or not dt:
             Clock.schedule_once(lambda _dt: self.add_message("AI", "I couldn't understand that date. Please try 'Tomorrow', 'Monday', or 'Dec 25'.", token=token))
             return
             
        self.task_draft['date_obj'] = dt
        self.task_draft['has_time'] = has_time
        if isinstance(dt, float):
             dt = datetime.fromtimestamp(dt)
        
        if has_time:
             self.task_draft['due_iso'] = dt.isoformat()
             
        if has_time:
             self.cur_state = self.STATE_PRIORITY
             msg = f"Got it: {dt.strftime('%b %d at %I:%M %p')}. What priority? (Low, Medium, High)"
             Clock.schedule_once(lambda _dt: self.add_message("AI", msg, token=token))
             Clock.schedule_once(lambda _dt: self.show_priority_buttons(), 0.5)
        else:
             self.cur_state = self.STATE_TIME
             Clock.schedule_once(lambda _dt: self.add_message("AI", f"Got the date ({dt.strftime('%b %d')}). What exact time? (e.g. 5pm)", token=token))

    def handle_time(self, text, token=None):
        # We need the date context to validate correct future time (if today)
        date_ctx = self.task_draft.get('date_obj')
        
        iso, valid, error = validate_time(text, date_ctx)
        
        if not valid:
             Clock.schedule_once(lambda _dt: self.add_message("AI", error, token=token))
             if "past" in error.lower():
                 Clock.schedule_once(lambda _dt: self.add_message("AI", "This is a past time. Please select a future time.", token=token))
             return
             
        self.task_draft['due_iso'] = iso
        self.cur_state = self.STATE_PRIORITY
        
        # Show buttons for priority
        Clock.schedule_once(lambda _dt: self.add_message("AI", "Please choose the task priority: Low, Medium, or High.", token=token))
        Clock.schedule_once(lambda _dt: self.show_priority_buttons())

    def show_priority_buttons(self):
        # Lock Input
        self.input_field.disabled = True

        # Big Layout for Priority
        layout = MDBoxLayout(
            orientation="vertical", 
            spacing=dp(15), 
            padding=[dp(20), dp(10)],
            size_hint=(0.9, None), 
            size_hint_y=None, height=dp(180), # Fixed height for buttons
            radius=[15],
            md_bg_color=App.get_running_app().theme_cls.bg_normal
        )
        
        label = MDLabel(
            text="Select Priority", 
            halign="center", 
            theme_text_color="Custom",
            text_color=(1,1,1,1) if self.app.theme_cls.theme_style=="Dark" else (0,0,0,1),
            font_style="H6",
            size_hint_y=None, height=dp(30)
        )
        layout.add_widget(label)
        
        btn_h = MDFillRoundFlatButton(
            text="High Priority", 
            md_bg_color=(1, 0.2, 0.2, 1), 
            size_hint_x=1,
            on_release=lambda x: self.process_input(None, text_override="High")
        )
        btn_m = MDFillRoundFlatButton(
            text="Medium Priority", 
            md_bg_color=(1, 0.8, 0, 1), 
            size_hint_x=1,
            text_color=(0,0,0,1),
            on_release=lambda x: self.process_input(None, text_override="Medium")
        )
        btn_l = MDFillRoundFlatButton(
            text="Low Priority", 
            md_bg_color=(0.2, 0.8, 0.2, 1), 
            size_hint_x=1,
            on_release=lambda x: self.process_input(None, text_override="Low")
        )
        
        layout.add_widget(btn_h)
        layout.add_widget(btn_m)
        layout.add_widget(btn_l)
        
        self.chat_list.add_widget(layout)
        # show_date_picker mechanism was completely stripped to resolve user FYP issue UX
        # where the KivyMD dialog kept intercepting chat flow.
        
    # Entry point for user input
    def on_input_confirm(self, instance):
        text = self.input_field.text.strip()
        if not text: return
        
        self.add_message("User", text, token=self.session_token)
        self.input_field.text = ""
        
        # Start background thread
        import threading
        t = threading.Thread(target=self._safe_process_logic, args=(text, self.session_token))
        t.start()

    def _safe_process_logic(self, text, token):
        try:
            self.process_input(None, text_override=text, token=token)
        except Exception as e:
            err_msg = str(e)
            print(f"AI Logic Error: {err_msg}")
            from kivy.clock import Clock
            # Use Clock to update UI from background thread. Pass variables safely.
            Clock.schedule_once(lambda _dt, msg=err_msg, t=token: self.add_message("AI", f"Internal error: {msg}", token=t))
            Clock.schedule_once(lambda _dt: self.reset_flow())

    # Original logic (now called from thread)
    def process_input(self, instance, text_override=None, token=None): 
        if text_override:
            text = text_override
        else:
            # Fallback if called directly without override (from buttons)
            text = self.input_field.text.strip()
            
        if not text: return
        
        # If button pressed, we want to simulate user message
        if text_override:
             # self.add_message already called in on_input_confirm for manual typing.
             # But buttons call process_input directly.
             # Wait, if button calls it, we might need a separate helper.
             pass
        else:
             from kivy.clock import Clock
             Clock.schedule_once(lambda _dt: self.add_message("User", text, token=token or self.session_token))
             self.input_field.text = ""

        # Check for Priority State FIRST 
        if self.cur_state == self.STATE_PRIORITY:
             self.handle_priority(text, token=token)
             return

        # Global Intent Detection
        intent = detect_intent(text)
        
        if intent == "GREETING":
            from kivy.clock import Clock
            Clock.schedule_once(lambda _dt: self.add_message("AI", "Hi! I’m here to help you create a task. Please tell me what task you want to add.", token=token))
            Clock.schedule_once(lambda _dt: self.reset_flow())
            return
            
        if intent == "UNRELATED":
            from kivy.clock import Clock
            Clock.schedule_once(lambda _dt: self.add_message("AI", "⚠️ This assistant is only for task creation and management.", token=token))
            Clock.schedule_once(lambda _dt: self.reset_flow())
            return

        # State Machine
        self.run_logic(text, token=token)

    def handle_priority(self, text, token=None):
        print(f"DEBUG: handle_priority called with '{text}'")
        text = text.lower()
        prio_map = {"high": 1, "medium": 2, "med": 2, "low": 3}
        
        val = 3
        found = False
        for k, v in prio_map.items():
            if k in text:
                val = v
                found = True
                break
        
        if not found:
            Clock.schedule_once(lambda _dt: self.add_message("AI", "Please choose Low, Medium, or High.", token=token))
            return

        # SAVE
        title = self.task_draft['title']
        from backend.ai_assistant import generate_description
        desc = generate_description(title)
        
        ct, nonce = encrypt_bytes(title.encode("utf-8"), self.app.derived_key)
        
        save_task(
            self.app.db_path,
            ct, nonce,
            self.task_draft['due_iso'],
            val,
            datetime.utcnow().isoformat(),
            self.task_draft.get('category', 'General'),
            "Default", desc,
            user_uid=self.app.current_uid
        )
        
        # Show confirmation
        dt_obj = datetime.fromisoformat(self.task_draft['due_iso'])
        dt_str = dt_obj.strftime("%b %d at %I:%M %p")
        prio_names = {1: "High", 2: "Medium", 3: "Low"}
        prio_str = prio_names.get(val, "Medium")
        
        confirm_msg = f"Task created: {title} ({dt_str}, {prio_str}).\n\nWhat is the next task you want to create?"
        Clock.schedule_once(lambda _dt: self.add_message("AI", confirm_msg, token=token))
        self.reset_flow()
        
        # Refresh Dashboard
        if self.app.sm.has_screen("dashboard"):
            self.app.sm.get_screen("dashboard").refresh_tasks(None)

