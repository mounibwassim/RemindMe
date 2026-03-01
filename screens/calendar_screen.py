from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineAvatarIconListItem, MDList, IconLeftWidget
from kivymd.uix.widget import MDWidget
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDSeparator
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle
from datetime import datetime, timedelta
import calendar
from kivymd.app import MDApp
from kivy.app import App
from kivy.metrics import dp

from backend.storage import list_tasks
from backend.crypto import decrypt_bytes
from backend.stats_service import get_weekly_completion_distribution, get_calendar_month_data

from kivymd.uix.floatlayout import MDFloatLayout

class CalendarCell(MDFloatLayout):
    def __init__(self, day, count, is_today, on_press_callback, **kwargs):
        super().__init__(**kwargs)
        self.day = day
        self.count = count
        self.is_today = is_today
        self.callback = on_press_callback
        
        # Background Logic
        with self.canvas.before:
            if is_today:
                Color(0.2, 0.6, 1, 0.3) # Light Blue
            else:
                app = MDApp.get_running_app()
                if app.theme_cls.theme_style == "Dark":
                    Color(0.2, 0.2, 0.2, 1)
                else:
                    Color(0.95, 0.95, 0.95, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
            
        self.bind(pos=self.update_rect, size=self.update_rect)
        
        app = App.get_running_app()
        is_dark = (app.theme_cls.theme_style == "Dark")
        text_col = (1,1,1,1) if is_dark else (0,0,0,1)

        # Day Number - Pinned to TOP CENTER
        self.add_widget(MDLabel(
            text=str(day), 
            halign="center", 
            font_size="20sp", # Increased font size
            bold=True,
            theme_text_color="Custom",
            text_color=text_col,
            pos_hint={'center_x': 0.5, 'top': 1},
            size_hint_y=None,
            height=dp(35)
        ))
        
        # Task Badge - Pinned to BOTTOM CENTER
        if count > 0:
            badge = MDLabel(
                text=f"{count}",
                halign="center",
                font_style="Caption",
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1),
                size_hint=(None, None),
                size=(dp(20), dp(20)),
                pos_hint={'center_x': 0.5, 'y': 0.1}
            )
            # Badge Background
            with badge.canvas.before:
                Color(0.2, 0.6, 1, 1) # Blue
                RoundedRectangle(pos=badge.pos, size=badge.size, radius=[10])
                
            # Bind background update
            def update_badge_bg(instance, value):
                instance.canvas.before.clear()
                with instance.canvas.before:
                    Color(0.2, 0.6, 1, 1)
                    RoundedRectangle(pos=instance.pos, size=instance.size, radius=[10])
            badge.bind(pos=update_badge_bg, size=update_badge_bg)
            
            self.add_widget(badge)

        # Make clickable
        self.bind(on_touch_down=self.on_touch)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_touch(self, instance, touch):
        if self.collide_point(*touch.pos):
            self.callback(self.day)
            return True
        return False

