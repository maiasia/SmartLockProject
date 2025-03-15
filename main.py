from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.core.window import Window
from smart_lock_ui import SmartLockApp

class SmartLockAppMD(MDApp):
    def build(self):
        return SmartLockApp()

if __name__ == '__main__':
    Window.size = (Window.width, Window.height)
    Window.maximize()
    SmartLockAppMD().run()
