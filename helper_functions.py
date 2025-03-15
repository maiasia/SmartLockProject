from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFlatButton

def log_action(action):
    """Logs an action with a timestamp."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Assuming usage_history is global or passed in
    usage_history.append(f"[{timestamp}] {action}")

def create_popup(title, message):
    """Create a modern popup with a title and message."""
    popup_content = BoxLayout(orientation="vertical", padding=10)
    popup_label = MDLabel(text=message, theme_text_color="Secondary", halign="center", size_hint_y=None, height=300)
    popup_label.color = (1, 1, 1, 1)
    popup_content.add_widget(popup_label)

    close_button = MDFlatButton(text="Close", on_release=lambda instance: popup.dismiss())
    close_button.md_bg_color = (0.5, 0.3, 0.8, 1)
    popup_content.add_widget(close_button)

    popup = Popup(title=title, content=popup_content, size_hint=(0.8, 0.4), auto_dismiss=False)
    popup.open()

    return popup
