import os
import sys
import logging
import traceback
import winsdk.windows.ui.notifications as notifications
import winsdk.windows.data.xml.dom as dom
import ctypes

def test_toast():
    AUMID = "RemindMe.App"
    if sys.platform == 'win32':
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(AUMID)
    
    title = "Test Notification"
    message = "This is a test of the winsdk implementation."
    
    xml_content = (
        f"<toast activationType='protocol'>\n"
        f"  <visual>\n"
        f"    <binding template='ToastGeneric'>\n"
        f"      <text>{title}</text>\n"
        f"      <text>{message}</text>\n"
        f"    </binding>\n"
        f"  </visual>\n"
    )
    
    # Try adding a dummy image path to see if it causes issues
    img_path = os.path.abspath("assets/logo.png")
    if os.path.exists(img_path):
        xml_content += f"  <image placement='appLogoOverride' src='file:///{img_path}'/>\n"
        
    xml_content += "</toast>"
    
    print(f"XML Payload:\n{xml_content}")
    
    doc = dom.XmlDocument()
    doc.load_xml(xml_content)
    
    notifier = notifications.ToastNotificationManager.create_toast_notifier(AUMID)
    toast = notifications.ToastNotification(doc)
    
    try:
        notifier.show(toast)
        print("✅ Toast dispatched successfully!")
    except Exception as e:
        print(f"❌ Failed to show toast: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_toast()
