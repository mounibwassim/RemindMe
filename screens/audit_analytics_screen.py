from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDRaisedButton, MDFlatButton, MDFillRoundFlatIconButton
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.dialog import MDDialog
from kivymd.app import MDApp
from kivy.app import App
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.uix.scrollview import ScrollView
from kivymd.uix.list import MDList, TwoLineAvatarIconListItem, IconLeftWidget
from kivy.properties import StringProperty, ColorProperty, NumericProperty
from kivy.graphics import Color, RoundedRectangle
from kivymd.uix.widget import MDWidget
from kivy.uix.widget import Widget
from datetime import datetime, timedelta
import calendar
import requests
import random
import os

from backend.storage import get_audit_stats, get_metric_details
from backend.stats_service import get_weekly_completion_distribution, get_monthly_completed_count, get_task_counts_formula, get_monthly_stats

from utils.ui_components import ClickableCard

class ModernAnalyticsCard(ClickableCard):
    icon = StringProperty("circle")
    title = StringProperty("Metric")
    value = StringProperty("0")
    color = ColorProperty([0, 0, 1, 1])
    progress = NumericProperty(0)
    metric_type = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(140) # Fixed height for cards
        self.padding = dp(16)
        self.spacing = dp(8)
        self.radius = [16]
        self.elevation = 0  # Disable elevation to prevent KivyMD shadow bugs
        
        # Theme check
        app = App.get_running_app()
        is_dark = (app.theme_cls.theme_style == "Dark")
        self.md_bg_color = app.theme_cls.bg_normal if not is_dark else (0.15, 0.15, 0.18, 1)
        text_col = (1, 1, 1, 1) if is_dark else (0.1, 0.1, 0.1, 1)

        # Row: Icon + Title
        header = MDBoxLayout(orientation="horizontal", spacing=dp(12), size_hint_y=None, height=dp(30))
        
        from kivymd.uix.label import MDIcon
        self.icon_widget = MDIcon(
            icon=self.icon,
            theme_text_color="Custom",
            text_color=self.color,
            font_size=dp(24),
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            pos_hint={'center_y': 0.5}
        )
        header.add_widget(self.icon_widget)
        
        header.add_widget(MDLabel(
            text=self.title.upper(),
            font_style="Caption",
            theme_text_color="Custom",
            text_color=(0.5, 0.5, 0.5, 1),
            valign="center",
            bold=True,
            size_hint_y=None,
            height=dp(40), # Fixed or dynamic height replacement
            pos_hint={'center_y': 0.5}
        ))
        self.add_widget(header)
        
        # Spacer
        self.add_widget(MDWidget(size_hint_y=None, height=dp(4)))
        
        # Value
        self.val_label = MDLabel(
            text=str(self.value),
            font_style="H4",
            bold=True,
            theme_text_color="Custom",
            text_color=text_col,
            size_hint_y=None,
            height=dp(40)
        )
        self.add_widget(self.val_label)
        
        # Progress Bar
        self.add_widget(MDWidget(size_hint_y=None, height=dp(8)))
        self.pb = MDProgressBar(
            value=self.progress,
            color=self.color,
            back_color=(self.color[0], self.color[1], self.color[2], 0.2),
            size_hint_y=None,
            height=dp(4)
        )
        self.add_widget(self.pb)
        
    def on_release(self, *args):
        pass

