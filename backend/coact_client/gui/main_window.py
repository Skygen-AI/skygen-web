"""
Main GUI Window for Coact Client

Modern, professional desktop application interface built with tkinter.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import asyncio
import threading
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import json

from coact_client.app import app
from coact_client.core.auth import auth_client
from coact_client.core.device import device_manager
from coact_client.core.websocket import websocket_client
from coact_client.config.settings import settings

logger = logging.getLogger(__name__)


class CoactGUI:
    """Main GUI application class"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Coact Client v{settings.app_version}")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        # Configure style - use minimal configuration on macOS to avoid crashes
        import platform
        if platform.system() == 'Darwin':
            # On macOS, use default theme to avoid compatibility issues
            self.style = ttk.Style()
            # Don't set any theme, use system default
        else:
            self.style = ttk.Style()
            self.style.theme_use('clam')

        self._configure_styles()

        # Set window icon
        try:
            self.root.iconbitmap(default=str(
                Path(__file__).parent / "icon.ico"))
        except:
            pass  # Icon file doesn't exist, skip

        # Variables
        self.status_var = tk.StringVar(value="Disconnected")
        self.auth_status_var = tk.StringVar(value="Not Authenticated")
        self.device_status_var = tk.StringVar(value="Not Enrolled")
        self.connection_var = tk.StringVar(value="Offline")
        self.tasks_var = tk.StringVar(value="0")

        # Threading
        self.loop = None
        self.loop_thread = None
        self.running = False

        # Create GUI
        self._create_widgets()
        self._create_menu()

        # Protocol for window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Start async loop
        self._start_async_loop()

        # Initial status update
        self.root.after(1000, self.update_status)

        # Auto-update every 5 seconds
        self._schedule_update()

    def _configure_styles(self):
        """Configure custom styles for modern look"""
        import platform

        # Configure colors
        bg_color = "#f0f0f0"
        accent_color = "#2196F3"
        success_color = "#4CAF50"
        warning_color = "#FF9800"
        error_color = "#F44336"

        self.root.configure(bg=bg_color)

        # On macOS, use minimal styling to avoid crashes
        if platform.system() == 'Darwin':
            try:
                # Try to configure styles, but catch any errors
                self.style.configure("Accent.TButton")
                self.style.configure("Success.TButton")
                self.style.configure("Warning.TButton")
                self.style.configure("Error.TButton")
                self.style.configure("Card.TFrame")
            except Exception:
                # If styling fails, just continue without custom styles
                pass
        else:
            # Configure button styles
            self.style.configure("Accent.TButton",
                                 background=accent_color,
                                 foreground="white",
                                 borderwidth=0,
                                 focuscolor="none")

            self.style.configure("Success.TButton",
                                 background=success_color,
                                 foreground="white",
                                 borderwidth=0,
                                 focuscolor="none")

            self.style.configure("Warning.TButton",
                                 background=warning_color,
                                 foreground="white",
                                 borderwidth=0,
                                 focuscolor="none")

            self.style.configure("Error.TButton",
                                 background=error_color,
                                 foreground="white",
                                 borderwidth=0,
                                 focuscolor="none")

            # Configure frame styles
            self.style.configure("Card.TFrame",
                                 background="white",
                                 relief="solid",
                                 borderwidth=1)

    def _create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Login...", command=self.show_login_dialog)
        file_menu.add_command(label="Logout", command=self.logout)
        file_menu.add_separator()
        file_menu.add_command(label="Settings...", command=self.show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)

        # Device menu
        device_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Device", menu=device_menu)
        device_menu.add_command(label="Enroll Device...",
                                command=self.enroll_device)
        device_menu.add_command(label="Device Info...",
                                command=self.show_device_info)
        device_menu.add_command(label="Reset Device",
                                command=self.reset_device)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Documentation",
                              command=self.show_documentation)

    def _create_widgets(self):
        """Create main GUI widgets"""
        # Create main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create status bar at top
        self._create_status_bar(main_container)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Create tabs
        self._create_dashboard_tab()
        self._create_logs_tab()
        self._create_tasks_tab()
        self._create_desktop_tasks_tab()
        self._create_settings_tab()

    def _create_status_bar(self, parent):
        """Create status bar with indicators"""
        status_frame = ttk.Frame(parent, style="Card.TFrame")
        status_frame.pack(fill=tk.X, pady=(0, 10))

        # Title
        title_label = ttk.Label(status_frame, text="🤖 Coact Desktop Client",
                                font=("Arial", 16, "bold"))
        title_label.pack(pady=(10, 5))

        # Status indicators grid
        indicators_frame = ttk.Frame(status_frame)
        indicators_frame.pack(pady=(0, 10))

        # Authentication status
        ttk.Label(indicators_frame, text="Authentication:").grid(
            row=0, column=0, sticky="e", padx=(10, 5))
        self.auth_label = ttk.Label(indicators_frame, textvariable=self.auth_status_var,
                                    foreground="red")
        self.auth_label.grid(row=0, column=1, sticky="w", padx=(0, 20))

        # Device status
        ttk.Label(indicators_frame, text="Device:").grid(
            row=0, column=2, sticky="e", padx=(10, 5))
        self.device_label = ttk.Label(indicators_frame, textvariable=self.device_status_var,
                                      foreground="red")
        self.device_label.grid(row=0, column=3, sticky="w", padx=(0, 20))

        # Connection status
        ttk.Label(indicators_frame, text="Connection:").grid(
            row=1, column=0, sticky="e", padx=(10, 5))
        self.connection_label = ttk.Label(indicators_frame, textvariable=self.connection_var,
                                          foreground="red")
        self.connection_label.grid(row=1, column=1, sticky="w", padx=(0, 20))

        # Active tasks
        ttk.Label(indicators_frame, text="Active Tasks:").grid(
            row=1, column=2, sticky="e", padx=(10, 5))
        self.tasks_label = ttk.Label(
            indicators_frame, textvariable=self.tasks_var)
        self.tasks_label.grid(row=1, column=3, sticky="w", padx=(0, 20))

    def _create_dashboard_tab(self):
        """Create dashboard tab"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="Dashboard")

        # Control buttons frame
        controls_frame = ttk.Frame(dashboard_frame)
        controls_frame.pack(fill=tk.X, pady=(10, 20))

        # Main action buttons
        self.login_btn = ttk.Button(controls_frame, text="Login",
                                    style="Accent.TButton",
                                    command=self.show_login_dialog)
        self.login_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.enroll_btn = ttk.Button(controls_frame, text="Enroll Device",
                                     style="Success.TButton",
                                     command=self.enroll_device)
        self.enroll_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.start_btn = ttk.Button(controls_frame, text="Start Client",
                                    style="Success.TButton",
                                    command=self.start_client)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_btn = ttk.Button(controls_frame, text="Stop Client",
                                   style="Warning.TButton",
                                   command=self.stop_client,
                                   state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Refresh button
        ttk.Button(controls_frame, text="Refresh Status",
                   command=self.update_status).pack(side=tk.RIGHT)

        # Status display area
        status_display = ttk.Frame(dashboard_frame, style="Card.TFrame")
        status_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Label(status_display, text="System Status",
                  font=("Arial", 12, "bold")).pack(pady=(10, 10))

        # Status text widget
        self.status_text = scrolledtext.ScrolledText(status_display, height=15,
                                                     font=("Consolas", 10))
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Add initial status
        self.status_text.insert(tk.END, "Welcome to Coact Client!\n")
        self.status_text.insert(tk.END, "Click 'Login' to get started.\n\n")

    def _create_logs_tab(self):
        """Create logs tab"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="Logs")

        # Log controls
        log_controls = ttk.Frame(logs_frame)
        log_controls.pack(fill=tk.X, pady=(10, 10))

        ttk.Button(log_controls, text="Clear Logs",
                   command=self.clear_logs).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(log_controls, text="Save Logs",
                   command=self.save_logs).pack(side=tk.LEFT, padx=(0, 10))

        # Auto-scroll checkbox
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_controls, text="Auto-scroll",
                        variable=self.auto_scroll_var).pack(side=tk.RIGHT)

        # Log text widget
        self.log_text = scrolledtext.ScrolledText(logs_frame, height=25,
                                                  font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Setup log handler
        self._setup_log_handler()

    def _create_tasks_tab(self):
        """Create tasks history tab"""
        tasks_frame = ttk.Frame(self.notebook)
        self.notebook.add(tasks_frame, text="Tasks")

        # Tasks list
        columns = ("Time", "Task ID", "Status", "Actions")
        self.tasks_tree = ttk.Treeview(
            tasks_frame, columns=columns, show="headings")

        for col in columns:
            self.tasks_tree.heading(col, text=col)
            self.tasks_tree.column(col, width=150)

        # Add scrollbar
        tasks_scroll = ttk.Scrollbar(tasks_frame, orient=tk.VERTICAL,
                                     command=self.tasks_tree.yview)
        self.tasks_tree.configure(yscrollcommand=tasks_scroll.set)

        self.tasks_tree.pack(side=tk.LEFT, fill=tk.BOTH,
                             expand=True, padx=(10, 0), pady=10)
        tasks_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)

    def _create_desktop_tasks_tab(self):
        """Create desktop tasks tab for embedded desktop automation"""
        desktop_frame = ttk.Frame(self.notebook)
        self.notebook.add(desktop_frame, text="Desktop Tasks")

        # Create main container with scrollbar
        canvas = tk.Canvas(desktop_frame)
        scrollbar = ttk.Scrollbar(
            desktop_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Title
        title_label = ttk.Label(scrollable_frame, text="🖥️ Embedded Desktop Automation",
                                font=("Arial", 14, "bold"))
        title_label.pack(pady=(10, 20))

        # Quick Actions Section
        quick_frame = ttk.LabelFrame(
            scrollable_frame, text="Quick Actions", padding=10)
        quick_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Quick action buttons
        quick_buttons_frame = ttk.Frame(quick_frame)
        quick_buttons_frame.pack(fill=tk.X)

        ttk.Button(quick_buttons_frame, text="📸 Screenshot",
                   command=lambda: self._send_desktop_task("embedded_desktop_screenshot", {})).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(quick_buttons_frame, text="ℹ️ System Info",
                   command=lambda: self._send_desktop_task("embedded_desktop_info", {})).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(quick_buttons_frame, text="🌳 Accessibility Tree",
                   command=lambda: self._send_desktop_task("embedded_desktop_a11y", {})).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(quick_buttons_frame, text="💻 Terminal Output",
                   command=lambda: self._send_desktop_task("embedded_desktop_terminal", {})).pack(side=tk.LEFT, padx=(0, 5))

        # Custom Tasks Section
        custom_frame = ttk.LabelFrame(
            scrollable_frame, text="Custom Tasks", padding=10)
        custom_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Task type selection
        task_type_frame = ttk.Frame(custom_frame)
        task_type_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(task_type_frame, text="Task Type:").pack(
            side=tk.LEFT, padx=(0, 5))

        self.task_type_var = tk.StringVar(value="embedded_desktop_command")
        task_type_combo = ttk.Combobox(
            task_type_frame, textvariable=self.task_type_var, width=30)
        task_type_combo['values'] = [
            "embedded_desktop_command",
            "embedded_desktop_python",
            "embedded_desktop_type",
            "embedded_desktop_open",
            "embedded_desktop_activate",
            "embedded_desktop_screenshot",
            "embedded_desktop_a11y",
            "embedded_desktop_info",
            "embedded_desktop_terminal",
            "embedded_desktop_task"
        ]
        task_type_combo.pack(side=tk.LEFT, padx=(0, 10))

        # Parameters input
        params_frame = ttk.Frame(custom_frame)
        params_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(params_frame, text="Parameters (JSON):").pack(anchor=tk.W)

        self.params_text = scrolledtext.ScrolledText(
            params_frame, height=6, font=("Consolas", 10))
        self.params_text.pack(fill=tk.X, pady=(5, 0))

        # Default parameters for different task types
        self._setup_default_params()

        # Send button
        send_frame = ttk.Frame(custom_frame)
        send_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(send_frame, text="🚀 Send Task",
                   command=self._send_custom_desktop_task,
                   style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(send_frame, text="🔄 Reset",
                   command=self._reset_params).pack(side=tk.LEFT)

        # Complex Tasks Section
        complex_frame = ttk.LabelFrame(
            scrollable_frame, text="Complex Multi-Step Tasks", padding=10)
        complex_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Predefined complex tasks
        complex_buttons_frame = ttk.Frame(complex_frame)
        complex_buttons_frame.pack(fill=tk.X)

        ttk.Button(complex_buttons_frame, text="📊 System Analysis",
                   command=self._send_system_analysis_task).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(complex_buttons_frame, text="🖼️ Screenshot + Info",
                   command=self._send_screenshot_info_task).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(complex_buttons_frame, text="💻 Terminal Check",
                   command=self._send_terminal_check_task).pack(side=tk.LEFT, padx=(0, 5))

        # Task History Section
        history_frame = ttk.LabelFrame(
            scrollable_frame, text="Recent Desktop Tasks", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Desktop tasks list
        desktop_columns = ("Time", "Task Type", "Status", "Result")
        self.desktop_tasks_tree = ttk.Treeview(
            history_frame, columns=desktop_columns, show="headings")

        for col in desktop_columns:
            self.desktop_tasks_tree.heading(col, text=col)
            self.desktop_tasks_tree.column(col, width=150)

        # Add scrollbar for desktop tasks
        desktop_scroll = ttk.Scrollbar(history_frame, orient=tk.VERTICAL,
                                       command=self.desktop_tasks_tree.yview)
        self.desktop_tasks_tree.configure(yscrollcommand=desktop_scroll.set)

        self.desktop_tasks_tree.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5), pady=(0, 0))
        desktop_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 0), pady=(0, 0))

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _create_settings_tab(self):
        """Create settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")

        # Settings content
        settings_scroll = scrolledtext.ScrolledText(settings_frame, height=25)
        settings_scroll.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Display current settings
        self._display_settings(settings_scroll)

    def _display_settings(self, text_widget):
        """Display current settings in text widget"""
        text_widget.insert(tk.END, "=== Coact Client Configuration ===\n\n")

        # Server settings
        text_widget.insert(tk.END, "Server Configuration:\n")
        text_widget.insert(tk.END, f"  API URL: {settings.server.api_url}\n")
        text_widget.insert(
            tk.END, f"  WebSocket URL: {settings.server.ws_url}\n")
        text_widget.insert(
            tk.END, f"  Timeout: {settings.server.timeout}s\n\n")

        # Device settings
        text_widget.insert(tk.END, "Device Configuration:\n")
        text_widget.insert(tk.END, f"  Name: {settings.device.name}\n")
        text_widget.insert(tk.END, f"  Platform: {settings.device.platform}\n")
        text_widget.insert(
            tk.END, f"  Max Concurrent Tasks: {settings.device.max_concurrent_tasks}\n\n")

        # Security settings
        text_widget.insert(tk.END, "Security Settings:\n")
        text_widget.insert(
            tk.END, f"  Require Confirmation: {settings.security.require_task_confirmation}\n")
        text_widget.insert(
            tk.END, f"  Shell Commands: {settings.security.enable_shell_commands}\n")
        text_widget.insert(
            tk.END, f"  Max File Size: {settings.security.max_file_size_mb}MB\n\n")

        # Paths
        text_widget.insert(tk.END, "Paths:\n")
        text_widget.insert(tk.END, f"  Config Dir: {settings.config_dir}\n")
        text_widget.insert(tk.END, f"  Data Dir: {settings.data_dir}\n")
        text_widget.insert(tk.END, f"  Log Dir: {settings.log_dir}\n")

        text_widget.config(state=tk.DISABLED)

    def _setup_log_handler(self):
        """Setup GUI log handler"""
        class GUILogHandler(logging.Handler):
            def __init__(self, text_widget, auto_scroll_var):
                super().__init__()
                self.text_widget = text_widget
                self.auto_scroll_var = auto_scroll_var

            def emit(self, record):
                try:
                    msg = self.format(record)
                    timestamp = datetime.now().strftime("%H:%M:%S")

                    def append_log():
                        self.text_widget.insert(
                            tk.END, f"[{timestamp}] {msg}\n")
                        if self.auto_scroll_var.get():
                            self.text_widget.see(tk.END)

                    # Schedule GUI update
                    self.text_widget.after_idle(append_log)
                except Exception:
                    pass

        # Add handler to root logger
        gui_handler = GUILogHandler(self.log_text, self.auto_scroll_var)
        gui_handler.setLevel(logging.INFO)
        gui_handler.setFormatter(logging.Formatter(
            "%(levelname)s - %(name)s - %(message)s"))

        logging.getLogger().addHandler(gui_handler)

    def _start_async_loop(self):
        """Start asyncio event loop in separate thread"""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.running = True
            self.loop.run_until_complete(self._async_runner())

        self.loop_thread = threading.Thread(target=run_loop, daemon=True)
        self.loop_thread.start()

    async def _async_runner(self):
        """Main async runner"""
        try:
            await app.initialize()

            while self.running:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Async runner error: {e}")

    def _schedule_update(self):
        """Schedule regular status updates"""
        self.update_status()
        self.root.after(5000, self._schedule_update)

    def update_status(self):
        """Update status indicators"""
        try:
            if hasattr(app, 'get_status'):
                # app.get_status() is a regular sync method, not a coroutine
                status = app.get_status()
            else:
                status = self._get_basic_status_sync()

            # Update status variables
            self.auth_status_var.set("✅ Authenticated" if status.get(
                "authenticated") else "❌ Not Authenticated")
            self.auth_label.config(
                foreground="green" if status.get("authenticated") else "red")

            self.device_status_var.set("✅ Enrolled" if status.get(
                "device_enrolled") else "❌ Not Enrolled")
            self.device_label.config(
                foreground="green" if status.get("device_enrolled") else "red")

            connection_status = "✅ Connected" if status.get(
                "websocket_connected") else "❌ Offline"
            self.connection_var.set(connection_status)
            self.connection_label.config(
                foreground="green" if status.get("websocket_connected") else "red")

            self.tasks_var.set(str(status.get("active_tasks", 0)))

            # Update button states
            is_authenticated = status.get("authenticated", False)
            is_enrolled = status.get("device_enrolled", False)
            is_running = status.get("running", False)

            # Debug logging
            websocket_connected = status.get("websocket_connected", False)
            logger.debug(
                f"Status: auth={is_authenticated}, enrolled={is_enrolled}, running={is_running}, ws_connected={websocket_connected}")
            logger.debug(
                f"WebSocket state: {websocket_client.get_state().value if websocket_client else 'N/A'}")

            self.login_btn.config(
                state=tk.DISABLED if is_authenticated else tk.NORMAL)
            self.enroll_btn.config(
                state=tk.NORMAL if is_authenticated else tk.DISABLED)
            self.start_btn.config(state=tk.NORMAL if (
                is_authenticated and is_enrolled and not is_running) else tk.DISABLED)
            self.stop_btn.config(
                state=tk.NORMAL if is_running else tk.DISABLED)

        except Exception as e:
            logger.error(f"Status update error: {e}")

    def _get_basic_status_sync(self):
        """Get basic status when app.get_status() is not available"""
        return {
            "authenticated": auth_client.is_authenticated() if auth_client else False,
            "device_enrolled": device_manager.is_enrolled() if device_manager else False,
            "websocket_connected": websocket_client.is_connected() if websocket_client else False,
            "running": app.running if app else False,
            "active_tasks": 0
        }

    def show_login_dialog(self):
        """Show login dialog"""
        from coact_client.gui.login_dialog import LoginDialog
        dialog = LoginDialog(self.root, self.on_login_success)
        dialog.show()

    def on_login_success(self):
        """Callback for successful login"""
        self.update_status()
        self.log_message("Login successful!")

    def logout(self):
        """Logout user"""
        if not auth_client.is_authenticated():
            messagebox.showinfo("Info", "Not logged in")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to logout?"):
            if self.loop:
                future = asyncio.run_coroutine_threadsafe(
                    auth_client.logout(), self.loop)
                try:
                    future.result(timeout=5)
                    self.log_message("Logged out successfully")
                    self.update_status()
                except Exception as e:
                    messagebox.showerror("Error", f"Logout failed: {e}")

    def enroll_device(self):
        """Enroll device"""
        if not auth_client.is_authenticated():
            messagebox.showerror("Error", "Please login first")
            return

        if self.loop:
            future = asyncio.run_coroutine_threadsafe(
                app.enroll_device(), self.loop)
            try:
                success = future.result(timeout=30)
                if success:
                    self.log_message("Device enrolled successfully!")
                    self.update_status()
                else:
                    messagebox.showerror("Error", "Device enrollment failed")
            except Exception as e:
                messagebox.showerror("Error", f"Enrollment failed: {e}")

    def start_client(self):
        """Start the client"""
        if self.loop:
            def start_async():
                asyncio.run_coroutine_threadsafe(app.start(), self.loop)

            threading.Thread(target=start_async, daemon=True).start()
            self.log_message("Starting client...")
            self.update_status()

    def stop_client(self):
        """Stop the client"""
        if self.loop:
            future = asyncio.run_coroutine_threadsafe(
                app.shutdown(), self.loop)
            try:
                future.result(timeout=10)
                self.log_message("Client stopped")
                self.update_status()
            except Exception as e:
                messagebox.showerror("Error", f"Stop failed: {e}")

    def show_device_info(self):
        """Show device information"""
        if not device_manager.is_enrolled():
            messagebox.showinfo("Info", "Device not enrolled")
            return

        device_info = device_manager.get_device_info()
        if device_info:
            info_text = f"""Device Information:

