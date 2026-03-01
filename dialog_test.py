from kivymd.app import MDApp
from kivymd.uix.pickers import MDDatePicker, MDTimePicker
from kivy.core.window import Window
import traceback

class TestApp(MDApp):
    def on_start(self):
        try:
            class ResponsiveDatePicker(MDDatePicker):
                def _update_dialog_size(self):
                    self.width = min(Window.width * 0.95, 400)
                    self.height = min(Window.height * 0.8, 400)
                    self.pos_hint = {"center_x": 0.5, "center_y": 0.5}

            date_dialog = ResponsiveDatePicker()
            date_dialog.open()
            print("DATE PICKER WORKED NATIVELY.")
        except Exception as e:
            print("DATE CRASH:", e)

if __name__ == "__main__":
    TestApp().run()
