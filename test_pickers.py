import traceback
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.core.window import Window
from kivymd.uix.screen import MDScreen
from kivymd.uix.pickers import MDDatePicker, MDTimePicker

Window.size = (360, 640)

KV = '''
MDScreen:
    MDBoxLayout:
        orientation: "vertical"
        spacing: "20dp"
        pos_hint: {"center_x": .5, "center_y": .5}
        adaptive_size: True
        
        MDRaisedButton:
            text: "Open Date"
            on_release: app.open_date()
            
        MDRaisedButton:
            text: "Open Time"
            on_release: app.open_time()
'''

class TestApp(MDApp):
    def build(self):
        return Builder.load_string(KV)

    def on_start(self):
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self.open_time(), 1)
        Clock.schedule_once(lambda dt: self.open_date(), 2)

    def open_date(self):
        try:
            date_dialog = MDDatePicker(primary_color=self.theme_cls.primary_color)
            date_dialog.open()
        except Exception as e:
            print("DATE CRASH:", e)
            traceback.print_exc()

    def open_time(self):
        try:
            time_dialog = MDTimePicker(primary_color=self.theme_cls.primary_color)
            time_dialog.open()
        except Exception as e:
            print("TIME CRASH:", e)
            traceback.print_exc()

if __name__ == "__main__":
    TestApp().run()