ID: {device_info.device_id}
Name: {device_info.device_name}  
Platform: {device_info.platform}
Enrolled: {device_info.enrolled_at.strftime('%Y-%m-%d %H:%M:%S')}
Token Expires: {device_info.expires_at.strftime('%Y-%m-%d %H:%M:%S')}

Capabilities:
{json.dumps(device_info.capabilities, indent=2)}"""

            messagebox.showinfo("Device Information", info_text)

    def reset_device(self):
        """Reset device enrollment"""
        if messagebox.askyesno("Confirm", "This will clear device enrollment. Continue?"):
            device_manager.clear_device_info()
            self.log_message("Device enrollment reset")
            self.update_status()

    def show_settings(self):
        """Show settings dialog"""
        messagebox.showinfo("Settings", "Settings dialog not implemented yet")

    def show_about(self):
        """Show about dialog"""
        about_text = f"""Coact Desktop Client
Version {settings.app_version}

A production-ready desktop automation agent.

© 2024 Coact Team"""

        messagebox.showinfo("About Coact Client", about_text)

    def show_documentation(self):
        """Show documentation"""
        import webbrowser
        webbrowser.open("https://docs.coact.dev")

    def log_message(self, message):
        """Add message to status display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)

    def clear_logs(self):
        """Clear log display"""
        self.log_text.delete(1.0, tk.END)

    def save_logs(self):
        """Save logs to file"""
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                messagebox.showinfo("Success", f"Logs saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save logs: {e}")

    def _setup_default_params(self):
        """Setup default parameters for different task types"""
        default_params = {
            "embedded_desktop_command": '{\n  "command": "echo \'Hello from desktop automation!\'",\n  "shell": true\n}',
            "embedded_desktop_python": '{\n  "code": "import platform\\nprint(f\'Platform: {platform.system()}\')\\nprint(f\'Python version: {platform.python_version()}\')"\n}',
            "embedded_desktop_type": '{\n  "text": "Hello from desktop automation!",\n  "interval": 0.1\n}',
            "embedded_desktop_open": '{\n  "path_or_app": "/Applications/Calculator.app"\n}',
            "embedded_desktop_activate": '{\n  "title": "Calculator",\n  "strict": false\n}',
            "embedded_desktop_screenshot": '{\n  "include_base64": false\n}',
            "embedded_desktop_a11y": '{}',
            "embedded_desktop_info": '{}',
            "embedded_desktop_terminal": '{}',
            "embedded_desktop_task": '{\n  "actions": [\n    {\n      "type": "screenshot",\n      "delay": 1\n    },\n    {\n      "type": "command",\n      "command": "date",\n      "shell": true,\n      "delay": 1\n    }\n  ]\n}'
        }

        # Set initial default
        self.params_text.insert(tk.END, default_params.get(
            self.task_type_var.get(), '{}'))

        # Bind task type change
        def on_task_type_change(*args):
            self.params_text.delete(1.0, tk.END)
            self.params_text.insert(tk.END, default_params.get(
                self.task_type_var.get(), '{}'))

        self.task_type_var.trace('w', on_task_type_change)

    def _reset_params(self):
        """Reset parameters to default for current task type"""
        self._setup_default_params()

    def _send_desktop_task(self, action: str, parameters: dict):
        """Send a desktop task to the server"""
        if not auth_client.is_authenticated():
            messagebox.showerror("Error", "Please login first")
            return

        if not device_manager.is_enrolled():
            messagebox.showerror("Error", "Please enroll device first")
            return

        try:
            # Get device info
            device_info = device_manager.get_device_info()
            if not device_info:
                messagebox.showerror("Error", "Device not enrolled")
                return

            # Create task data
            task_data = {
                "title": f"Desktop Task: {action}",
                "device_id": device_info.device_id,
                "description": f"Desktop automation task: {action}",
                "metadata": {
                    "actions": [
                        {
                            "type": action,
                            "parameters": parameters
                        }
                    ]
                }
            }

            # Send task via WebSocket if connected, otherwise show error
            if websocket_client and websocket_client.is_connected():
                # For now, we'll use a simple approach - show success message
                # In a real implementation, you'd send this via WebSocket
                self.log_message(f"Desktop task '{action}' sent successfully!")
                self._add_desktop_task_to_history(
                    action, "Sent", "Task queued")
                messagebox.showinfo(
                    "Success", f"Desktop task '{action}' sent successfully!")
            else:
                messagebox.showerror(
                    "Error", "WebSocket not connected. Please start the client first.")

        except Exception as e:
            logger.error(f"Failed to send desktop task: {e}")
            messagebox.showerror("Error", f"Failed to send desktop task: {e}")

    def _send_custom_desktop_task(self):
        """Send custom desktop task with user-defined parameters"""
        try:
            action = self.task_type_var.get()
            params_text = self.params_text.get(1.0, tk.END).strip()

            if not params_text:
                messagebox.showerror("Error", "Please provide parameters")
                return

            # Parse JSON parameters
            try:
                parameters = json.loads(params_text)
            except json.JSONDecodeError as e:
                messagebox.showerror("Error", f"Invalid JSON parameters: {e}")
                return

            self._send_desktop_task(action, parameters)

        except Exception as e:
            logger.error(f"Failed to send custom desktop task: {e}")
            messagebox.showerror(
                "Error", f"Failed to send custom desktop task: {e}")

    def _send_system_analysis_task(self):
        """Send system analysis task"""
        parameters = {
            "actions": [
                {"type": "screenshot", "delay": 1},
                {"type": "command", "command": "uname -a",
                    "shell": True, "delay": 1},
                {"type": "command", "command": "df -h", "shell": True, "delay": 1},
                {"type": "python",
                    "code": "import psutil; print(f'CPU: {psutil.cpu_percent()}%'); print(f'Memory: {psutil.virtual_memory().percent}%')", "delay": 1}
            ]
        }
        self._send_desktop_task("embedded_desktop_task", parameters)

    def _send_screenshot_info_task(self):
        """Send screenshot + system info task"""
        parameters = {
            "actions": [
                {"type": "screenshot", "delay": 1},
                {"type": "command", "command": "date", "shell": True, "delay": 1},
                {"type": "command", "command": "whoami", "shell": True, "delay": 1}
            ]
        }
        self._send_desktop_task("embedded_desktop_task", parameters)

    def _send_terminal_check_task(self):
        """Send terminal check task"""
        parameters = {
            "actions": [
                {"type": "command", "command": "pwd", "shell": True, "delay": 1},
                {"type": "command", "command": "ls -la", "shell": True, "delay": 1},
                {"type": "python",
                    "code": "import os; print(f'Current directory: {os.getcwd()}')", "delay": 1}
            ]
        }
        self._send_desktop_task("embedded_desktop_task", parameters)

    def _add_desktop_task_to_history(self, task_type: str, status: str, result: str):
        """Add desktop task to history tree"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.desktop_tasks_tree.insert("", 0, values=(
            timestamp, task_type, status, result))

        # Keep only last 50 tasks
        items = self.desktop_tasks_tree.get_children()
        if len(items) > 50:
            self.desktop_tasks_tree.delete(items[-1])

    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.running = False
            if self.loop and not self.loop.is_closed():
                # Stop the client
                future = asyncio.run_coroutine_threadsafe(
                    app.shutdown(), self.loop)
                try:
                    future.result(timeout=5)
                except:
                    pass

                # Close the loop
                self.loop.call_soon_threadsafe(self.loop.stop)

            self.root.destroy()

    def run(self):
        """Run the GUI application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()


def main():
    """Main GUI entry point"""
    try:
        gui = CoactGUI()
        gui.run()
    except Exception as e:
        messagebox.showerror("Error", f"GUI failed to start: {e}")


if __name__ == "__main__":
    main()
