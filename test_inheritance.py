import sys
from kivymd.uix.pickers import MDDatePicker, MDTimePicker
from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
import inspect

def test():
    print("MDDatePicker bases:", inspect.getmro(MDDatePicker))
    print("MDTimePicker bases:", inspect.getmro(MDTimePicker))

if __name__ == "__main__":
    test()
