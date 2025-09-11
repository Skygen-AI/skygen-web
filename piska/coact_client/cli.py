"""
Command Line Interface for Coact Client

Provides CLI commands for managing the Coact desktop client.
"""

import asyncio
import sys
import getpass
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

from coact_client.app import app
from coact_client.config.settings import settings
from coact_client.core.auth import auth_client
from coact_client.core.device import device_manager
from coact_client.utils.logging import setup_logging

console = Console()


def async_command(f):
    """Decorator to run async functions in click commands"""
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--config", type=click.Path(), help="Path to config file")
def cli(debug: bool, config: Optional[str]):
    """Coact Desktop Client - Automated task execution agent"""
    if debug:
        settings.debug = True
        settings.logging.level = "DEBUG"
    
    if config:
        # TODO: Load custom config file
        pass
    
    # Setup logging
    setup_logging()


@cli.command()
@click.option("--email", prompt=True, help="User email")
@click.option("--password", prompt=True, hide_input=True, help="User password")
@async_command
async def login(email: str, password: str):
    """Login to Coact account"""
    console.print("🔐 Logging in to Coact...", style="blue")
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("Authenticating...", total=None)
        
        try:
            success = await app.authenticate(email, password)
            if success:
                console.print("✅ Login successful!", style="green")
                console.print(f"User: {auth_client.get_current_email()}")
            else:
                console.print("❌ Login failed", style="red")
                sys.exit(1)
        except Exception as e:
            console.print(f"❌ Login error: {e}", style="red")
            sys.exit(1)


