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
            from kivymd.uix.dialog import MDDialog
            from kivymd.uix.button import MDFlatButton
            from kivy.metrics import dp

            date_dialog = MDDatePicker(
                primary_color=self.theme_cls.primary_color,
                size_hint=(0.95, None),
            )
            date_dialog.height = min(Window.height * 0.8, dp(400))
            date_dialog.pos_hint = {"center_x": 0.5, "center_y": 0.5}

            def on_save(instance, value, date_range):
                print("SAVED:", value)
                dialog.dismiss()

            dialog = MDDialog(
                title="Select Date",
                type="custom",
                content_cls=date_dialog,
                buttons=[
                    MDFlatButton(text="CANCEL", on_release=lambda x: dialog.dismiss()),
                    MDFlatButton(text="OK", on_release=lambda x: on_save(date_dialog, getattr(date_dialog, 'sel_date', getattr(date_dialog, 'date', None)), None)),
                ],
            )
            dialog.open()
        except Exception as e:
            print("DATE CRASH:", e)
            traceback.print_exc()

    def open_time(self):
        try:
            from kivymd.uix.dialog import MDDialog
            from kivymd.uix.button import MDFlatButton
            from kivy.metrics import dp

            time_dialog = MDTimePicker(
                primary_color=self.theme_cls.primary_color,
                size_hint=(0.9, None)
            )
            time_dialog.height = min(Window.height * 0.5, dp(300))
            time_dialog.pos_hint = {"center_x": 0.5, "center_y": 0.5}

            dialog = MDDialog(
                title="Select Time",
                type="custom",
                content_cls=time_dialog,
                buttons=[
                    MDFlatButton(text="CANCEL", on_release=lambda x: dialog.dismiss()),
                    MDFlatButton(text="OK", on_release=lambda x: print("SAVED TIME")),
                ],
            )
            dialog.open()
        except Exception as e:
            print("TIME CRASH:", e)
            traceback.print_exc()

if __name__ == "__main__":
    TestApp().run()
