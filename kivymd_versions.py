import sys

def check_kivymd_version():
    import kivymd
    print(kivymd.__version__)
    
    from kivymd.uix.pickers import MDDatePicker, MDTimePicker
    import inspect
    print("MDTimePicker INIT ARGS:", inspect.signature(MDTimePicker.__init__))
    print("MDDatePicker INIT ARGS:", inspect.signature(MDDatePicker.__init__))

if __name__ == '__main__':
    check_kivymd_version()
