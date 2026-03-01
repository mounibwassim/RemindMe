from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton
from kivy.graphics import Color, Rectangle, RoundedRectangle
from datetime import datetime, timedelta
import calendar
from kivymd.app import MDApp
from kivy.app import App
from kivy.metrics import dp
from kivymd.uix.floatlayout import MDFloatLayout

from backend.storage import list_tasks
from backend.crypto import decrypt_bytes

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
                app = App.get_running_app()
                if app.theme_cls.theme_style == "Dark":
                    Color(0.2, 0.2, 0.2, 1)
                else:
                    Color(0.95, 0.95, 0.95, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
            
        self.bind(pos=self.update_rect, size=self.update_rect)
        
        app = App.get_running_app()
        is_dark = (app.theme_cls.theme_style == "Dark")
        text_col = (1,1,1,1) if is_dark else (0,0,0,1)

        # Day Number - Pinned to TOP CENTER with larger font
        self.add_widget(MDLabel(
            text=str(day), 
            halign="center", 
            font_size="20sp", # Google-style readable numbers
            bold=True,
            theme_text_color="Custom",
            text_color=text_col,
            pos_hint={'center_x': 0.5, 'top': 0.95},
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
                size=(dp(24), dp(24)),
                pos_hint={'center_x': 0.5, 'y': 0.1}
            )
            # Badge Background
            with badge.canvas.before:
                Color(0.2, 0.6, 1, 1) # Blue
                RoundedRectangle(pos=badge.pos, size=badge.size, radius=[12])
                
            def update_badge_bg(instance, value):
                instance.canvas.before.clear()
                with instance.canvas.before:
                    Color(0.2, 0.6, 1, 1)
                    RoundedRectangle(pos=instance.pos, size=instance.size, radius=[instance.height/2.0])
            badge.bind(pos=update_badge_bg, size=update_badge_bg)
            
            self.add_widget(badge)

        self.bind(on_touch_down=self.on_touch)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_touch(self, instance, touch):
        if self.collide_point(*touch.pos):
            self.callback(self.day)
            return True
        return False

class CalendarMonthScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_date = datetime.now()
        
    def on_enter(self):
        self.app = App.get_running_app()
        self.current_date = datetime.now()
        self.load_view()

    def on_touch_down(self, touch):
        if self.manager and self.manager.current != self.name:
            return super().on_touch_down(touch)
        self._touch_x = touch.x
        return super().on_touch_down(touch)
        
    def on_touch_up(self, touch):
        if self.manager and self.manager.current != self.name:
            return super().on_touch_up(touch)
        if hasattr(self, '_touch_x'):
            dx = touch.x - self._touch_x
            if dx > 100: # Swipe Right -> Prev
                self.prev_month(None)
                return True
            elif dx < -100: # Swipe Left -> Next
                self.next_month(None)
                return True
            # Clear touch after processing
            delattr(self, '_touch_x')
        return super().on_touch_up(touch)

    def load_view(self):
        self.clear_widgets()
        
        main_layout = MDBoxLayout(orientation="vertical")
        main_layout.md_bg_color = self.app.theme_cls.bg_normal
        
        is_dark = (self.app.theme_cls.theme_style == "Dark")
        text_col = (1,1,1,1) if is_dark else (0,0,0,1)

        # 1. Top Bar / App Bar equivalent
        header_bar = MDBoxLayout(size_hint_y=None, height=dp(64), padding=[dp(10), dp(10)])
        header_bar.add_widget(MDIconButton(
            icon="arrow-left", 
            theme_text_color="Custom", text_color=text_col,
            on_release=lambda x: self.app.switch_screen("dashboard"),
            pos_hint={'center_y': 0.5}
        ))
        header_bar.add_widget(MDLabel(
            text="Calendar", 
            font_style="H6", 
            theme_text_color="Custom", text_color=text_col, 
            pos_hint={'center_y': 0.5}
        ))
        
        main_layout.add_widget(header_bar)

        # 2. Month Selector
        month_header = BoxLayout(size_hint_y=None, height=dp(60), padding=dp(10), spacing=dp(10))
        
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
        
        month_header.add_widget(prev_btn)
        month_header.add_widget(self.month_label)
        month_header.add_widget(next_btn)
        
        main_layout.add_widget(month_header)

        # 3. Days of week header
        days_header = GridLayout(cols=7, size_hint_y=None, height=dp(40))
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for day in days:
            days_header.add_widget(MDLabel(
                text=day, 
                halign="center", 
                bold=True, 
                theme_text_color="Hint",
                font_style="Subtitle2"
            ))
        main_layout.add_widget(days_header)

        # 4. Grid Container (75-85% height logic achieved by giving it size_hint=1)
        grid_container = MDBoxLayout(padding=dp(10))
        self.grid = GridLayout(cols=7, spacing=dp(10)) # 8-12dp spacing requirement
        
        self.refresh_grid()
        
        grid_container.add_widget(self.grid)
        main_layout.add_widget(grid_container)
        
        self.add_widget(main_layout)

    def refresh_grid(self):
        self.grid.clear_widgets()
        
        year = self.current_date.year
        month = self.current_date.month
        
        tasks_doc = self.get_tasks_for_month(year, month)
        
        cal = calendar.monthcalendar(year, month)
        today = datetime.now()
        
        for week in cal:
            for day in week:
                if day == 0:
                    # Empty cell
                    self.grid.add_widget(MDBoxLayout())
                else:
                    is_today = (day == today.day and month == today.month and year == today.year)
                    key = f"{year}-{month:02d}-{day:02d}"
                    count = len(tasks_doc.get(key, []))
                    
                    cell = CalendarCell(
                        day=day, 
                        count=count, 
                        is_today=is_today,
                        on_press_callback=self.on_day_press
                    )
                    self.grid.add_widget(cell)

    def prev_month(self, instance):
        first = self.current_date.replace(day=1)
        prev = first - timedelta(days=1)
        self.current_date = prev.replace(day=1)
        self.load_view()

    def next_month(self, instance):
        last = calendar.monthrange(self.current_date.year, self.current_date.month)[1]
        last_day = self.current_date.replace(day=last)
        next_date = last_day + timedelta(days=1)
        self.current_date = next_date.replace(day=1)
        self.load_view()

    def get_tasks_for_month(self, year, month):
        month_tasks = {}
        if not hasattr(self, 'app') or not self.app.db_path: return month_tasks
        rows = list_tasks(self.app.db_path)
        
        for row in rows:
            if len(row) >= 8:
                try:
                    due_str = row[3]
                    if not due_str:
                        continue
                    dt = datetime.fromisoformat(due_str)
                    
                    if dt.year == year and dt.month == month:
                        key = f"{year}-{month:02d}-{dt.day:02d}"
                        if key not in month_tasks: month_tasks[key] = []
                        month_tasks[key].append(row)
                except:
                    pass
        return month_tasks

    def on_day_press(self, day):
        # selected date -> switch to Daily View
        selected_date = self.current_date.replace(day=day)
        self.app.selected_calendar_date = selected_date
        self.app.switch_screen("calendar_day")
