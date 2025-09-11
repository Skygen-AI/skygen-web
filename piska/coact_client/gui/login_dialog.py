"""
Login Dialog for Coact Client GUI

Professional login dialog with email/password authentication.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
import threading
from typing import Callable, Optional

from coact_client.app import app


class LoginDialog:
    """Professional login dialog"""
    
    def __init__(self, parent, success_callback: Optional[Callable] = None):
        self.parent = parent
        self.success_callback = success_callback
        self.dialog = None
        self.email_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.remember_var = tk.BooleanVar(value=True)
        self.result = False
    
    def show(self):
        """Show the login dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Login to Coact")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50,
            self.parent.winfo_rooty() + 50
        ))
        
        self._create_widgets()
        
        # Focus on email field
        self.email_entry.focus()
        
        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
        
        # Bind Enter key to login
        self.dialog.bind('<Return>', lambda e: self.login())
        
        # Wait for dialog to close
        self.dialog.wait_window()
        
        return self.result
    
    def _create_widgets(self):
        """Create dialog widgets"""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_frame, text="🤖 Coact Login", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Description
        desc_label = ttk.Label(main_frame, 
                              text="Sign in to your Coact account to continue",
                              font=("Arial", 10))
        desc_label.pack(pady=(0, 20))
        
        # Form frame
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Email field
        ttk.Label(form_frame, text="Email:").pack(anchor=tk.W, pady=(0, 5))
        self.email_entry = ttk.Entry(form_frame, textvariable=self.email_var, 
                                    font=("Arial", 11), width=30)
        self.email_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Password field
        ttk.Label(form_frame, text="Password:").pack(anchor=tk.W, pady=(0, 5))
        self.password_entry = ttk.Entry(form_frame, textvariable=self.password_var,
                                       show="*", font=("Arial", 11), width=30)
        self.password_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Remember checkbox
        ttk.Checkbutton(form_frame, text="Remember credentials", 
                       variable=self.remember_var).pack(anchor=tk.W, pady=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(form_frame, text="", foreground="red")
        self.status_label.pack(pady=(0, 10))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X)
        
        # Cancel button
        ttk.Button(buttons_frame, text="Cancel", 
                  command=self.cancel).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Login button
        self.login_button = ttk.Button(buttons_frame, text="Login", 
                                      command=self.login)
        self.login_button.pack(side=tk.RIGHT)
        
        # Progress bar (initially hidden)
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        
        # Alternative login frame
        alt_frame = ttk.Frame(main_frame)
        alt_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Separator(alt_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 10))
        
        signup_frame = ttk.Frame(alt_frame)
        signup_frame.pack()
        
        ttk.Label(signup_frame, text="Don't have an account?").pack(side=tk.LEFT)
        signup_btn = ttk.Label(signup_frame, text="Sign up here", 
                              foreground="blue", cursor="hand2")
        signup_btn.pack(side=tk.LEFT, padx=(5, 0))
        signup_btn.bind("<Button-1>", self.show_signup)
    
    def show_signup(self, event):
        """Show signup information"""
        messagebox.showinfo("Sign Up", 
                           "Please visit https://coact.dev to create an account")
    
    def login(self):
        """Perform login"""
        email = self.email_var.get().strip()
        password = self.password_var.get()
        
        if not email:
            self.status_label.config(text="Please enter your email")
            self.email_entry.focus()
            return
        
        if not password:
            self.status_label.config(text="Please enter your password")
            self.password_entry.focus()
            return
        
        # Disable form and show progress
        self._set_form_state(False)
        self.progress.pack(pady=(10, 0))
        self.progress.start()
        self.status_label.config(text="Authenticating...")
        
        # Perform login in background thread
        threading.Thread(target=self._do_login, args=(email, password), daemon=True).start()
    
    def _set_form_state(self, enabled: bool):
        """Enable or disable form elements"""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.email_entry.config(state=state)
        self.password_entry.config(state=state)
        self.login_button.config(state=state)
    
    def _do_login(self, email: str, password: str):
        """Perform login in background thread"""
        try:
            # Get event loop from main thread
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # No loop in current thread, try to get from main app
                import threading
                main_thread = threading.main_thread()
                if hasattr(main_thread, 'loop'):
                    loop = main_thread.loop
            
            if loop and not loop.is_closed():
                # Use existing loop
                future = asyncio.run_coroutine_threadsafe(
                    app.authenticate(email, password), loop)
                success = future.result(timeout=30)
            else:
                # Create new loop for this thread
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    success = new_loop.run_until_complete(
                        app.authenticate(email, password))
                finally:
                    new_loop.close()
            
            # Schedule GUI update
            self.dialog.after(0, self._on_login_result, success, None)
            
        except Exception as e:
            # Schedule error display
            self.dialog.after(0, self._on_login_result, False, str(e))
    
    def _on_login_result(self, success: bool, error: Optional[str]):
        """Handle login result in main thread"""
        self.progress.stop()
        self.progress.pack_forget()
        self._set_form_state(True)
        
        if success:
            self.status_label.config(text="Login successful!", foreground="green")
            self.result = True
            
            # Call success callback
            if self.success_callback:
                self.success_callback()
            
            # Close dialog after short delay
            self.dialog.after(1000, self.close)
        else:
            error_msg = error or "Login failed"
            self.status_label.config(text=error_msg, foreground="red")
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus()
    
    def cancel(self):
        """Cancel login"""
        self.result = False
        self.close()
    
    def close(self):
        """Close dialog"""
        if self.dialog:
            self.dialog.grab_release()
            self.dialog.destroy()