@cli.command()
@async_command
async def logout():
    """Logout from Coact account"""
    console.print("🔓 Logging out...", style="blue")
    
    try:
        async with auth_client:
            await auth_client.logout()
        console.print("✅ Logged out successfully", style="green")
    except Exception as e:
        console.print(f"❌ Logout error: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option("--force", is_flag=True, help="Force re-enrollment")
@async_command
async def enroll(force: bool):
    """Enroll this device with Coact server"""
    console.print("📱 Enrolling device...", style="blue")
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("Enrolling device...", total=None)
        
        try:
            await app.initialize()
            success = await app.enroll_device(force=force)
            if success:
                device_info = device_manager.get_device_info()
                console.print("✅ Device enrolled successfully!", style="green")
                console.print(f"Device ID: {device_info.device_id}")
                console.print(f"Device Name: {device_info.device_name}")
                console.print(f"Platform: {device_info.platform}")
            else:
                console.print("❌ Device enrollment failed", style="red")
                sys.exit(1)
        except Exception as e:
            console.print(f"❌ Enrollment error: {e}", style="red")
            sys.exit(1)


@cli.command()
@async_command
async def start():
    """Start the Coact client daemon"""
    console.print("🚀 Starting Coact Client...", style="blue")
    
    try:
        await app.initialize()
        
        # Check prerequisites
        if not auth_client.is_authenticated():
            console.print("❌ Not authenticated. Please run 'coact login' first.", style="red")
            sys.exit(1)
        
        if not device_manager.is_enrolled():
            console.print("❌ Device not enrolled. Please run 'coact enroll' first.", style="red")
            sys.exit(1)
        
        console.print("✅ Starting client daemon...", style="green")
        await app.start()
        
    except KeyboardInterrupt:
        console.print("\n⏹️  Stopping client...", style="yellow")
    except Exception as e:
        console.print(f"❌ Client error: {e}", style="red")
        sys.exit(1)
    finally:
        await app.shutdown()


@cli.command()
@async_command
async def status():
    """Show client status and information"""
    try:
        await app.initialize()
        status_info = app.get_status()
        
        # Create status table
        table = Table(title="Coact Client Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        # Add status rows
        table.add_row("Version", status_info["version"])
        table.add_row("Environment", status_info["environment"])
        table.add_row("Running", "✅ Yes" if status_info["running"] else "❌ No")
        table.add_row("Authenticated", "✅ Yes" if status_info["authenticated"] else "❌ No")
        table.add_row("Device Enrolled", "✅ Yes" if status_info["device_enrolled"] else "❌ No")
        table.add_row("WebSocket Connected", "✅ Yes" if status_info["websocket_connected"] else "❌ No")
        table.add_row("WebSocket State", status_info["websocket_state"])
        table.add_row("Active Tasks", str(status_info["active_tasks"]))
        table.add_row("Supported Actions", str(len(status_info["supported_actions"])))
        
        console.print(table)
        
        # Show device info if enrolled
        if status_info["device_enrolled"]:
            device_info = device_manager.get_device_info()
            if device_info:
                device_panel = Panel(
                    f"ID: {device_info.device_id}\n"
                    f"Name: {device_info.device_name}\n"
                    f"Platform: {device_info.platform}\n"
                    f"Enrolled: {device_info.enrolled_at.strftime('%Y-%m-%d %H:%M:%S')}",
                    title="Device Information",
                    border_style="blue"
                )
                console.print(device_panel)
        
        # Show supported actions
        if status_info["supported_actions"]:
            actions_text = ", ".join(sorted(status_info["supported_actions"]))
            actions_panel = Panel(
                actions_text,
                title="Supported Actions",
                border_style="green"
            )
            console.print(actions_panel)
            
    except Exception as e:
        console.print(f"❌ Status error: {e}", style="red")
        sys.exit(1)


@cli.command()
@async_command
async def metrics():
    """Show performance metrics"""
    try:
        await app.initialize()
        metrics_data = app.get_metrics()
        
        if not metrics_data:
            console.print("No metrics available", style="yellow")
            return
        
        # Create metrics table
        table = Table(title="Performance Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Latest Value", style="blue")
        
        for metric_name, metric_values in metrics_data.items():
            if metric_values:
                count = len(metric_values)
                latest_value = metric_values[-1]["value"]
                table.add_row(metric_name, str(count), f"{latest_value:.3f}")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ Metrics error: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option("--all", is_flag=True, help="Clear all data including credentials")
@async_command
async def reset(all: bool):
    """Reset client data"""
    if all:
        console.print("⚠️  This will clear ALL data including credentials!", style="red")
        if not click.confirm("Are you sure?"):
            return
    
    try:
        # Clear device enrollment
        device_manager.clear_device_info()
        console.print("✅ Device enrollment cleared", style="green")
        
        if all:
            # Clear credentials
            async with auth_client:
                await auth_client.logout()
            console.print("✅ Credentials cleared", style="green")
            
            # Clear logs and cache
            if settings.log_dir.exists():
                for log_file in settings.log_dir.glob("*.log*"):
                    log_file.unlink(missing_ok=True)
            
            if settings.cache_dir.exists():
                for cache_file in settings.cache_dir.glob("*"):
                    if cache_file.is_file():
                        cache_file.unlink(missing_ok=True)
            
            console.print("✅ Logs and cache cleared", style="green")
        
        console.print("🔄 Reset complete", style="blue")
        
    except Exception as e:
        console.print(f"❌ Reset error: {e}", style="red")
        sys.exit(1)


@cli.command()
def config():
    """Show configuration information"""
    try:
        # Show configuration paths
        paths_table = Table(title="Configuration Paths")
        paths_table.add_column("Type", style="cyan")
        paths_table.add_column("Path", style="green")
        
        paths_table.add_row("Config Directory", str(settings.config_dir))
        paths_table.add_row("Data Directory", str(settings.data_dir))
        paths_table.add_row("Cache Directory", str(settings.cache_dir))
        paths_table.add_row("Log Directory", str(settings.log_dir))
        paths_table.add_row("Config File", str(settings.get_config_file()))
        paths_table.add_row("Credentials File", str(settings.get_credentials_file()))
        paths_table.add_row("Log File", str(settings.get_log_file()))
        
        console.print(paths_table)
        
        # Show server configuration
        server_panel = Panel(
            f"API URL: {settings.server.api_url}\n"
            f"WebSocket URL: {settings.server.ws_url}\n"
            f"Timeout: {settings.server.timeout}s\n"
            f"Max Retries: {settings.server.max_retries}\n"
            f"Verify SSL: {settings.server.verify_ssl}",
            title="Server Configuration",
            border_style="blue"
        )
        console.print(server_panel)
        
        # Show security settings
        security_panel = Panel(
            f"Require Task Confirmation: {settings.security.require_task_confirmation}\n"
            f"Enable Shell Commands: {settings.security.enable_shell_commands}\n"
            f"Max File Size: {settings.security.max_file_size_mb}MB\n"
            f"Allowed Extensions: {', '.join(settings.security.allowed_file_extensions)}",
            title="Security Settings",
            border_style="yellow"
        )
        console.print(security_panel)
        
    except Exception as e:
        console.print(f"❌ Config error: {e}", style="red")
        sys.exit(1)


@cli.command()
def version():
    """Show version information"""
    version_info = f"""
    🤖 Coact Desktop Client
    
    Version: {settings.app_version}
    Environment: {settings.environment}
    Python: {sys.version.split()[0]}
    Platform: {sys.platform}
    
    © 2024 Coact Team
    """
    
    console.print(Panel(version_info.strip(), title="Version Information", border_style="blue"))


def main():
    """Main CLI entry point"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n⏹️  Interrupted", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    main()