#!/usr/bin/env python3
"""
GUI Main Entry Point for Coact Client

Launches the graphical user interface version of Coact Client.
"""

import sys
import os
import logging
import argparse
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:
    print("❌ tkinter not available. GUI mode requires tkinter.")
    sys.exit(1)

from coact_client.config.settings import settings
from coact_client.utils.logging import setup_logging
from coact_client.gui.main_window import CoactGUI
from coact_client.gui.system_tray import system_tray, HAS_TRAY_SUPPORT


def check_dependencies():
    """Check if all GUI dependencies are available"""
    missing_deps = []
    
    try:
        import tkinter
    except ImportError:
        missing_deps.append("tkinter")
    
    try:
        from PIL import Image
    except ImportError:
        missing_deps.append("Pillow")
    
    if missing_deps:
        print(f"❌ Missing GUI dependencies: {', '.join(missing_deps)}")
        print("Please install them with: pip install Pillow")
        return False
    
    return True


def main():
    """Main GUI application entry point"""
    parser = argparse.ArgumentParser(description="Coact Client GUI")
    parser.add_argument("--tray-only", action="store_true", 
                       help="Run only in system tray (no main window)")
    parser.add_argument("--no-tray", action="store_true",
                       help="Disable system tray integration")
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug mode")
    parser.add_argument("--log-level", default="INFO",
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Set logging level")
    
    args = parser.parse_args()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Configure settings
    if args.debug:
        settings.debug = True
        settings.logging.level = "DEBUG"
    else:
        settings.logging.level = args.log_level
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting Coact Client GUI v{settings.app_version}")
    
    try:
        # System tray only mode
        if args.tray_only:
            if not HAS_TRAY_SUPPORT:
                print("❌ System tray support not available")
                sys.exit(1)
            
            logger.info("Running in system tray only mode")
            system_tray.start()
            
            # Keep the main thread alive
            try:
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                system_tray.stop()
            
            return
        
        # Normal GUI mode
        gui_app = None
        
        def show_gui():
            """Show the main GUI window"""
            nonlocal gui_app
            if gui_app and gui_app.root.winfo_exists():
                gui_app.root.deiconify()
                gui_app.root.lift()
            else:
                if gui_app is None:
                    gui_app = CoactGUI()
                gui_app.root.mainloop()
        
        # Start system tray if available and not disabled
        # Temporarily disabled on macOS due to compatibility issues
        import platform
        if HAS_TRAY_SUPPORT and not args.no_tray and platform.system() != 'Darwin':
            system_tray.show_gui_callback = show_gui
            system_tray.start()
            logger.info("System tray started")
        elif platform.system() == 'Darwin':
            logger.info("System tray disabled on macOS due to compatibility issues")
        
        # Show main GUI
        show_gui()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"GUI application failed: {e}")
        
        # Show error dialog if possible
        try:
            root = tk.Tk()
            root.withdraw()  # Hide the root window
            messagebox.showerror("Error", f"Coact Client GUI failed to start:\n\n{e}")
            root.destroy()
        except:
            print(f"❌ GUI Error: {e}")
        
        sys.exit(1)
    finally:
        # Clean shutdown
        try:
            if HAS_TRAY_SUPPORT:
                system_tray.stop()
        except:
            pass


if __name__ == "__main__":
    main()