class CalendarScreen(BoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.app = app
        self.current_date = datetime.now()
        
        # Add background color
        with self.canvas.before:
            self.bg_color = Color()
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        
        self.bind(pos=self.update_bg, size=self.update_bg)
        self.update_theme_bg()
        self.load_view()

    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def update_theme_bg(self, *args):
        is_dark = (MDApp.get_running_app().theme_cls.theme_style == "Dark")
        self.bg_color.rgba = self.app.theme_cls.bg_normal

    def load_view(self):
        self.clear_widgets()
        
        # Header (Month Year | Prev | Next)
        header = BoxLayout(size_hint_y=None, height=60, padding=10, spacing=10)
        
        is_dark = (MDApp.get_running_app().theme_cls.theme_style == "Dark")
        text_col = (1,1,1,1) if is_dark else (0,0,0,1)

        self.month_label = MDLabel(
            text=self.current_date.strftime("%B %Y"),
            halign="center",
            font_style="H5",
            bold=True,
            theme_text_color="Custom",
            text_color=text_col
        )
        
        prev_btn = MDIconButton(icon="chevron-left", on_release=self.prev_month, size_hint=(None, None), size=(dp(48), dp(48)), pos_hint={'center_y': 0.5}, theme_text_color="Custom", text_color=text_col)
        next_btn = MDIconButton(icon="chevron-right", on_release=self.next_month, size_hint=(None, None), size=(dp(48), dp(48)), pos_hint={'center_y': 0.5}, theme_text_color="Custom", text_color=text_col)
        
        header.add_widget(prev_btn)
        header.add_widget(self.month_label)
        header.add_widget(next_btn)
        
        self.add_widget(header)
        
        # Days of Week Header
        days_header = GridLayout(cols=7, size_hint_y=None, height=40, padding=5)
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            days_header.add_widget(MDLabel(
                text=day, 
                halign="center", 
                bold=True,
                theme_text_color="Custom",
                text_color=text_col
            ))
        self.add_widget(days_header)
        
        # Calendar Grid Container
        self.grid = GridLayout(cols=7, padding=dp(10), spacing=dp(8), size_hint_y=0.75)
        self.add_widget(self.grid)
        
        # --- TASK LIST AREA (Filtering) ---
        self.add_widget(MDSeparator())
        self.filter_label = MDLabel(
            text="Select a date to see tasks",
            halign="center",
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(40),
            bold=True
        )
        self.add_widget(self.filter_label)
        
        self.scroll_tasks = MDScrollView()
        self.day_task_list = MDList()
        self.scroll_tasks.add_widget(self.day_task_list)
        self.add_widget(self.scroll_tasks)
        
        self.refresh_grid()

    def refresh_grid(self):
        self.grid.clear_widgets()
        
        year = self.current_date.year
        month = self.current_date.month
        cal = calendar.monthcalendar(year, month)
        
        # Fetch tasks
        tasks = self.get_tasks_for_month(year, month)
        
        for week in cal:
            for day in week:
                if day == 0:
                    self.grid.add_widget(MDLabel(text=""))
                else:
                    count = len(tasks.get(day, []))
                    is_today = (day == datetime.now().day and month == datetime.now().month and year == datetime.now().year)
                    cell = CalendarCell(day, count, is_today, self.show_tasks)
                    self.grid.add_widget(cell)

    def get_tasks_for_month(self, year, month):
        if not self.app.db_path: return {}
        
        # Consolidate via stats_service
        raw_dist = get_calendar_month_data(self.app.db_path, year, month)
        
        tasks_by_day = {}
        for day, items in raw_dist.items():
            tasks_by_day[day] = []
            for item in items:
                # Decrypt title in UI layer as stats_service shouldn't have encryption keys
                try:
                    title_desc = decrypt_bytes(item["ciphertext"], item["nonce"], self.app.derived_key)
                    title = title_desc.decode("utf-8").split("\n")[0]
                except:
                    title = "Error"
                
                tasks_by_day[day].append({
                    "id": item["id"],
                    "title": title,
                    "due": item["due"],
                    "completed": item["completed"],
                    "priority": item["priority"],
                    "category": item["category"]
                })
                
        return tasks_by_day

    def prev_month(self, instance):
        first = self.current_date.replace(day=1)
        prev = first - timedelta(days=1)
        self.current_date = prev
        self.month_label.text = self.current_date.strftime("%B %Y")
        self.refresh_grid()

    def next_month(self, instance):
        # Add 32 days to get to next month safely
        first = self.current_date.replace(day=1)
        next_month = first + timedelta(days=32)
        self.current_date = next_month
        self.month_label.text = self.current_date.strftime("%B %Y")
        self.refresh_grid()

    def show_tasks(self, day):
        self.on_date_selected(day)

    def on_date_selected(self, day):
        # Update label
        date_obj = self.current_date.replace(day=day)
        self.filter_label.text = f"Tasks for {date_obj.strftime('%b %d, %Y')}"
        
        # Filter tasks
        tasks = self.get_tasks_for_month(date_obj.year, date_obj.month).get(day, [])
        self.day_task_list.clear_widgets()
        
        if not tasks:
            self.day_task_list.add_widget(MDLabel(text="No tasks for this day.", halign="center", theme_text_color="Secondary", size_hint_y=None, height=dp(50)))
            return

        for t in tasks:
            status = "(Done)" if t['completed'] else f"({t['due'].split('T')[1][:5]})"
            
            # Priority color
            color = (0, 0.8, 0, 1) 
            if t['priority'] == 1: color = (1, 0.2, 0.2, 1)
            elif t['priority'] == 2: color = (1, 0.8, 0, 1)
            if t['completed']: color = (0.5, 0.5, 0.5, 1)

            item = TwoLineAvatarIconListItem(
                text=t['title'],
                secondary_text=f"{status} - {t['category']}",
                on_release=lambda x, task=t: self.show_task_details(task)
            )
            
            icon = "check-circle" if t['completed'] else "calendar-clock"
            item.add_widget(IconLeftWidget(icon=icon, theme_text_color="Custom", text_color=color))
            self.day_task_list.add_widget(item)

    def show_task_details(self, t):
        # Reuse logic or show simple dialog
        self.app.root.get_screen('dashboard').show_task_options(t)
