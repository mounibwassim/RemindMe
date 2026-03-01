from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.scrollview import ScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDRaisedButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.pickers import MDTimePicker, MDDatePicker
from kivy.graphics import Color, RoundedRectangle, Line, Rectangle
from datetime import datetime, time, timezone, timedelta
from kivymd.app import MDApp
from kivy.app import App
from kivy.metrics import dp
from backend.storage import list_tasks, save_task
from backend.crypto import decrypt_bytes
from kivy.uix.behaviors import DragBehavior
from kivy.logger import Logger
import threading

class TaskBlock(MDBoxLayout):
    def __init__(self, task_data, callback, **kwargs):
        super().__init__(**kwargs)
        self.task_data = task_data
        self.callback = callback
        
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.size_hint_x = 1.0
        self.height = dp(30)
        self.spacing = dp(10)
        self.padding = [dp(0), dp(2), dp(5), dp(2)]
        
        # Priority Color Indicator
        prio = task_data.get('prio', 3)
        if prio == 1:
            color = (1, 0.2, 0.2, 1) # Redish
        elif prio == 2:
            color = (1, 0.6, 0.2, 1) # Orangeish
        else:
            color = (0.2, 0.7, 0.3, 1) # Greenish
            
        import datetime as dt_lib
        is_completed = False
        if task_data.get('completed') and str(task_data.get('completed')).strip() != "":
            color = (0.5, 0.5, 0.5, 1) # Greyed out
            self.opacity = 0.6
            is_completed = True
            
        # Overdue Calculation directly from DB flag
        is_overdue = task_data.get('is_overdue', 0) == 1
            
        # Alert/Overdue Color Override (Text Color only, no bulky container boxes)
        if is_overdue:
            color = (0.9, 0.1, 0.1, 1) # Strong Red Overdue
        elif task_data.get('notified') == 1 and not is_completed:
            color = (1, 0.3, 0.3, 1)   # Light Red Alert
            
        from kivymd.uix.label import MDLabel, MDIcon
        
        # Time
        try:
            dt_o = dt_lib.datetime.fromisoformat(task_data.get('due', ''))
            time_str = dt_o.strftime("%H:%M")
        except:
            time_str = "00:00"
            
        # Bullet
        self.add_widget(MDLabel(
            text=f"• {time_str} →",
            theme_text_color="Custom",
            text_color=color,
            font_style="Caption",
            bold=True,
            size_hint_x=None,
            width=dp(60),
            pos_hint={'center_y': 0.5}
        ))
        
        # Title
        self.add_widget(MDLabel(
            text=task_data.get('title', 'Task'),
            theme_text_color="Primary",
            font_style="Body2",
            shorten=True,
            pos_hint={'center_y': 0.5}
        ))
        
        if is_completed:
            self.add_widget(MDIcon(
                icon="check-circle", theme_text_color="Custom", 
                text_color=color, pos_hint={'center_y': 0.5}, font_size="16sp"
            ))
            
    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            self.callback(self.task_data)
            return True
        return super().on_touch_up(touch)

class HourRow(MDBoxLayout):
    def __init__(self, hour, **kwargs):
        super().__init__(**kwargs)
        self.hour = hour
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.bind(minimum_height=self.setter('height'))
        self.padding = [dp(10), dp(5), dp(10), dp(5)]
        self.spacing = dp(10)
        
        app = App.get_running_app()
        is_dark = getattr(app.theme_cls, 'theme_style', 'Light') == "Dark"
        text_col = (1,1,1,1) if is_dark else (0.4, 0.4, 0.4, 1)
        line_thick_col = (1,1,1,0.2) if is_dark else (0,0,0,0.6)
        
        # Time Label Container
        from kivymd.uix.floatlayout import MDFloatLayout
        time_box = MDFloatLayout(size_hint_x=None, width=dp(50))
        
        # :00 label at top
        time_box.add_widget(MDLabel(
            text=f"{hour:02d}:00",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=text_col,
            halign="right",
            pos_hint={'top': 1.0}
        ))
        self.add_widget(time_box)
        
        # Divider Lines and Vertical Task Container (Stacked)
        self.content_container = MDBoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2), padding=[0, dp(10)])
        self.content_container.bind(minimum_height=self.content_container.setter('height'))
        
        # Minimum row spacing
        def ensure_min_height(*args):
            if self.content_container.height < dp(60):
                self.content_container.height = dp(60)
        self.content_container.bind(height=ensure_min_height)
        
        with self.content_container.canvas.before:
            Color(*line_thick_col)
            self.hour_divider = Line(points=[], width=1.5)
            
        self.content_container.bind(pos=self.update_divider, size=self.update_divider)
        self.add_widget(self.content_container)

    def update_divider(self, *args):
        # Bind the thick timeline visually exactly parallel to the text label.
        top_y = self.content_container.y + self.content_container.height - dp(10)
        self.hour_divider.points = [self.content_container.x, top_y, self.content_container.right, top_y]
        
    def add_task(self, task_block):
        # Simply append without absolute floating mappings
        task_block.size_hint_x = 1.0
        self.content_container.add_widget(task_block)

class CalendarDayScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None

    def on_enter(self):
        self.app = App.get_running_app()
        if not hasattr(self.app, 'selected_calendar_date') or not self.app.selected_calendar_date:
            self.app.selected_calendar_date = datetime.now()
            
        self.display_date = self.app.selected_calendar_date
        self.load_view()
        self.fetch_and_render_tasks()

    def go_back(self, instance):
        self.app.switch_screen("calendar_month")

    def load_view(self):
        self.clear_widgets()
        
        main_layout = MDBoxLayout(orientation="vertical")
        main_layout.md_bg_color = self.app.theme_cls.bg_normal
        
        is_dark = (self.app.theme_cls.theme_style == "Dark")
        text_col = (1,1,1,1) if is_dark else (0,0,0,1)

        # 1. Top Bar
        header_bar = MDBoxLayout(size_hint_y=None, height=dp(64), padding=[dp(10), dp(10)])
        header_bar.add_widget(MDIconButton(
            icon="arrow-left", 
            theme_text_color="Custom", text_color=text_col,
            on_release=self.go_back,
            pos_hint={'center_y': 0.5}
        ))
        
        title_text = self.display_date.strftime("%A, %d %B %Y")
        header_bar.add_widget(MDLabel(
            text=title_text, 
            font_style="H6", 
            theme_text_color="Custom", text_color=text_col, 
            pos_hint={'center_y': 0.5},
            bold=True
        ))
        
        main_layout.add_widget(header_bar)

        # 2. Daily Timeline ScrollView
        self.scroll = ScrollView(bar_width=dp(4))
        self.timeline_layout = MDBoxLayout(orientation="vertical", size_hint_y=None)
        self.timeline_layout.bind(minimum_height=self.timeline_layout.setter('height'))
        
        # Initialize Hour Rows 00:00 to 23:00
        self.hour_rows = {}
        for h in range(24):
            hr = HourRow(hour=h)
            self.hour_rows[h] = hr
            self.timeline_layout.add_widget(hr)
            
        # Add Red Line for current time
        self.time_line = MDBoxLayout(size_hint_y=None, height=dp(2), md_bg_color=(1, 0, 0, 1), opacity=0)
        self.add_widget(self.time_line) # Will be moved inside timeline in update loop
            
        self.scroll.add_widget(self.timeline_layout)
        main_layout.add_widget(self.scroll)
        
        self.add_widget(main_layout)
        
        # Start Red Line update loop
        from kivy.clock import Clock
        Clock.schedule_interval(self.update_time_line, 30)
        Clock.schedule_once(self.update_time_line)

    def fetch_and_render_tasks(self):
        # Clear existing tasks
        for h in range(24):
            self.hour_rows[h].content_container.clear_widgets()

        if not hasattr(self, 'app') or not self.app.db_path: return
        rows = list_tasks(self.app.db_path)
        
        target_year = self.display_date.year
        target_month = self.display_date.month
        target_day = self.display_date.day
        
        for row in rows:
            if len(row) >= 8:
                try:
                    # Parsing varies by row length (due to migrations)
                    # Safe index extraction
                    tid = row[0]
                    ct = row[1]
                    nonce = row[2]
                    due_str = row[3]
                    prio = row[4]
                    notified = row[5]
                    created = row[6] if len(row) > 6 else ""
                    completed = row[7] if len(row) > 7 else None
                    category = row[8] if len(row) > 8 else ""
                    sound = row[9] if len(row) > 9 else "Default"
                    desc = row[10] if len(row) > 10 else ""
                    is_overdue_flag = row[11] if len(row) > 11 else 0                    
                    if not due_str:
                        continue
                        
                    dt = datetime.fromisoformat(due_str)
                    
                    if dt.date() == datetime(target_year, target_month, target_day).date():
                        try:
                            # Use current derived_key if available, else attempt to reload (rare)
                            key = self.app.derived_key
                            if not key:
                                from backend.storage import load_accounts_meta, ensure_account
                                # fallback logic omitted for brevity as app should have key
                                pass
                            title = decrypt_bytes(ct, nonce, key).decode("utf-8").split("\n")[0]
                        except Exception as e:
                            Logger.error(f"Calendar: Task decryption failed ID {tid}: {e}")
                            title = "[Decryption Error]"
                        
                        task_data = {
                            "id": tid,
                            "title": title,
                            "due": due_str,
                            "prio": prio,
                            "category": category,
                            "ct": ct,
                            "nonce": nonce,
                            "desc": desc,
                            "completed": completed,
                            "notified": notified,
                            "is_overdue": is_overdue_flag
                        }
                        
                        tb = TaskBlock(task_data=task_data, callback=self.open_task_modal)
                        # Add to the appropriate hour segment
                        self.hour_rows[dt.hour].add_task(tb)
                        
                except Exception as e:
                    print(f"Error parsing task in daily view: {e}")

    def update_time_line(self, *args):
        # Timeline logic suspended due to vertical stacking migration preventing absolute pos mappings
        if hasattr(self, 'time_line'):
            self.time_line.opacity = 0
            if self.time_line.parent:
                self.time_line.parent.remove_widget(self.time_line)

    def open_task_modal(self, task_data):
        if not task_data:
            return
            
        self.active_task_data = task_data
        
        try:
            current_dt = datetime.fromisoformat(task_data['due'])
            time_str = current_dt.strftime("%I:%M %p")
            date_str = current_dt.strftime("%b %d, %Y")
        except:
            time_str = "Invalid Time"
            date_str = "Invalid Date"
            
        content = MDBoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        content.add_widget(MDLabel(text=f"{task_data.get('title', 'Untitled')}", font_style="H6", bold=True, size_hint_y=None, height=dp(40)))
        content.add_widget(MDLabel(text=f"Date: {date_str}", size_hint_y=None, height=dp(20)))
        content.add_widget(MDLabel(text=f"Time: {time_str}", size_hint_y=None, height=dp(20)))
        
        prio = task_data.get('prio', 3)
        prio_map = {1: "High", 2: "Medium", 3: "Low"}
        content.add_widget(MDLabel(text=f"Priority: {prio_map.get(prio, 'Medium')}", size_hint_y=None, height=dp(20)))
        
        status = task_data.get('status', 'active')
        if status == 'completed':
            content.add_widget(MDLabel(text="Status: Completed", theme_text_color="Custom", text_color=(0, 0.6, 0, 1), size_hint_y=None, height=dp(20)))
            
        self.task_dialog = MDDialog(
            title="Task Details",
            type="custom",
            content_cls=content,
            buttons=[MDFlatButton(text="CLOSE", theme_text_color="Primary", on_release=lambda *args: self.task_dialog.dismiss() if hasattr(self, 'task_dialog') and self.task_dialog else None)]
        )
        self.task_dialog.open()

    def do_snooze(self, tid, mins):
        from backend.storage import snooze_task
        app = App.get_running_app()
        snooze_task(app.db_path, tid, mins)
        if hasattr(self, "task_dialog") and self.task_dialog: self.task_dialog.dismiss()
        
        from kivymd.toast import toast
        toast(f"Task snoozed for {mins} minutes.")
        
        self.load_view()
        self.fetch_and_render_tasks()

    def do_dismiss(self, tid):
        from backend.storage import dismiss_notification
        app = App.get_running_app()
        dismiss_notification(app.db_path, tid)
        if hasattr(self, "task_dialog") and self.task_dialog: self.task_dialog.dismiss()
        
        from kivymd.toast import toast
        toast("Task alert dismissed.")
        
        self.load_view()
        self.fetch_and_render_tasks()

    def close_task_detail(self, *args):
        if hasattr(self, "task_dialog") and self.task_dialog:
            self.task_dialog.dismiss()
