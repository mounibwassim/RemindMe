from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.pickers import MDDatePicker
from kivy.core.window import Window

KV = '''
FloatLayout:
    MDRaisedButton:
        text: "Open Date Picker"
        pos_hint: {'center_x': .5, 'center_y': .5}
        on_release: app.show_date_picker()
'''

class CustomDatePicker(MDDatePicker):
    def on_device_orientation(self, instance, orientation):
        # ALWAYS force portrait to prevent the Landscape right-side black clipping bug!
        super().on_device_orientation(instance, "portrait")

class TestApp(MDApp):
    def build(self):
        Window.size = (300, 600) # Simulate a very narrow mobile screen!
        return Builder.load_string(KV)

    def show_date_picker(self):
        date_dialog = CustomDatePicker()
        date_dialog.size_hint = (0.9, None)
        date_dialog.height = Window.height * 0.7
        date_dialog.open()

if __name__ == '__main__':
    TestApp().run()
