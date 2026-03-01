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

class TestApp(MDApp):
    def build(self):
        return Builder.load_string(KV)

    def show_date_picker(self):
        date_dialog = MDDatePicker()
        # The user's requested logic:
        # modal dialog 90% width, adaptive height
        date_dialog.size_hint = (None, None)
        date_dialog.width = Window.width * 0.9
        date_dialog.height = Window.height * 0.7
        date_dialog.open()

if __name__ == '__main__':
    TestApp().run()
