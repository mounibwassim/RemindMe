from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton, MDFillRoundFlatButton, MDFillRoundFlatIconButton, MDRoundFlatIconButton, MDRectangleFlatButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import MDList, OneLineAvatarIconListItem, IconLeftWidget, IconRightWidget
from kivymd.uix.scrollview import ScrollView
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.uix.widget import Widget
from datetime import datetime, timedelta
from kivy.app import App
from backend.storage import list_tasks, complete_task, delete_task, snooze_task, dismiss_notification, delete_all_completed_tasks
from backend.crypto import decrypt_bytes
from backend.audit import write_audit
from kivy.metrics import dp

from utils.ui_components import ClickableCard

class TaskCard(ClickableCard):
    def __init__(self, task_id, title, due, priority, category, notified, app, refresh_callback, description="", **kwargs):
        self.is_overdue = kwargs.pop('is_overdue', 0)
        super().__init__(**kwargs)
        self.orientation = "horizontal" # Changed to horizontal for better layout
        self.size_hint_y = None
        self.height = dp(80) 
        self.radius = [12]
        self.padding = 0 # Padding handled by inner boxes
        self.spacing = 0
        self.elevation = 1 
        
        self.task_id = task_id
        self.app = app
        self.refresh_callback = refresh_callback
        self.title = title
        self.due = due
        self.prio = priority
        self.cat = category
        self.description = description
        self.notified = notified
        
        # Priority mapping — PERMANENT, never overridden by overdue state
        prio_map = {
            1: (1, 0.2, 0.2, 1),    # High  - Red
            2: (1, 0.8, 0, 1),      # Med   - Yellow
            3: (0.2, 0.8, 0.2, 1)   # Low   - Green
        }
        # prio_color is ONLY for the left bar and priority icon — NEVER modified
        self.prio_color = prio_map.get(priority, (0.2, 0.8, 0.2, 1))
        
        # DEFAULT Container Variables
        self.md_bg_color = (1, 1, 1, 1)  # Normal Background
        if not app:  # Safe fallback
            is_dark = False
        else:
            is_dark = getattr(app.theme_cls, 'theme_style', "Light") == "Dark"
            if is_dark:
                self.md_bg_color = (0.2, 0.2, 0.2, 1)
        
        # OVERDUE / NOTIFIED: Aggressive RED for overdue, subtle red for notified
        if self.is_overdue == 1:
            # Strong Red
            self.md_bg_color = (0.5, 0.1, 0.1, 1) if is_dark else (1, 0.7, 0.7, 1)
        elif notified == 1:
            # Medium Red
            self.md_bg_color = (0.4, 0.1, 0.1, 1) if is_dark else (1, 0.8, 0.8, 1)
        
        # Separate tint for category icon in overdue state (prio_color is untouched)
        self.cat_icon_color = self.prio_color
        
        # Category Icon Mapping
        cat_icons = {
            "Work": "briefcase", "Study": "school", "Travel": "airplane",
            "Personal": "account", "General": "star", "Other": "circle-outline",
            "Health": "heart-pulse", "Gym": "dumbbell", "Shopping": "cart"
        }
        self.cat_icon = cat_icons.get(category, "checkbox-blank-circle-outline")

        # 1. Priority Indicator (Left Bar)
        self.priority_bar = MDBoxLayout(size_hint_x=None, width=dp(6), md_bg_color=self.prio_color)
        self.priority_bar.radius = [12, 0, 0, 12]
        self.add_widget(self.priority_bar)
        
        # Priority mapping for icons
        prio_icon_map = {
            1: "chevron-double-up",
            2: "minus",
            3: "chevron-down"
        }
        self.p_icon = prio_icon_map.get(priority, "circle")
        
        # 2. Main Content
        content = MDBoxLayout(orientation="horizontal", padding=[dp(12), dp(8)], spacing=dp(10))
        
        # Icon Label (Fixed Width to prevent overlap, bigger width for spacing)
        icon_box = MDBoxLayout(size_hint_x=None, width=dp(60), pos_hint={'center_y': 0.5}, padding=[dp(10), 0])
        # Two icons: Priority and Category
        icon_box.add_widget(MDIcon(
            icon=self.p_icon,
            theme_text_color="Custom",
            text_color=self.prio_color,   # Always original priority color
            font_size="18sp",
            pos_hint={'center_y': 0.5}
        ))
        icon_box.add_widget(MDIcon(
            icon=self.cat_icon,
            theme_text_color="Custom",
            text_color=self.cat_icon_color,  # Red only when overdue, else prio_color
            font_size="24sp",
            pos_hint={'center_y': 0.5}
        ))
        content.add_widget(icon_box)
        
        # Text Column
        text_col = MDBoxLayout(orientation="vertical", spacing=dp(2))
        title_lbl = MDLabel(text=title, bold=True, font_style="Subtitle2", theme_text_color="Primary", size_hint_y=None, height=dp(30))
        
        try:
             dt = datetime.fromisoformat(due)
             d_str = dt.strftime("%b %d, %I:%M %p")
        except: d_str = due
            
        due_lbl = MDLabel(text=d_str, font_style="Caption", theme_text_color="Secondary", size_hint_y=None, height=dp(20))
        
        text_col.add_widget(title_lbl)
        text_col.add_widget(due_lbl)
        content.add_widget(text_col)
        
        # 3. Actions
        actions = MDBoxLayout(size_hint_x=None, width=dp(100), pos_hint={'center_y': 0.5}, spacing=dp(2))
        
        # Complete Icon Button
        actions.add_widget(MDIconButton(
            icon="check-circle-outline", 
            theme_text_color="Custom", 
            text_color=(0, 0.6, 0, 1), 
            on_release=self.confirm_complete
        ))
        
        # Quick Delete (Optional - or just leave to details. User wants delete working)
        actions.add_widget(MDIconButton(
            icon="delete-outline", 
            theme_text_color="Error", 
            on_release=self.confirm_delete
        ))
        
        content.add_widget(actions)
        self.add_widget(content)

    def confirm_complete(self, instance):
        try:
            complete_task(self.app.db_path, self.task_id, datetime.now().isoformat(), user_uid=self.app.current_uid)
        except Exception as e:
            from kivy.logger import Logger
            Logger.error(f"Task completion error: {e}")
            return
            
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self.refresh_callback(), 0.1)

    def on_touch_down(self, touch):
        # If the touch is on one of the action buttons, let them handle it
        for child in self.children[0].children[0].children: # Actions layout
            if child.collide_point(*touch.pos):
                return super().on_touch_down(touch)
        
        if self.collide_point(*touch.pos):
             return super().on_touch_down(touch)
        return False

    def confirm_delete(self, *args):
        self.dialog = MDDialog(
            title="Delete Task?",
            text=f"Are you sure you want to delete/update this task?",
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda x: self.dialog.dismiss()),
                MDRaisedButton(text="DELETE", md_bg_color=(1, 0, 0, 1), on_release=self.do_delete)
            ]
        )
        self.dialog.open()

    def do_delete(self, *args):
        try:
            delete_task(self.app.db_path, self.task_id, user_uid=self.app.current_uid)
            write_audit(self.app.db_path, self.task_id, "deleted", user_uid=self.app.current_uid, task_title=self.title)
        except Exception as e:
            from kivy.logger import Logger
            Logger.error(f"Task deletion error: {e}")
            
        if self.dialog:
            self.dialog.dismiss()
            
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self.refresh_callback(), 0.1)

