from kivymd.app import MDApp
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.dialog import MDDialog

class TestApp(MDApp):
    def on_start(self):
        try:
            d = MDDatePicker()
            dialog = MDDialog(content_cls=d)
            dialog.open()
        except Exception as e:
            with open("crash_python.log", "w") as f:
                import traceback
                f.write(traceback.format_exc())

if __name__ == "__main__":
    TestApp().run()
