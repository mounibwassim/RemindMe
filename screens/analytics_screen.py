from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton
from kivymd.uix.card import MDCard
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.metrics import dp
from datetime import datetime, timedelta
import sqlite3
import threading
from kivy.clock import Clock
from kivy.app import App
from kivymd.app import MDApp
from functools import partial
from kivymd.uix.behaviors import RectangularRippleBehavior
from kivymd.uix.widget import MDWidget
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.tooltip import MDTooltip
from kivymd.toast import toast
from utils.ui_components import ClickableCard
from backend.stats_service import get_task_counts_formula, get_weekly_completion_distribution, get_priority_distribution

class ClickableBar(ButtonBehavior, RectangularRippleBehavior, MDBoxLayout, MDTooltip):
    def __init__(self, count, day_label, **kwargs):
        super().__init__(**kwargs)
        self.count = count
        self.day_label = day_label
        self.ripple_behavior = True
        self.radius = [4, 4, 4, 4]
        # Tooltip text: Show Created
        self.tooltip_text = f"{day_label}: {count} tasks created"
        self.tooltip_bg_color = (0.2, 0.6, 1, 1) # Blue tooltip
        self.tooltip_text_color = (1, 1, 1, 1)

    def on_release(self):
        toast(f"{self.day_label}: {self.count} tasks")

class AnalyticsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.week_offset = 0 
        self.chart_container = None
        self.week_range_lbl = None

    def on_enter(self):
        self.app = App.get_running_app()
        self.week_offset = 0 
        try:
            self.load_view()
        except Exception as e:
            print(f"Analytics crash: {e}")

    def load_view(self):
        self.clear_widgets()
        
        # ROOT LAYOUT
        self.root_layout = MDBoxLayout(orientation="vertical")
        self.root_layout.md_bg_color = self.app.theme_cls.bg_normal
        self.add_widget(self.root_layout)
        
        # 1. HEADER (Static)
        self.build_header()
        
        # 2. CONTENT CONTAINER (To be filled async)
        self.scroll = ScrollView(bar_width=0)
        self.content_box = MDBoxLayout(orientation="vertical", spacing=dp(20), padding=dp(20), size_hint_y=None)
        self.content_box.bind(minimum_height=self.content_box.setter('height'))
        self.scroll.add_widget(self.content_box)
        self.root_layout.add_widget(self.scroll)
        
        # Show Loading Spinner or Label
        self.loading_lbl = MDLabel(text="Loading Analytics...", halign="center", theme_text_color="Hint")
        self.content_box.add_widget(self.loading_lbl)
        
        # Start Async Fetch
        threading.Thread(target=self.bg_fetch_data, daemon=True).start()

    def build_header(self):
        header_card = MDCard(
            size_hint_y=None, 
            height=dp(100), 
            radius=[0, 0, 20, 20], 
            elevation=4,
            md_bg_color=App.get_running_app().theme_cls.primary_color
        )
        
        header_content = MDBoxLayout(orientation="vertical", padding=[dp(20), dp(10), dp(20), dp(20)])
        
        top_row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40))
        top_row.add_widget(MDIconButton(icon="arrow-left", on_release=self.go_back, theme_text_color="Custom", text_color=(1,1,1,1)))
        
        title_box = MDBoxLayout(orientation="vertical", pos_hint={'center_y': 0.5})
        title_box.add_widget(MDLabel(
            text="Analytics", 
            font_style="H5", 
            bold=True, 
            theme_text_color="Custom", 
            text_color=(1,1,1,1), 
            halign="center"
        ))
        top_row.add_widget(title_box)
        
        top_row.add_widget(MDIconButton(icon="chart-bar", theme_text_color="Custom", text_color=(1,1,1,1)))
        header_content.add_widget(top_row)
        
        self.week_range_lbl = MDLabel(text="...", font_style="Subtitle1", theme_text_color="Custom", text_color=(0.9, 0.9, 0.9, 1), halign="center")
        header_content.add_widget(self.week_range_lbl)
        
        header_card.add_widget(header_content)
        self.root_layout.add_widget(header_card, index=1) 

    def bg_fetch_data(self):
        try:
            # Current Week Range (Monday-Sunday)
            now = datetime.now()
            start_week_dt = now - timedelta(days=now.weekday())
            start_week_dt = start_week_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            end_week_dt = start_week_dt + timedelta(days=7)
            
            start_iso = start_week_dt.isoformat()
            end_iso = end_week_dt.isoformat()
            
            # Use centralized service with Week filter for Cards
            comp, pend, upc, total = get_task_counts_formula(self.app.db_path, start_iso=start_iso, end_iso=end_iso)
            
            # Priority distribution for this week
            prio_dist = get_priority_distribution(self.app.db_path, start_iso=start_iso, end_iso=end_iso)
            
            # Weekly stats for chart (respects week_offset)
            week_data = self.calculate_weekly_stats(self.week_offset)
            
            # Compute Rate based on this week's data
            rate = int((comp / (comp + pend)) * 100) if (comp + pend) > 0 else 0
            
            stats = {
                'total': total,
                'completed': comp,
                'pending': pend,
                'upcoming': upc,
                'rate': rate,
                'high': prio_dist[1],
                'medium': prio_dist[2],
                'low': prio_dist[3]
            }
            
            Clock.schedule_once(partial(self.update_ui_with_data, stats, week_data, None))
        except Exception as e:
            import traceback
            err = traceback.format_exc()
            Clock.schedule_once(lambda dt: self.show_error(f"Err: {e}\n{err}"))
            
    def show_error(self, error_msg):
        if hasattr(self, 'content_box'):
            self.content_box.clear_widgets()
            self.content_box.add_widget(MDLabel(text=f"Error loading data:\n{error_msg}", halign="center", theme_text_color="Error"))

    def update_ui_with_data(self, stats, week_data, _, dt):
        if not hasattr(self, 'content_box'): return
        self.content_box.clear_widgets()
        
        is_dark = (self.app.theme_cls.theme_style == "Dark")
        card_bg = (0.18, 0.18, 0.18, 1) if is_dark else (1, 1, 1, 1)
        text_primary = (1, 1, 1, 1) if is_dark else (0, 0, 0, 1)
        text_secondary = (0.7, 0.7, 0.7, 1) if is_dark else (0.5, 0.5, 0.5, 1)
        
        # 1. WEEKLY SUMMARY CARDS
        cards_scroll = ScrollView(size_hint_y=None, height=dp(110), do_scroll_x=True, do_scroll_y=False)
        cards_layout = MDBoxLayout(orientation="horizontal", spacing=dp(15), size_hint_x=None, padding=[dp(5), dp(5), dp(5), dp(5)])
        cards_layout.bind(minimum_width=cards_layout.setter('width'))
        
        cards_layout.add_widget(self.create_summary_card("Total Tasks", str(stats['total']), "format-list-bulleted", card_bg, text_primary))
        cards_layout.add_widget(self.create_summary_card("Completed", str(stats['completed']), "check-circle", card_bg, text_primary))
        cards_layout.add_widget(self.create_summary_card("Pending", str(stats['pending']), "clock-alert-outline", card_bg, text_primary))
        cards_layout.add_widget(self.create_summary_card("Upcoming", str(stats['upcoming']), "calendar-clock", card_bg, text_primary))
        cards_layout.add_widget(self.create_summary_card("Rate", f"{stats['rate']}%", "percent", card_bg, text_primary))
        cards_layout.add_widget(self.create_summary_card("High Prio", str(stats['high']), "alert", card_bg, text_primary))
        
        cards_scroll.add_widget(cards_layout)
        self.content_box.add_widget(cards_scroll)
        
        # 2. WEEKLY PROGRESS CHARTS
        self.content_box.add_widget(MDLabel(text="Weekly Progress", font_style="H6", bold=True, size_hint_y=None, height=dp(30), theme_text_color="Custom", text_color=text_primary))
        
        chart_card = MDCard(orientation="vertical", size_hint_y=None, height=dp(250), radius=[15], elevation=2, padding=dp(15))
        chart_card.md_bg_color = card_bg
        
        nav = MDBoxLayout(size_hint_y=None, height=dp(40))
        nav.add_widget(MDIconButton(icon="chevron-left", on_release=self.prev_week, theme_text_color="Custom", text_color=text_secondary))
        nav.add_widget(MDLabel(text="Weekly Completion Overview", halign="center", font_style="Caption", theme_text_color="Custom", text_color=text_secondary))
        nav.add_widget(MDIconButton(icon="chevron-right", on_release=self.next_week, theme_text_color="Custom", text_color=text_secondary))
        chart_card.add_widget(nav)
        
        self.chart_container = MDBoxLayout(orientation="horizontal", spacing=dp(8), padding=[0, dp(10), 0, 0])
        chart_card.add_widget(self.chart_container)
        
        self.content_box.add_widget(chart_card)
        
        # Render initial chart data
        self.render_chart_bars(week_data)
        
        # 3. PRIORITY DISTRIBUTION
        self.content_box.add_widget(MDLabel(text="Priority Distribution", font_style="H6", bold=True, size_hint_y=None, height=dp(30), theme_text_color="Custom", text_color=text_primary))
        
        prio_layout = MDBoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(90))
        prio_layout.add_widget(self.create_prio_card("High", stats['high'], (1, 0.2, 0.2, 1), card_bg, text_primary))
        prio_layout.add_widget(self.create_prio_card("Medium", stats['medium'], (1, 0.8, 0, 1), card_bg, text_primary))
        prio_layout.add_widget(self.create_prio_card("Low", stats['low'], (0.2, 0.8, 0.2, 1), card_bg, text_primary))
        self.content_box.add_widget(prio_layout)
        
        # 4. AI INSIGHT CARD
        insight_msg = self.get_ai_insight(stats)
        
        insight_card = ClickableCard(
            orientation="vertical", 
            size_hint_y=None, 
            height=dp(100), 
            radius=[15], 
            elevation=1, 
            padding=dp(15),
            on_release=self.go_to_ai
        )
        insight_card.md_bg_color = (0.15, 0.2, 0.3, 1) if is_dark else (0.9, 0.95, 1, 1)
        
        insight_header = MDBoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(30))
        from kivymd.uix.label import MDIcon
        
        insight_header.add_widget(MDIcon(
            icon="robot", 
            theme_text_color="Custom", 
            text_color=(0.2, 0.6, 1, 1), 
            size_hint=(None, None), 
            size=(dp(24), dp(24)),
            pos_hint={'center_y': 0.5}
        ))
        
        insight_header.add_widget(MDLabel(
            text="AI Insight", 
            bold=True, 
            theme_text_color="Custom", 
            text_color=(0.2, 0.6, 1, 1),
            pos_hint={'center_y': 0.5},
            size_hint_y=None, height=dp(100)
        ))
        
        insight_card.add_widget(insight_header)
        
        insight_card.add_widget(MDLabel(
            text=insight_msg, 
            font_style="Body2", 
            theme_text_color="Custom", 
            text_color=text_secondary,
            valign="top"
        ))
        
        self.content_box.add_widget(insight_card)
        
    def get_ai_insight(self, stats):
        from backend.ai_assistant import generate_weekly_insight
        from datetime import datetime, timedelta
        
        now = datetime.now()
        start_dt = now - timedelta(days=now.weekday())  # Monday of current week
        start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Map stats for AI engine requirements
        total = stats.get('total', 0)
        completed = stats.get('completed', 0)
        
        # Gather audit metrics if possible mapping
        try:
            from backend.storage import get_audit_stats_since
            audit_stats = get_audit_stats_since(self.app.db_path, start_dt)
            snoozed = audit_stats.get('snoozed_events', 0)
            sent = audit_stats.get('notifications_sent', 0)
        except:
            snoozed = 0
            sent = 0

        insight_text = generate_weekly_insight(self.app.db_path, start_dt, completed, total, snoozed, sent)
        return insight_text

    def create_summary_card(self, title, value, icon, bg_color, text_color):
        card = MDCard(orientation="vertical", size_hint=(None, None), size=(dp(100), dp(100)), radius=[12], elevation=2, padding=dp(10))
        card.md_bg_color = bg_color
        
        from kivymd.uix.label import MDIcon
        card.add_widget(MDIcon(icon=icon, theme_text_color="Custom", text_color=(0.2, 0.6, 1, 1), halign="left"))
        card.add_widget(MDWidget()) # Spacer
        card.add_widget(MDLabel(text=value, font_style="H5", bold=True, theme_text_color="Custom", text_color=text_color))
        card.add_widget(MDLabel(text=title, font_style="Caption", theme_text_color="Custom", text_color=(0.5, 0.5, 0.5, 1)))
        return card

    def create_prio_card(self, title, value, color, bg_color, text_color):
        card = MDCard(orientation="vertical", size_hint_y=None, height=dp(80), radius=[12], elevation=2, padding=dp(10))
        card.md_bg_color = bg_color
        
        from kivymd.uix.label import MDIcon
        row = MDBoxLayout(spacing=dp(5))
        row.add_widget(MDIcon(icon="circle", theme_text_color="Custom", text_color=color, font_size="10sp"))
        row.add_widget(MDLabel(text=title, font_style="Caption", theme_text_color="Custom", text_color=(0.5, 0.5, 0.5, 1)))
        card.add_widget(row)
        
        card.add_widget(MDLabel(text=str(value), font_style="H5", bold=True, halign="center", theme_text_color="Custom", text_color=text_color))
        return card

    def update_weekly_chart(self):
        # Triggered by nav buttons, async update
        threading.Thread(target=self.bg_update_chart, daemon=True).start()
        
    def bg_update_chart(self):
        try:
            week_data = self.calculate_weekly_stats(self.week_offset)
            Clock.schedule_once(partial(self.render_chart_bars, week_data))
        except Exception as e:
            # Just ignore chart errors or log, to prevent crash
            pass

    def render_chart_bars(self, week_data, dt=None):
        if not self.chart_container: return
        self.chart_container.clear_widgets()
        
        # Update Range Label
        if self.week_range_lbl:
            self.week_range_lbl.text = f"{week_data['date_range_label']}"
            
        # Draw Bars
        max_val = max(week_data['week_completed']) if week_data['week_completed'] else 5
        if max_val < 5: max_val = 5
        
        is_dark = (self.app.theme_cls.theme_style == "Dark")
        label_color = (0.9, 0.9, 0.9, 1) if is_dark else (0.2, 0.2, 0.2, 1)
        
        for i in range(7):
            val = week_data['week_completed'][i] 
            label = week_data['week_labels'][i]
            
            bar_col = MDBoxLayout(orientation="vertical", spacing=dp(5))
            
            # Bar Area
            bar_area = MDBoxLayout(orientation="vertical")
            
            if val < max_val:
                bar_area.add_widget(MDWidget(size_hint_y=(max_val - val)/max_val))
                
            if val > 0:
                bar = ClickableBar(count=val, day_label=label, size_hint_y=(val/max_val))
                bar.md_bg_color = (0.2, 0.6, 1, 1) 
                bar_area.add_widget(bar)
            else:
                bar_area.add_widget(MDBoxLayout(size_hint_y=None, height=dp(2), md_bg_color=(0.5, 0.5, 0.5, 1)))
            
            bar_col.add_widget(bar_area)
            bar_col.add_widget(MDLabel(text=label, halign="center", font_style="Caption", size_hint_y=None, height=dp(15), theme_text_color="Custom", text_color=label_color))
            
            self.chart_container.add_widget(bar_col)

    def calculate_weekly_stats(self, week_offset=0):
        if not self.app.db_path:
            return {'week_labels': [], 'week_completed': [], 'date_range_label': ''}
            
        dist = get_weekly_completion_distribution(self.app.db_path, week_offset)
        
        return {
            'week_labels': dist['labels'], 
            'week_completed': dist['counts'], 
            'date_range_label': dist['range']
        }

    def prev_week(self, instance):
        self.week_offset += 1
        self.update_weekly_chart()

    def next_week(self, instance):
        self.week_offset -= 1
        self.update_weekly_chart()

    def go_to_ai(self, instance):
        self.app.switch_screen("ai")

    def go_back(self, instance):
        self.app.switch_screen("dashboard")