class DashboardScreen(MDScreen):
    def update_date(self, *args):
        if hasattr(self, 'date_label'):
            self.date_label.text = datetime.now().strftime("%a %d %b")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ui_built = False

    def switch_to_calendar(self, instance):
        if hasattr(self, 'nav'):
            self.nav.switch_tab('screen2')

    def on_enter(self):
        self.app = App.get_running_app()
        # Force a fresh UI build to avoid BottomNavigation rendering bugs
        self.build_ui()
        self.ui_built = True
        self.refresh_tasks(None)
        
    def on_leave(self):
        # Completely obliterate the UI on leave to clear corrupt navigation states
        if hasattr(self, 'nav'):
            del self.nav
        self.clear_widgets()

    def build_ui(self):
        self.clear_widgets()
        
        # Navigation
        self.nav = MDBottomNavigation()
        
        # --- TAB 1: Tasks ---
        screen1 = MDBottomNavigationItem(name="screen1", text="Tasks", icon="format-list-bulleted", on_tab_press=self.refresh_tasks)
        
        layout1 = MDBoxLayout(orientation="vertical")
        
        # Header (Theme-aware)
        header1 = MDCard(size_hint_y=None, height=dp(80), radius=[0, 0, 20, 20], elevation=4, md_bg_color=App.get_running_app().theme_cls.primary_color)
        h1 = MDBoxLayout(orientation="horizontal", padding=[dp(15), 0], spacing=dp(5))
        
        # Date Button (Left)
        today_str = datetime.now().strftime("%a %d %b")
        self.date_btn = MDFlatButton(
            text=today_str, 
            theme_text_color="Custom", 
            text_color=(1, 1, 1, 1), 
            font_style="Caption",
            on_release=self.switch_to_calendar
        )
        try: self.date_btn.font_name = "Montserrat"
        except: pass
        
        h1.add_widget(self.date_btn)
        
        # Icons Container (Right)
        icons_box = MDBoxLayout(orientation="horizontal", spacing=dp(0), adaptive_width=True, pos_hint={'center_y': 0.5})
        
        icon_color = (1, 1, 1, 1) # White
        exit_color = (1, 0.4, 0.4, 1) # Light Red
        
        # Add Task
        icons_box.add_widget(MDIconButton(
            icon="plus-circle", theme_text_color="Custom", text_color=icon_color, 
            on_release=self.go_to_create, icon_size="28sp"
        ))
        # AI
        icons_box.add_widget(MDIconButton(
            icon="robot", theme_text_color="Custom", text_color=icon_color, 
            on_release=self.open_ai, icon_size="28sp"
        ))
        # Analytics
        icons_box.add_widget(MDIconButton(
            icon="chart-bar", theme_text_color="Custom", text_color=icon_color, 
            on_release=self.go_to_analytics, icon_size="28sp"
        ))
        # Settings
        icons_box.add_widget(MDIconButton(
            icon="cog", theme_text_color="Custom", text_color=icon_color, 
            on_release=self.go_to_settings, icon_size="28sp"
        ))
        # Exit
        icons_box.add_widget(MDIconButton(
            icon="logout", theme_text_color="Custom", text_color=exit_color, 
            on_release=self.logout, icon_size="28sp"
        ))
        
        h1.add_widget(icons_box)
        
        header1.add_widget(h1)
        layout1.add_widget(header1)
        
        # Schedule Date Update
        from kivy.clock import Clock
        Clock.schedule_interval(self.update_date, 3600)
        
        # Scrollable Task List
        scroll1 = ScrollView()
        self.task_list = MDList()
        self.task_list.padding = dp(10)
        self.task_list.spacing = dp(10)
        scroll1.add_widget(self.task_list)
        layout1.add_widget(scroll1)
        
        screen1.add_widget(layout1)
        self.nav.add_widget(screen1)

        # --- TAB 2: Calendar ---
        screen2 = MDBottomNavigationItem(name="screen2", text="Calendar", icon="calendar", on_tab_press=self.go_to_calendar)
        self.nav.add_widget(screen2)
        
        # --- TAB 3: History ---
        screen3 = MDBottomNavigationItem(name="screen3", text="History", icon="history", on_tab_press=self.refresh_history)
        layout3 = MDBoxLayout(orientation="vertical")
        
        # Header (Blue)
        header3 = MDCard(size_hint_y=None, height=dp(80), radius=[0, 0, 20, 20], elevation=4, md_bg_color=App.get_running_app().theme_cls.primary_color)
        h3 = MDBoxLayout(orientation="horizontal", padding=[dp(10), 0], spacing=dp(5))
        
        h3.add_widget(MDLabel(text="History", theme_text_color="Custom", text_color=(1,1,1,1), font_style="H5", bold=True, pos_hint={'center_y': 0.5}, halign="center"))
        
        # Clear All
        h3.add_widget(MDIconButton(icon="delete", theme_text_color="Custom", text_color=(1, 0.3, 0.3, 1), on_release=self.confirm_clear_all_history, pos_hint={'center_y': 0.5}))
        
        header3.add_widget(h3)
        layout3.add_widget(header3)
        
        # List
        scroll3 = ScrollView()
        self.history_list = MDList()
        scroll3.add_widget(self.history_list)
        layout3.add_widget(scroll3)
        
        screen3.add_widget(layout3)
        self.nav.add_widget(screen3)
        
        self.add_widget(self.nav)
        
    def refresh_tasks(self, instance):
        if not hasattr(self, 'task_list'): return
        self.task_list.clear_widgets()
        if not self.app.db_path: return
        
        try:
            rows = list_tasks(self.app.db_path)
        except Exception as e:
            print(f"Error listing tasks: {e}")
            return
        clean_tasks = []
        for row in rows:
            is_overdue_flag = 0
            
            # Safe index extraction
            tid = row[0]
            ct = row[1]
            nonce = row[2]
            due = row[3]
            prio = row[4]
            notified = row[5]
            created = row[6] if len(row) > 6 else ""
            completed = row[7] if len(row) > 7 else None
            category = row[8] if len(row) > 8 else ""
            sound = row[9] if len(row) > 9 else "Default"
            desc = row[10] if len(row) > 10 else ""
            is_overdue_flag = row[11] if len(row) > 11 else 0
            
            if completed: continue
            
            try: title = decrypt_bytes(ct, nonce, self.app.derived_key).decode("utf-8").split("\n")[0]
            except: title = "????"
            
            clean_tasks.append({'id': tid, 'title': title, 'due': due, 'prio': prio, 'cat': category, 'notified': notified, 'sound': sound, 'desc': desc, 'is_overdue': is_overdue_flag})
            
        clean_tasks.sort(key=lambda x: x['due'])
        
        if not clean_tasks:
            self.task_list.add_widget(MDLabel(text="All caught up!", halign="center", theme_text_color="Secondary", size_hint_y=None, height=dp(100)))
            
        for t in clean_tasks:
            card = TaskCard(t['id'], t['title'], t['due'], t['prio'], t['cat'], t['notified'], self.app, lambda: self.refresh_tasks(None), description=t['desc'], is_overdue=t['is_overdue'])
            card.bind(on_release=lambda x, task=t: self.show_task_options(task))
            self.task_list.add_widget(card)

    def show_task_options(self, t):
        write_audit(self.app.db_path, t['id'], "opened", user_uid=self.app.current_uid, task_title=t['title'])
        content = MDBoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None, padding=[0, dp(10), 0, 0])
        content.bind(minimum_height=content.setter('height'))
        
        # Priority mapping
        prio_map = {1: ("High", (1, 0.2, 0.2, 1)), 2: ("Medium", (1, 0.8, 0, 1)), 3: ("Low", (0.2, 0.8, 0.2, 1))}
        prio_text, prio_col = prio_map.get(t['prio'], ("Low", (0.2, 0.8, 0.2, 1)))

        # 1. Title
        title_lbl = MDLabel(text=t['title'], font_style="H5", bold=True, theme_text_color="Primary", size_hint_y=None, height=dp(40))
        content.add_widget(title_lbl)
        
        from kivymd.uix.card import MDSeparator
        content.add_widget(MDSeparator())
        
        # 2. Description
        desc_text = t['desc'] if t['desc'] else "No description provided."
        desc_lbl = MDLabel(text=desc_text, font_style="Body1", theme_text_color="Secondary", size_hint_y=None)
        desc_lbl.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        content.add_widget(desc_lbl)
        
        content.add_widget(MDSeparator())
        
        # 3. Details Row (Priority Badge)
        details_row = MDBoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(30))
        details_row.add_widget(MDIcon(icon="flag", theme_text_color="Custom", text_color=prio_col, size_hint=(None, None), size=(dp(24), dp(24))))
        details_row.add_widget(MDLabel(text=f"Priority: {prio_text}", theme_text_color="Secondary", font_style="Caption"))
        content.add_widget(details_row)
        
        # 4. Due Date
        due_row = MDBoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(30))
        due_row.add_widget(MDIcon(icon="calendar-clock", theme_text_color="Primary", size_hint=(None, None), size=(dp(24), dp(24))))
        due_row.add_widget(MDLabel(text=f"Due: {t['due']}", theme_text_color="Secondary", font_style="Caption"))
        content.add_widget(due_row)

        content.add_widget(MDSeparator())
        
        btn_box = MDBoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None, height=dp(100))

        # Action Buttons configuration
        if t['notified'] == 1 or t.get('is_overdue', 0) == 1:
            # Overdue / Active Notification state -> Persistent Alerts
            snooze_row = MDBoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(40))
            snooze_row.add_widget(MDRectangleFlatButton(text="Snooze 5m", text_color=(1, 0.5, 0, 1), on_release=lambda x: self.do_snooze(t['id'], 5), size_hint_x=0.5))
            snooze_row.add_widget(MDRectangleFlatButton(text="Snooze 10m", text_color=(1, 0.5, 0, 1), on_release=lambda x: self.do_snooze(t['id'], 10), size_hint_x=0.5))
            btn_box.add_widget(snooze_row)
            
            btn_box.add_widget(MDFillRoundFlatIconButton(text="Dismiss", icon="check", md_bg_color=(0.9, 0.1, 0.1, 1), on_release=lambda x: self.do_dismiss(t['id']), size_hint_y=None, height=dp(40), size_hint_x=1))
        else:
            action_row = MDBoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(48))
            action_row.add_widget(MDFillRoundFlatIconButton(text="Edit", icon="pencil", on_release=lambda x: self.do_modify(t), size_hint_x=0.5))
            action_row.add_widget(MDFillRoundFlatIconButton(text="Delete", icon="delete", md_bg_color=(1,0.2,0.2,1), on_release=lambda x: self.do_delete(t['id']), size_hint_x=0.5))
            btn_box.add_widget(action_row)
            
        content.add_widget(btn_box)

        self.dialog = MDDialog(
            title="",
            type="custom",
            content_cls=content,
            size_hint_x=0.9,
            radius=[20, 20, 20, 20],
            buttons=[MDFlatButton(text="CLOSE", theme_text_color="Primary", on_release=lambda *args: self.dialog.dismiss() if hasattr(self, 'dialog') and self.dialog else None)]
        )
        self.dialog.open()

    def close_task_detail(self, *args):
        if hasattr(self, 'dialog') and self.dialog:
            self.dialog.dismiss()

    def do_modify(self, t):
        self.dialog.dismiss()
        self.confirm_dialog = MDDialog(
            title="Update Task?",
            text=f"Are you sure you want to delete/update this task?",
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda x: self.confirm_dialog.dismiss()),
                MDRaisedButton(text="CONFIRM", on_release=lambda x: self.navigate_to_edit(t))
            ]
        )
        self.confirm_dialog.open()

    def navigate_to_edit(self, t):
        self.confirm_dialog.dismiss()
        self.app.modify_task_data = (t['id'], t['title'], t['due'], t['prio'], t['cat'], t['sound'], t['desc'])
        self.app.switch_screen("create_task")
        
    def do_delete(self, tid):
        self.dialog.dismiss()
        self.delete_confirm_dialog = MDDialog(
            title="Delete Task?",
            text=f"Are you sure you want to delete/update this task?",
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda x: self.delete_confirm_dialog.dismiss()),
                MDRaisedButton(text="DELETE", md_bg_color=(1, 0, 0, 1), on_release=lambda x: self.execute_delete(tid))
            ]
        )
        self.delete_confirm_dialog.open()

    def execute_delete(self, tid):
        self.delete_confirm_dialog.dismiss()
        delete_task(self.app.db_path, tid, user_uid=self.app.current_uid)
        self.refresh_tasks(None)
        
    def do_dismiss(self, tid):
        dismiss_notification(self.app.db_path, tid, user_uid=self.app.current_uid)
        self.dialog.dismiss()
        from kivymd.toast import toast
        toast("Task alert dismissed.")
        self.refresh_tasks(None)
        
    def do_snooze(self, tid, mins):
        snooze_task(self.app.db_path, tid, mins, user_uid=self.app.current_uid)
        self.dialog.dismiss()
        from kivymd.toast import toast
        toast(f"Task snoozed for {mins} minutes.")
        self.refresh_tasks(None)

    def go_to_create(self, i): self.app.selected_date_hint = None; self.app.switch_screen("create_task")
    def open_ai(self, i): self.app.switch_screen("ai")
    def go_to_calendar(self, i): 
        # Do not switch tabs before leaving, it causes white-screen animation overlap
        self.app.switch_screen("calendar_month")
    
    def refresh_history(self, i):
        self.history_list.clear_widgets()
        if not self.app.db_path: return
        rows = list_tasks(self.app.db_path)
        for row in rows:
            tid = row[0]
            ct = row[1]
            nonce = row[2]
            due = row[3]
            prio = row[4]
            notified = row[5]
            created = row[6] if len(row) > 6 else ""
            completed = row[7] if len(row) > 7 else None
            category = row[8] if len(row) > 8 else ""
            sound = row[9] if len(row) > 9 else "Default"
            desc = row[10] if len(row) > 10 else ""
            
            if not completed: continue
            try: title = decrypt_bytes(ct, nonce, self.app.derived_key).decode("utf-8").split("\n")[0]
            except: title="Error"
            
            item = OneLineAvatarIconListItem(text=title)
            item.add_widget(IconLeftWidget(icon="check-circle"))
            item.add_widget(IconRightWidget(icon="trash-can", on_release=lambda x, t=tid: self.confirm_delete_history_item(t)))
            self.history_list.add_widget(item)

    def confirm_clear_all_history(self, i): self.dialog = MDDialog(title="Clear All?", buttons=[MDFlatButton(text="No", on_release=lambda x: self.dialog.dismiss()), MDRaisedButton(text="Yes", on_release=self.do_clear_all_history)]); self.dialog.open()
    def do_clear_all_history(self, i): delete_all_completed_tasks(self.app.db_path, user_uid=self.app.current_uid); self.dialog.dismiss(); self.refresh_history(None)
    def confirm_delete_history_item(self, tid): self.dialog = MDDialog(title="Delete?", buttons=[MDFlatButton(text="No", on_release=lambda x: self.dialog.dismiss()), MDRaisedButton(text="Yes", on_release=lambda x: self.do_delete_history(tid))]); self.dialog.open()
    def do_delete_history(self, tid): delete_task(self.app.db_path, tid, user_uid=self.app.current_uid); self.dialog.dismiss(); self.refresh_history(None)
    
    def go_to_analytics(self, i): self.app.switch_screen("analytics")
    def go_to_settings(self, i): self.app.switch_screen("settings")
    def open_ai(self, i): 
        # Check explicit navigation mapping as requested
        import logging
        if not self.manager.has_screen("ai"):
             Logger.error("Dashboard: Cannot navigate, 'ai' screen missing from manager.")
             return
             
        self.app.switch_screen("ai")

    def logout(self, i): 
        self.app.stop_scheduler()
        self.app.current_user = None
        self.app.switch_screen("login")
