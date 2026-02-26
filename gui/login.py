"""Login screen"""
import customtkinter as ctk
from typing import Callable
import threading


class LoginWindow(ctk.CTkToplevel):
    """Login window"""

    def __init__(self, parent, on_login_success: Callable):
        super().__init__(parent)

        self.on_login_success = on_login_success

        # Window settings
        self.title("Claude.ai Login")
        self.geometry("400x280")
        self.resizable(False, False)

        # Center
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.winfo_screenheight() // 2) - (280 // 2)
        self.geometry(f"+{x}+{y}")

        self._create_widgets()

        # Modal
        self.transient(parent)
        self.grab_set()

    def _create_widgets(self):
        """Create widgets"""

        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Claude.ai Login",
            font=ctk.CTkFont(family="Inter", size=24, weight="bold")
        )
        title_label.pack(pady=(30, 10))

        # Description
        desc_label = ctk.CTkLabel(
            self,
            text="A browser will open for you to sign in.\nLogin will be detected automatically.",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color="gray"
        )
        desc_label.pack(pady=(0, 20))

        # Login button
        self.login_button = ctk.CTkButton(
            self,
            text="Sign in with Browser",
            command=self._on_login_click,
            width=320,
            height=50,
            font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
            fg_color="#4299e1",
            hover_color="#3182ce"
        )
        self.login_button.pack(pady=(0, 15))

        # Status label
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color="gray"
        )
        self.status_label.pack(pady=5)

    def _on_login_click(self):
        """Login button clicked"""
        self.status_label.configure(text="Opening browser...", text_color="gray")
        self.login_button.configure(state="disabled")
        self.after(100, self._perform_login)

    def _perform_login(self):
        """Perform login (separate thread)"""
        self.status_label.configure(text="Please sign in from the browser...", text_color="#4299e1")

        def login_thread():
            success = self.on_login_success()
            self.after(0, lambda: self._on_login_complete(success))

        thread = threading.Thread(target=login_thread, daemon=True)
        thread.start()

    def _on_login_complete(self, success: bool):
        """Login complete (main thread)"""
        if success:
            self.status_label.configure(text="Login successful", text_color="green")
            self.grab_release()
            self.after(1000, self.destroy)
        else:
            self.status_label.configure(text="Login failed. Please try again.", text_color="red")
            self.login_button.configure(state="normal")