class AuditAnalyticsScreen(MDScreen):
    insight_mode = StringProperty("Weekly")
    
    def on_enter(self):
        """Called every time the screen is displayed."""
        try:
            self.app = MDApp.get_running_app()
            self.load_view()
            self.refresh_data()
        except Exception as e:
            print("Audit crash:", e)
            self.clear_widgets()
            from kivymd.uix.label import MDLabel
            self.add_widget(MDLabel(text="No audit history yet.", halign="center"))

    def go_to_ai(self, instance):
        self.app.switch_screen("ai")
        
    def go_back(self, instance):
        self.app.switch_screen("settings")

    def set_insight_mode(self, mode):
        self.insight_mode = mode
        self.refresh_data()

    def get_current_start_dt(self):
        now = datetime.now()
        if self.insight_mode == "Weekly":
            start_dt = now - timedelta(days=now.weekday())
            return start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def show_card_details(self, card):
        metric = card.metric_type
        start_dt = self.get_current_start_dt()
        
        # Get detailed breakdown filtered by window
        details = get_metric_details(self.app.db_path, metric, start_dt)
        
        title = f"{card.title} Details"
        msg = f"Statistic: {card.value}\n\n"
        
        # Format Recent Events
        recent_text = ""
        if 'recent_events' in details and details['recent_events']:
            recent_text = "\n\nRecent Activity:\n"
            for ts_iso in details['recent_events']:
                try:
                    if isinstance(ts_iso, tuple): # For Snoozed (ts, extra)
                        dt = datetime.fromisoformat(ts_iso[0])
                        # Timestamps are stored as local naive via datetime.now() — display directly
                        extra = f" ({ts_iso[1]})" if ts_iso[1] else ""
                        recent_text += f"- {dt.strftime('%b %d, %I:%M %p')}{extra}\n"
                    else:
                        dt = datetime.fromisoformat(ts_iso)
                        # Timestamps are stored as local naive via datetime.now() — display directly
                        recent_text += f"- {dt.strftime('%b %d, %I:%M %p')}\n"
                except:
                    pass
            recent_text += "..." if len(details['recent_events']) >= 5 else ""

        if metric == 'completed_tasks':
            comp = details.get('total_completed', 0)
            created = details.get('total_created', 0)
            rate = details.get('completion_rate', 0)
            msg = (f"Completed in this period: {comp}\n"
                   f"Created in this period: {created}\n"
                   f"Completion Rate: {rate}%\n"
                   f"{recent_text}")
                   
        elif metric == 'notifications_sent':
            sent = details.get('total', 0)
            msg = (f"Sent in this period: {sent}\n"
                   f"History:\n")
            if 'daily_breakdown' in details and details['daily_breakdown']:
                for day, count in details['daily_breakdown']:
                     msg += f"- {day}: {count}\n"
            else:
                msg += "No recent activity."
                
        elif metric == 'snoozed_events':
            snoozed = details.get('total_snoozed', 0)
            msg = (f"Snoozed in this period: {snoozed}\n"
                   f"{recent_text}")
            if 'common_durations' in details and details['common_durations']:
                msg += "\n\nCommon Snooze Times:\n"
                for dur, count in details['common_durations']:
                    msg += f"- {dur}: {count} times\n"

        elif metric == 'notifications_opened':
            opened = details.get('total_opened', 0)
            sent = details.get('total_sent', 0)
            rate = details.get('open_rate', 0)
            msg = (f"Opened in this period: {opened}\n"
                   f"Total Sent: {sent}\n"
                   f"Open Rate: {rate}%\n"
                   f"{recent_text}")

        self.dialog = MDDialog(
            title=title,
            text=msg,
            buttons=[
                MDRaisedButton(text="OK", on_release=lambda x: self.dialog.dismiss())
            ]
        )
        self.dialog.open()

    def refresh_data(self):
        import threading
        from kivy.clock import Clock
        threading.Thread(target=self._bg_refresh_data, daemon=True).start()

    def _bg_refresh_data(self):
        from kivy.clock import Clock
        start_dt = self.get_current_start_dt()
        now = datetime.now()
        
        # UI Updates (Colors/Labels)
        active_color = self.app.theme_cls.primary_color
        inactive_color = (0, 0, 0, 0)
        inactive_text = active_color if (self.app.theme_cls.theme_style=="Light") else (1,1,1,1)
        
        if self.insight_mode == "Weekly":
            end_dt = start_dt + timedelta(days=6)
            date_str = f"{start_dt.strftime('%b %d')} - {end_dt.strftime('%b %d')}"
            if hasattr(self, 'period_label'):
                self.period_label.text = f"Weekly Overview ({date_str})"
            
            # Buttons
            if hasattr(self, 'btn_weekly'):
                self.btn_weekly.md_bg_color = active_color
                self.btn_weekly.text_color = (1, 1, 1, 1)
                self.btn_weekly.elevation = 6
                self.btn_weekly.icon_color = (1, 1, 1, 1)
                
                self.btn_monthly.md_bg_color = inactive_color
                self.btn_monthly.text_color = inactive_text
                self.btn_monthly.elevation = 0
                self.btn_monthly.icon_color = inactive_text
        else:
            month_name = now.strftime("%B")
            _, last_day = calendar.monthrange(now.year, now.month)
            if hasattr(self, 'period_label'):
                self.period_label.text = f"Monthly Overview ({month_name} 1 - {last_day})"
            
            # Buttons
            if hasattr(self, 'btn_monthly'):
                self.btn_monthly.md_bg_color = active_color
                self.btn_monthly.text_color = (1, 1, 1, 1)
                self.btn_monthly.elevation = 6
                self.btn_monthly.icon_color = (1, 1, 1, 1)
                
                self.btn_weekly.md_bg_color = inactive_color
                self.btn_weekly.text_color = inactive_text
                self.btn_weekly.elevation = 0
                self.btn_weekly.icon_color = inactive_text

        # Fetch Stats from Local SQL
        try:
            from backend.storage import get_audit_stats_since
            from backend.audit import get_audit_logs

            if self.insight_mode == "Weekly":
                start_week_dt = now - timedelta(days=now.weekday())
                start_week_dt = start_week_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                end_week_dt = start_week_dt + timedelta(days=7)
                
                # Single source for Weekly
                comp, pend, upc, created = get_task_counts_formula(
                    self.app.db_path, 
                    start_iso=start_week_dt.isoformat(), 
                    end_iso=end_week_dt.isoformat()
                )
                completed = comp
                
                # Audit still handles events
                audit_stats = get_audit_stats(self.app.db_path, days=7)
                snoozed = audit_stats.get('snoozed_events', 0)
                sent = audit_stats.get('notifications_sent', 0)
                opened = audit_stats.get('notifications_opened', 0)
            else:
                # Monthly stats manually tracked to 1st of month
                start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                if now.month == 12:
                    end_month = start_month.replace(year=now.year+1, month=1)
                else:
                    end_month = start_month.replace(month=now.month+1)
                    
                comp, pend, upc, total = get_task_counts_formula(
                    self.app.db_path,
                    start_iso=start_month.isoformat(),
                    end_iso=end_month.isoformat()
                )
                completed = comp
                created = total
                
                # Events for month
                start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                days_in_month = (now - start_month).days + 1
                audit_stats = get_audit_stats(self.app.db_path, days=days_in_month)
                snoozed = audit_stats.get('snoozed_events', 0)
                sent = audit_stats.get('notifications_sent', 0)
                opened = audit_stats.get('notifications_opened', 0)
            
            local_rows = get_audit_logs(self.app.db_path, limit=20)
            logs = []
            for row in local_rows:
                logs.append({
                    "action": row[2],
                    "task_title": f"Task {row[1]}",
                    "timestamp": row[3],
                    "extra": row[5] or ""
                })

        except Exception as e:
            from kivy.logger import Logger
            Logger.error(f"Audit data fetch error: {e}")
            created = completed = snoozed = sent = opened = 0
            logs = []
        
        # Schedule UI update on main thread
        Clock.schedule_once(lambda dt: self._update_ui_results(completed, created, sent, snoozed, opened, logs))

    def _update_ui_results(self, completed, created, sent, snoozed, opened, logs, dt=0):
        # Update Cards
        if hasattr(self, 'card_completed'):
            self.card_completed.val_label.text = str(completed)
            rate = int((completed / created * 100)) if created > 0 else 0
            self.card_completed.pb.value = rate
            
        if hasattr(self, 'card_sent'):
            self.card_sent.val_label.text = str(sent)
            self.card_sent.pb.value = 100 if sent > 0 else 0
            
        if hasattr(self, 'card_snoozed'):
            self.card_snoozed.val_label.text = str(snoozed)
            rate = int((snoozed / sent * 100)) if sent > 0 else 0
            self.card_snoozed.pb.value = rate
            
        if hasattr(self, 'card_opened'):
            self.card_opened.val_label.text = str(opened)
            op_rate = int((opened / sent * 100)) if sent > 0 else 0
            self.card_opened.pb.value = op_rate

        from backend.ai_assistant import generate_weekly_insight, generate_monthly_insight
        
        # AI Insight
        text = ""
        start_dt = self.get_current_start_dt()
        
        if self.insight_mode == "Weekly":
            text = generate_weekly_insight(self.app.db_path, start_dt, completed, created, snoozed, sent)
        else:
            text = generate_monthly_insight(self.app.db_path, start_dt, completed, created, snoozed, sent)

        if hasattr(self, 'ai_label'):
            self.ai_label.text = text

    def load_view(self):
        self.clear_widgets()
        is_dark = (self.app.theme_cls.theme_style == "Dark")
        
        root = MDBoxLayout(orientation="vertical")
        root.md_bg_color = self.app.theme_cls.bg_normal
        
        # --- HEADER ---
        header_card = MDCard(size_hint_y=None, height=dp(60), elevation=3)
        header_card.radius = [0, 0, 20, 20]
        header_card.md_bg_color = self.app.theme_cls.primary_color
        
        h_box = MDBoxLayout(padding=[dp(10), 0], spacing=dp(5))
        
        h_box.add_widget(MDIconButton(
            icon="arrow-left", theme_text_color="Custom", text_color=(1,1,1,1),
            on_release=self.go_back, pos_hint={'center_y': 0.5}, icon_size="20sp"
        ))
        
        h_box.add_widget(MDLabel(
            text="Audit Analytics", font_style="Subtitle1", bold=True,
            theme_text_color="Custom", text_color=(1,1,1,1),
            halign="center", pos_hint={'center_y': 0.5}
        ))
        
        h_box.add_widget(Widget(size_hint_x=None, width=dp(48)))
        header_card.add_widget(h_box)
        root.add_widget(header_card)
        
        # Scroll
        scroll = ScrollView(size_hint=(1, 1))
        
        # Content Layout
        content = MDBoxLayout(orientation="vertical", padding=[dp(20), dp(40), dp(20), dp(20)], spacing=dp(24), size_hint_y=None)
        content.md_bg_color = self.app.theme_cls.bg_normal
        content.bind(minimum_height=content.setter('height'))
        
        # --- AI INSIGHT CARD ---
        self.ai_card = MDCard(
            orientation="vertical", 
            padding=dp(20), 
            spacing=dp(10), 
            size_hint_y=None,
            elevation=0 # Zero elevation to prevent black shadows
        )
        self.ai_card.bind(minimum_height=self.ai_card.setter('height'))
        self.ai_card.radius = [16, 16, 16, 16]
        self.ai_card.md_bg_color = (0.1, 0.1, 0.15, 1) if is_dark else (0.92, 0.96, 1, 1)

        
        # AI Header Row
        ai_head = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(50))
        # Left Side (Icon + Title)
        from kivymd.uix.label import MDIcon
        left_box = MDBoxLayout(size_hint=(None, None), size=(dp(120), dp(50)), spacing=dp(12), pos_hint={'center_y': 0.5})
        left_box.add_widget(MDIcon(
            icon="robot", 
            theme_text_color="Custom", 
            text_color=self.app.theme_cls.primary_color, 
            font_size=dp(28),
            pos_hint={'center_y': 0.5}
        ))
        left_box.add_widget(MDLabel(
            text="AI INSIGHTS", 
            font_style="Subtitle2", 
            bold=True, 
            theme_text_color="Primary", 
            size_hint_y=None, 
            height=dp(30),
            pos_hint={'center_y': 0.5}
        ))
        ai_head.add_widget(left_box)
        
        # Spacer
        ai_head.add_widget(Widget())
        
        # Right Side (Toggles)
        toggle_box = MDBoxLayout(size_hint=(None, None), size=(dp(220), dp(50)), spacing=dp(8), pos_hint={'center_y': 0.5})
        self.btn_weekly = MDFillRoundFlatIconButton(
            text="Weekly", 
            icon="calendar-week",
            on_release=lambda x: self.set_insight_mode("Weekly"), 
            font_size="10sp", 
            size_hint_y=None, 
            height=dp(36)
        )
        self.btn_monthly = MDFillRoundFlatIconButton(
            text="Monthly", 
            icon="calendar-month",
            on_release=lambda x: self.set_insight_mode("Monthly"), 
            font_size="10sp", 
            size_hint_y=None, 
            height=dp(36)
        )
        toggle_box.add_widget(self.btn_weekly)
        toggle_box.add_widget(self.btn_monthly)
        ai_head.add_widget(toggle_box)
        
        self.ai_card.add_widget(ai_head)
        
        # AI Text
        self.ai_label = MDLabel(
            text="Analyzing...",
            font_style="Body2",
            theme_text_color="Primary",
            size_hint_y=None
        )
        self.ai_label.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1] + dp(20)))
        
        self.ai_card.add_widget(self.ai_label)
        
        content.add_widget(self.ai_card)
        
        # Spacer for Breathing Room
        content.add_widget(Widget(size_hint_y=None, height=dp(20)))
        
        # --- PERIOD LABEL ---
        self.period_label = MDLabel(
            text="Weekly Overview", 
            font_style="Subtitle2", 
            bold=True, 
            theme_text_color="Secondary", 
            size_hint_y=None,
            height=dp(30)
        )
        content.add_widget(self.period_label)
        
        # --- GRID OF CARDS ---
        grid = MDGridLayout(cols=2, spacing=dp(16), size_hint_y=None, height=dp(320))
        
        self.card_completed = ModernAnalyticsCard(
            icon="check-circle", title="Completed", value="0", color=(0.2, 0.8, 0.2, 1), progress=0, metric_type='completed_tasks'
        )
        self.card_completed.bind(on_release=lambda x: self.show_card_details(self.card_completed))

        self.card_sent = ModernAnalyticsCard(
            icon="bell-ring", title="Sent", value="0", color=(0.2, 0.6, 1, 1), progress=0, metric_type='notifications_sent'
        )
        self.card_sent.bind(on_release=lambda x: self.show_card_details(self.card_sent))

        self.card_snoozed = ModernAnalyticsCard(
            icon="clock-time-four", title="Snoozed", value="0", color=(1, 0.6, 0.2, 1), progress=0, metric_type='snoozed_events'
        )
        self.card_snoozed.bind(on_release=lambda x: self.show_card_details(self.card_snoozed))

        self.card_opened = ModernAnalyticsCard(
            icon="eye", title="Opened", value="0", color=(0.6, 0.2, 1, 1), progress=0, metric_type='notifications_opened'
        )
        self.card_opened.bind(on_release=lambda x: self.show_card_details(self.card_opened))

        
        grid.add_widget(self.card_completed)
        grid.add_widget(self.card_sent)
        grid.add_widget(self.card_snoozed)
        grid.add_widget(self.card_opened)
        
        content.add_widget(grid)
        
        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)
        
        # Initial Data
        self.refresh_data()

    def show_ticket_details(self, text_msg):
        self.dialog = MDDialog(
            title="Ticket Details",
            text=text_msg,
            buttons=[
                MDRaisedButton(text="CLOSE", on_release=lambda x: self.dialog.dismiss())
            ]
        )
        self.dialog.open()

