from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import MDList, OneLineListItem
from kivy.uix.label import Label ##
from kivy.clock import Clock
from datetime import datetime
from kivy.uix.popup import Popup
from kivymd.uix.button import MDFlatButton
from kivymd.uix.label import MDLabel
from kivy.uix.boxlayout import BoxLayout

import random
import smtplib
import ssl

import win32com.client as win32
import re
import traceback

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Global data
users = {"admin": "1234"}  # Default users and passwords
usage_history = []  # Lock usage history
current_user = None  # Currently logged-in user
lock_duration = 0  # Lock duration in minutes
remaining_time = 0  # Remaining time for lock duration
lock_timer = None  # Timer handle
is_locked_for_duration = False  # Flag to check if locked for duration


def log_action(action):
    """Logs an action with a timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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


class SmartLockApp(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)

        # Username display label at the top (initially empty)
        self.username_display = MDLabel(
            text="Username: Not logged in",
            font_style="H6",
            size_hint_y=None,
            height=40,
            theme_text_color="Secondary",
            halign="center"
        )
        self.add_widget(self.username_display)  # Add the username label to the top

        # Login Section
        self.add_widget(MDLabel(
            text="Smart Lock System",
            font_style="H4",
            size_hint_y=None,
            height=50,
            theme_text_color="Primary"
        ))

        # Username input field (Initially visible)
        self.username_input = MDTextField(
            hint_text="Username",
            size_hint_y=None,
            height=50,
            pos_hint={"center_x": 0.5},
            mode="rectangle"
        )
        self.username_input.line_color_focus = (0.5, 0.3, 0.8, 1)
        self.add_widget(self.username_input)

        # Password input field (Initially visible)
        self.password_input = MDTextField(
            hint_text="Password",
            password=True,
            size_hint_y=None,
            height=50,
            pos_hint={"center_x": 0.5},
            mode="rectangle"
        )
        self.password_input.line_color_focus = (0.5, 0.3, 0.8, 1)
        self.add_widget(self.password_input)

        # Forgot password button
        self.forgot_password_button = MDRaisedButton(
            text="Forgot password",
            size_hint_y=None,
            height=50,
            pos_hint={"center_x": 0.5},
            on_release=self.send_new_password,
            disabled=False
        )
        self.forgot_password_button.md_bg_color = (0.5, 0.3, 0.8, 1)
        self.add_widget(self.forgot_password_button)

        # Login button
        self.login_button = MDRaisedButton(
            text="Login",
            size_hint_y=None,
            height=50,
            pos_hint={"center_x": 0.5},
            on_release=self.login
        )
        self.login_button.md_bg_color = (0.5, 0.3, 0.8, 1)
        self.add_widget(self.login_button)

        # Logout button (Initially hidden)
        self.logout_button = MDRaisedButton(
            text="Logout",
            size_hint_y=None,
            height=50,
            pos_hint={"center_x": 0.5},
            on_release=self.logout,
            disabled=True  # Initially disabled
        )
        self.logout_button.md_bg_color = (0.9, 0.1, 0.1, 1)  # Red color for logout

        self.lock_section = BoxLayout(orientation="vertical", size_hint_y=None, height=300, opacity=0)

        self.lock_section.add_widget(MDLabel(
            text="Lock Control",
            font_style="H6",
            size_hint_y=None,
            height=40,
            theme_text_color="Secondary"
        ))

        # Unlock button (Initially hidden)
        self.unlock_button = MDRaisedButton(
            text="Unlock",
            size_hint_y=None,
            height=50,
            pos_hint={"center_x": 0.5},
            on_release=self.unlock_lock,
            disabled=True
        )
        self.unlock_button.md_bg_color = (0, 0.7, 0.2, 1)  # Green color for unlock
        self.lock_section.add_widget(self.unlock_button)

        # Lock button (Initially hidden)
        self.lock_button = MDRaisedButton(
            text="Lock",
            size_hint_y=None,
            height=50,
            pos_hint={"center_x": 0.5},
            on_release=self.lock_lock,
            disabled=True
        )
        self.lock_button.md_bg_color = (0.9, 0.1, 0.1, 1)  # Red color for lock
        self.lock_section.add_widget(self.lock_button)

        # Lock time input field (Initially hidden)
        self.lock_time_input = MDTextField(
            hint_text="Lock for (minutes)",
            size_hint_y=None,
            height=50,
            pos_hint={"center_x": 0.5},
            mode="rectangle",
            disabled=True  # Initially disabled
        )
        self.lock_section.add_widget(self.lock_time_input)

        # Timer label to display remaining time for lock duration (Initially hidden)
        self.timer_label = MDLabel(
            text="Time remaining: N/A",
            theme_text_color="Secondary",
            halign="center",
            size_hint_y=None,
            height=40,
            opacity=0  # Hidden initially
        )
        self.lock_section.add_widget(self.timer_label)  # Add timer label to the layout

        # Lock for duration button (Initially hidden)
        self.lock_time_button = MDRaisedButton(
            text="Lock for Duration",
            size_hint_y=None,
            height=50,
            pos_hint={"center_x": 0.5},
            on_release=self.lock_for_duration,
            disabled=True  # Initially disabled
        )
        self.lock_section.add_widget(self.lock_time_button)

        # Stop Timer button (Initially hidden)
        self.stop_timer_button = MDRaisedButton(
            text="Stop Timer",
            size_hint_y=None,
            height=50,
            pos_hint={"center_x": 0.5},
            on_release=self.stop_timer,
            disabled=True  # Initially disabled
        )
        self.lock_section.add_widget(self.stop_timer_button)

        # Add the lock section to the layout (hidden initially)
        self.add_widget(self.lock_section)

        # Add the logout button at the bottom of the screen
        self.add_widget(self.logout_button)

        # User management section
        self.user_management_button = MDRaisedButton(
            text="User Management",
            size_hint_y=None,
            height=50,
            pos_hint={"center_x": 0.5},
            on_release=self.user_management
        )
        self.user_management_button.md_bg_color = (0.5, 0.3, 0.8, 1)
        self.add_widget(self.user_management_button)

    def login(self, instance):
        global current_user
        username = self.username_input.text
        password = self.password_input.text

        if username in users and users[username] == password:
            current_user = username
            log_action(f"{username} logged in")
            create_popup("Login Success", f"Welcome, {username}!")

            self.username_input.text = ""
            self.password_input.text = ""

            # Hide login inputs and button
            self.username_input.opacity = 0
            self.password_input.opacity = 0
            self.login_button.opacity = 0
            #self.Forgot_the_password_button.opacity = 0

            # Show logout button
            self.logout_button.disabled = False

            # Show lock control section after successful login
            self.unlock_button.disabled = is_locked_for_duration
            self.lock_button.disabled = is_locked_for_duration
            self.lock_time_input.disabled = False
            self.lock_time_button.disabled = is_locked_for_duration
            self.stop_timer_button.disabled = False
            self.timer_label.opacity = 1  # Show timer label
            self.lock_section.opacity = 1  # Make lock section visible

            # Show the logged-in username at the top of the screen
            self.username_display.text = f"Username: {username}"

        else:
            self.login_error_popup = create_popup("Login Error", "Invalid username or password!")

    def logout(self, instance):
        global current_user
        log_action(f"{current_user} logged out")
        create_popup("Logout Success", f"Goodbye, {current_user}!")

        # Reset the state
        current_user = None
        self.username_display.text = "Username: Not logged in"

        # Show login inputs and button
        self.username_input.opacity = 1
        self.password_input.opacity = 1
        self.login_button.opacity = 1
        #self.email_input.opacity = 0
        #self.forgot_password_button.opacity = 1

        # Hide logout button and lock control section
        self.logout_button.disabled = True
        self.unlock_button.disabled = True
        self.lock_button.disabled = True
        self.lock_time_input.disabled = True
        self.lock_time_button.disabled = True
        self.stop_timer_button.disabled = True
        self.timer_label.opacity = 0
        self.lock_section.opacity = 0

    def lock_lock(self, instance):
        """Lock the lock immediately."""
        log_action(f"{current_user} locked the smart lock")
        create_popup("Lock", "The smart lock is now locked.")

    def unlock_lock(self, instance):
        """Unlock the lock immediately."""
        global remaining_time, is_locked_for_duration

        # if is_locked_for_duration:  # Check if the lock is still locked due to timer
        #     create_popup("Unlock Error", "Unlocking is not allowed while the timer is running.")
        #     return  # Exit early and do nothing if the timer is running

        # Unlock the lock if no timer is running
        log_action(f"{current_user} unlocked the smart lock")
        create_popup("Unlock", "The smart lock is now unlocked.")

    def lock_for_duration(self, instance):
        """Lock the lock for a specific duration."""
        global lock_duration, remaining_time, is_locked_for_duration

        if current_user != "admin":
            # Disable buttons if the user is not the admin
            self.lock_time_button.disabled = True
            self.stop_timer_button.disabled = True
            create_popup("Permission Denied", "Only an admin can lock the lock for a duration.")
            return

        # if remaining_time != 0:
        #     create_popup("Lock timer already active", "The lock is already locked for a duration")
        #     return

        try:
            lock_duration = int(self.lock_time_input.text)
            remaining_time = lock_duration * 60
            is_locked_for_duration = True
            self.lock_timer = Clock.schedule_interval(self.update_lock_timer, 1)

            # Disable buttons during the timer
            self.lock_button.disabled = True
            self.unlock_button.disabled = True
            self.lock_time_button.disabled = True
            self.stop_timer_button.disabled = False  # Enable Stop Timer button

            log_action(f"{current_user} locked the smart lock for {lock_duration} minutes.")
            create_popup("Lock Duration", f"The lock is now set for {lock_duration} minutes.")

        except ValueError:
            create_popup("Error", "Please enter a valid duration in minutes.")

    def update_lock_timer(self, dt):
        """Update the lock timer every second."""
        global remaining_time, is_locked_for_duration
        if remaining_time > 0:
            remaining_time -= 1
            minutes = remaining_time // 60
            seconds = remaining_time % 60
            self.timer_label.text = f"Time remaining: {minutes:02}:{seconds:02}"
        else:
            # Timer finished, unlock buttons
            self.lock_button.disabled = False
            self.unlock_button.disabled = False
            self.lock_time_button.disabled = False
            self.stop_timer_button.disabled = True  # Disable Stop Timer button
            self.lock_timer.cancel()
            is_locked_for_duration = False
            self.timer_label.text = "Time remaining: 00:00"
            create_popup("Lock Duration Finished", "The lock duration has ended. You can now unlock the lock.")

    def stop_timer(self, instance):
        """Stop the lock timer."""
        global remaining_time, is_locked_for_duration
        if self.lock_timer:
            self.lock_timer.cancel()
            remaining_time = 0
            is_locked_for_duration = False

            # Re-enable buttons after stopping the timer
            self.lock_button.disabled = False
            self.unlock_button.disabled = False
            self.lock_time_button.disabled = False
            self.stop_timer_button.disabled = True  # Disable Stop Timer button

            self.timer_label.text = "Time remaining: N/A"
            create_popup("Timer Stopped", "The timer was stopped.")

    def user_management(self, instance):
        """Open user management popup."""
        if current_user == "admin":
            content = BoxLayout(orientation="vertical", padding=10)

            # Button to view the list of users
            view_users_button = MDRaisedButton(
                text="View Users",
                size_hint_y=None,
                height=50,
                pos_hint={"center_x": 0.5},
                on_release=self.view_users
            )
            content.add_widget(view_users_button)

            # Button to add a user
            add_button = MDRaisedButton(
                text="Add User",
                size_hint_y=None,
                height=50,
                pos_hint={"center_x": 0.5},
                on_release=self.open_add_user_window
            )
            content.add_widget(add_button)

            # Button to remove a user
            remove_button = MDRaisedButton(
                text="Remove User",
                size_hint_y=None,
                height=50,
                pos_hint={"center_x": 0.5},
                on_release=self.remove_user
            )
            content.add_widget(remove_button)

            # Button to view the usage history
            history_button = MDRaisedButton(
                text="View Usage History",
                size_hint_y=None,
                height=50,
                pos_hint={"center_x": 0.5},
                on_release=self.view_usage_history
            )
            content.add_widget(history_button)

            # Popup to show user management options
            user_popup = Popup(
                title="User Management",
                content=content,
                size_hint=(0.8, 0.6),
                auto_dismiss=True
            )
            user_popup.open()
        else:
            create_popup("Access Denied", "Only admin can manage users!")

    def view_users(self, instance):
        """Display the list of users in a popup."""
        user_list = "\n".join(users.keys())
        if user_list:
            create_popup("Users List", user_list)
        else:
            create_popup("No Users", "No users available.")

    def open_add_user_window(self, instance):
        """Open a window to add a new user."""
        content = BoxLayout(orientation="vertical", padding=10)
        username_input = MDTextField(hint_text="Username", size_hint_y=None, height=50)
        password_input = MDTextField(hint_text="Password", password=True, size_hint_y=None, height=50)
        email_input = MDTextField(hint_text="Email", size_hint_y=None, height=50)

        def add_user(instance):
            """Add user to the system."""
            username = username_input.text
            password = password_input.text
            email = email_input.text
            if username and password and email:
                # Check if the password is exactly 4 digits
                if len(password) == 4 and password.isdigit():
                    users[username] = {"password": password, "email": email}
                    create_popup("User Added", f"User '{username}' added successfully.")
                    username_input.text = ""
                    password_input.text = ""
                    email_input.text = ""
                else:
                    create_popup("Error", "Password must be exactly 4 digits.")
            else:
                create_popup("Error", "Please enter username, password, and email.")

        add_button = MDRaisedButton(text="Add User", on_release=add_user)
        close_button = MDRaisedButton(text="Close", on_release=lambda instance: user_popup.dismiss())
        close_button.md_bg_color = (0.5, 0.3, 0.8, 1)

        content.add_widget(username_input)
        content.add_widget(password_input)
        content.add_widget(email_input)
        content.add_widget(add_button)
        content.add_widget(close_button)

        user_popup = Popup(
            title="Add User",
            content=content,
            size_hint=(0.8, 0.6),
            auto_dismiss=True
        )
        user_popup.open()

    def remove_user(self, instance):
        """Remove a user by selecting from a list."""
        content = BoxLayout(orientation="vertical", padding=10)
        users_list = MDList()  # Create a scrollable list for users

        def create_user_item(username):
            """Helper function to create a list item for each user."""
            item = OneLineListItem(
                text=username,
                on_release=lambda x: confirm_remove(username)  # Call confirm_remove when clicked
            )
            return item

        def confirm_remove(username):
            """Confirm before removing a user."""
            if username == "admin":
                create_popup("Error", "The 'admin' user cannot be removed.")
                return

            confirm_content = BoxLayout(orientation="vertical", padding=10)
            confirm_label = Label(text=f"Are you sure you want to remove '{username}'?")
            confirm_buttons = BoxLayout(size_hint_y=None, height=50, spacing=10)

            def remove_user_action(instance):
                """Perform the user removal."""
                del users[username]
                create_popup("User Removed", f"User '{username}' has been removed.")
                user_popup.dismiss()
                confirm_popup.dismiss()
                refresh_user_list()  # Refresh the user list after removal

            yes_button = MDRaisedButton(text="Yes", on_release=remove_user_action)
            no_button = MDRaisedButton(text="No", on_release=lambda x: confirm_popup.dismiss())
            confirm_buttons.add_widget(yes_button)
            confirm_buttons.add_widget(no_button)

            confirm_content.add_widget(confirm_label)
            confirm_content.add_widget(confirm_buttons)

            confirm_popup = Popup(
                title="Confirm Removal",
                content=confirm_content,
                size_hint=(0.8, 0.4),
                auto_dismiss=True,
            )
            confirm_popup.open()

        def refresh_user_list():
            """Refresh the displayed user list."""
            users_list.clear_widgets()
            for username in users:
                users_list.add_widget(create_user_item(username))

        # Initialize user list with all usernames
        refresh_user_list()

        # Close button for the popup
        close_button = MDRaisedButton(
            text="Close",
            on_release=lambda x: user_popup.dismiss()
        )
        close_button.md_bg_color = (0.5, 0.3, 0.8, 1)

        content.add_widget(users_list)
        content.add_widget(close_button)

        user_popup = Popup(
            title="Remove User",
            content=content,
            size_hint=(0.8, 0.6),
            auto_dismiss=True,
        )
        user_popup.open()

    def view_usage_history(self, instance):
        """Display the usage history in a popup."""
        if usage_history:
            history = "\n".join(usage_history)
            create_popup("Usage History", history)
        else:
            create_popup("No History", "No usage history available.")

    # def send_new_password(self, instance):
    #     # Email input field (Initially non-visible)
    #     self.email_input = MDTextField(
    #         hint_text="Enter your email",
    #         size_hint_y=None,
    #         height=50,
    #         pos_hint={"center_x": 0.5},
    #         mode="rectangle"
    #     )
    #     self.email_input.line_color_focus = (0.5, 0.3, 0.8, 1)
    #     self.add_widget(self.email_input)
    #
    #     # Send email button
    #     self.send_email_button = MDRaisedButton(
    #         text="Send",
    #         size_hint_y=None,
    #         height=50,
    #         pos_hint={"center_x": 0.5},
    #         on_release=self.send_email,
    #         disabled=False
    #     )
    #     self.send_email_button.md_bg_color = (0.5, 0.3, 0.8, 1)
    #     self.add_widget(self.send_email_button)

    def send_new_password(self, instance):
        # Check if email input field already exists
        if not hasattr(self, 'email_input'):
            # Email input field (Initially non-visible)
            self.email_input = MDTextField(
                hint_text="Enter your email",
                size_hint_y=None,
                height=50,
                pos_hint={"center_x": 0.5},
                mode="rectangle"
            )
            self.email_input.line_color_focus = (0.5, 0.3, 0.8, 1)
            self.add_widget(self.email_input)

        # Check if send email button already exists
        if not hasattr(self, 'send_email_button'):
            # Send email button
            self.send_email_button = MDRaisedButton(
                text="Send",
                size_hint_y=None,
                height=50,
                pos_hint={"center_x": 0.5},
                on_release=self.send_email,
                disabled=False
            )
            self.send_email_button.md_bg_color = (0.5, 0.3, 0.8, 1)
            self.add_widget(self.send_email_button)

    def generate_password(self):
        """Generate a new 4 digit random password."""
        new_password = str(random.randint(1000, 9999))
        return new_password

    def send_email(self, instance):
        user_email = self.email_input.text

        if not user_email:
            create_popup("Error", "Please enter an email address.")
            return

        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", user_email):
            create_popup("Error", "Please enter a valid email address.")
            return

        def get_email_by_username(username):
            """Get the email address of a user by their username."""
            user_details = users.get(username)
            if user_details and isinstance(user_details, dict):
                return user_details.get("email")
            return None

        # Find the user associated with the email
        user = None
        for username, details in users.items():
            #email = get_email_by_username(username)
            #if email == user_email:
            if isinstance(details, dict) and details.get("email") == user_email:
                user = username
                break

        if not user:
            create_popup("Error", "No user found with this email address.")
            return

        new_password = self.generate_password()  # Generate a new random password

        sender_email = 'smartlock.app@outlook.com'
        sender_password = 'InbarMai'

        try:
            # Create Outlook application instance
            outlook = win32.Dispatch('outlook.application')
            namespace = outlook.GetNamespace('MAPI')

            account = None
            for acc in namespace.Accounts:
                if acc.SmtpAddress.lower() == sender_email.lower():
                    account = acc
                    break

            if not account:
                create_popup("Error", "Outlook account not found.")
                return

            mail = outlook.CreateItem(0)
            mail._oleobj_.Invoke(*(64209, 0, 8, 0, account))
            mail.To = user_email
            mail.Subject = 'Smart Lock - New Password'
            mail.Body = f"Hello,\n\nYour new password is: {new_password}\n\nPlease change it after logging in."
            mail.HTMLBody = f"<h2>Your new password:</h2><p><strong>{new_password}</strong></p><p>Please change it after logging in.</p>"

            # Send the email
            mail.Send()
            create_popup("Success", f"Password sent to {user_email}")

            # Update the user's password in the users dictionary
            users[user]["password"] = new_password

        except Exception as e:
            create_popup("Error", f"Failed to send email: {e}")


    def close_dialog(self, instance=None):
        self.dialog.dismiss()

