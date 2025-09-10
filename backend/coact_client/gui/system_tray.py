"""
System Tray Integration for Coact Client

Provides system tray icon with context menu for quick access.
"""

import tkinter as tk
from tkinter import messagebox
import sys
import threading
from typing import Optional, Callable

try:
    import pystray
    from pystray import MenuItem as item
    from PIL import Image, ImageDraw
    HAS_TRAY_SUPPORT = True
except ImportError:
    HAS_TRAY_SUPPORT = False

from coact_client.core.auth import auth_client
from coact_client.core.device import device_manager
from coact_client.core.websocket import websocket_client
from coact_client.app import app
from coact_client.config.settings import settings


class SystemTray:
    """System tray integration"""
    
    def __init__(self, show_gui_callback: Optional[Callable] = None):
        self.show_gui_callback = show_gui_callback
        self.icon = None
        self.running = False
        
        if not HAS_TRAY_SUPPORT:
            print("⚠️  System tray support not available (pystray not installed)")
            return
    
    def create_icon_image(self, connected: bool = False) -> Image.Image:
        """Create tray icon image"""
        # Create a simple icon
        width = 64
        height = 64
        
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        
        # Draw robot icon
        color = "#4CAF50" if connected else "#9E9E9E"
        
        # Robot head
        dc.ellipse([16, 8, 48, 40], fill=color)
        
        # Eyes
        dc.ellipse([22, 18, 28, 24], fill="white")
        dc.ellipse([36, 18, 42, 24], fill="white")
        
        # Mouth
        dc.arc([26, 26, 38, 32], 0, 180, fill="white", width=2)
        
        # Body
        dc.rectangle([20, 36, 44, 56], fill=color)
        
        # Connection indicator
        if connected:
            dc.ellipse([50, 50, 62, 62], fill="#4CAF50")
        
        return image
    
    def create_menu(self) -> pystray.Menu:
        """Create context menu"""
        return pystray.Menu(
            item("Show Coact Client", self.show_gui, default=True),
            pystray.Menu.SEPARATOR,
            item("Status", self.show_status),
            item("Connect", self.connect, visible=lambda item: not self.is_connected()),
            item("Disconnect", self.disconnect, visible=lambda item: self.is_connected()),
            pystray.Menu.SEPARATOR,
            item("Login", self.login, visible=lambda item: not self.is_authenticated()),
            item("Logout", self.logout, visible=lambda item: self.is_authenticated()),
            pystray.Menu.SEPARATOR,
            item("Settings", self.show_settings),
            item("About", self.show_about),
            pystray.Menu.SEPARATOR,
            item("Exit", self.quit_application)
        )
    
    def start(self):
        """Start system tray"""
        if not HAS_TRAY_SUPPORT:
            return
        
        self.running = True
        
        # Create icon
        image = self.create_icon_image()
        menu = self.create_menu()
        
        self.icon = pystray.Icon(
            "coact-client",
            image,
            "Coact Client",
            menu
        )
        
        # Start in separate thread
        def run_tray():
            self.icon.run()
        
        tray_thread = threading.Thread(target=run_tray, daemon=True)
        tray_thread.start()
        
        # Update icon periodically
        self._schedule_icon_update()
    
    def _schedule_icon_update(self):
        """Schedule periodic icon updates"""
        if not self.running or not self.icon:
            return
        
        try:
            # Update icon based on connection status
            connected = self.is_connected()
            new_image = self.create_icon_image(connected)
            
            if self.icon.icon != new_image:
                self.icon.icon = new_image
            
            # Update tooltip
            status_parts = []
            if self.is_authenticated():
                status_parts.append("Authenticated")
            if device_manager.is_enrolled():
                status_parts.append("Enrolled")
            if connected:
                status_parts.append("Connected")
            
            if status_parts:
                tooltip = f"Coact Client - {', '.join(status_parts)}"
            else:
                tooltip = "Coact Client - Offline"
            
            if self.icon.title != tooltip:
                self.icon.title = tooltip
                
        except Exception as e:
            print(f"Tray update error: {e}")
        
        # Schedule next update
        if self.running:
            threading.Timer(5.0, self._schedule_icon_update).start()
    
    def stop(self):
        """Stop system tray"""
        self.running = False
        if self.icon:
            self.icon.stop()
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        try:
            return auth_client.is_authenticated()
        except:
            return False
    
    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        try:
            return websocket_client.is_connected()
        except:
            return False
    
    def show_gui(self, icon=None, item=None):
        """Show main GUI"""
        if self.show_gui_callback:
            self.show_gui_callback()
        else:
            # Show basic message
            self._show_notification("Coact Client", "GUI not available")
    
    def show_status(self, icon=None, item=None):
        """Show status information"""
        try:
            auth_status = "✅ Authenticated" if self.is_authenticated() else "❌ Not Authenticated"
            device_status = "✅ Enrolled" if device_manager.is_enrolled() else "❌ Not Enrolled"
            connection_status = "✅ Connected" if self.is_connected() else "❌ Offline"
            
            status_text = f"""Coact Client Status

{auth_status}
{device_status}
{connection_status}

Version: {settings.app_version}
Environment: {settings.environment}"""
            
            self._show_notification("Status", status_text)
            
        except Exception as e:
            self._show_notification("Error", f"Status check failed: {e}")
    
    def connect(self, icon=None, item=None):
        """Connect to server"""
        try:
            if not self.is_authenticated():
                self._show_notification("Error", "Please login first")
                return
            
            if not device_manager.is_enrolled():
                self._show_notification("Error", "Please enroll device first")
                return
            
            # Start connection in background
            def start_client():
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(app.start())
                except Exception as e:
                    self._show_notification("Error", f"Connection failed: {e}")
            
            threading.Thread(target=start_client, daemon=True).start()
            self._show_notification("Connecting", "Starting connection...")
            
        except Exception as e:
            self._show_notification("Error", f"Connection failed: {e}")
    
    def disconnect(self, icon=None, item=None):
        """Disconnect from server"""
        try:
            # Stop client in background
            def stop_client():
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(app.shutdown())
                except Exception as e:
                    self._show_notification("Error", f"Disconnect failed: {e}")
            
            threading.Thread(target=stop_client, daemon=True).start()
            self._show_notification("Disconnecting", "Stopping connection...")
            
        except Exception as e:
            self._show_notification("Error", f"Disconnect failed: {e}")
    
    def login(self, icon=None, item=None):
        """Show login prompt"""
        self._show_notification("Login", "Please use the GUI application to login")
    
    def logout(self, icon=None, item=None):
        """Logout user"""
        try:
            def do_logout():
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(auth_client.logout())
            
            threading.Thread(target=do_logout, daemon=True).start()
            self._show_notification("Logout", "Logged out successfully")
            
        except Exception as e:
            self._show_notification("Error", f"Logout failed: {e}")
    
    def show_settings(self, icon=None, item=None):
        """Show settings"""
        self._show_notification("Settings", "Please use the GUI application for settings")
    
    def show_about(self, icon=None, item=None):
        """Show about information"""
        about_text = f"""Coact Desktop Client
Version {settings.app_version}

A production-ready desktop automation agent.

© 2024 Coact Team"""
        
        self._show_notification("About", about_text)
    
    def quit_application(self, icon=None, item=None):
        """Quit application"""
        self.stop()
        
        # Stop the main app
        try:
            def stop_app():
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(app.shutdown())
            
            threading.Thread(target=stop_app, daemon=True).start()
        except:
            pass
        
        # Exit
        import os
        os._exit(0)
    
    def _show_notification(self, title: str, message: str):
        """Show notification message"""
        if self.icon:
            self.icon.notify(message, title)
        else:
            print(f"{title}: {message}")


# Global tray instance
system_tray = SystemTray()