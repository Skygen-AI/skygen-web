"""
Shell command execution module

Handles secure execution of shell commands with safety checks.
"""

import asyncio
import logging
import subprocess
import os
import shlex
from typing import Dict, Any, List, Optional
from pathlib import Path

from coact_client.config.settings import settings

logger = logging.getLogger(__name__)


class ShellError(Exception):
    """Shell execution errors"""
    pass


class ShellModule:
    """Shell command execution module"""
    
    def __init__(self):
        self.enabled = settings.security.enable_shell_commands
        self.whitelist = set(settings.security.shell_whitelist)
        self.timeout = 60  # Default timeout in seconds
        self.max_output_size = 1024 * 1024  # 1MB max output
        
        # Dangerous commands that should never be allowed
        self.blacklist = {
            "rm", "rmdir", "del", "format", "fdisk",
            "dd", "mkfs", "parted", "gparted",
            "sudo", "su", "chmod", "chown",
            "passwd", "useradd", "userdel", "usermod",
            "systemctl", "service", "init",
            "reboot", "shutdown", "halt", "poweroff",
            "iptables", "ufw", "firewall-cmd",
            "crontab", "at", "batch",
        }
        
        if not self.enabled:
            logger.warning("Shell command execution is disabled in configuration")
    
    async def execute_command(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute shell command with safety checks"""
        if not self.enabled:
            raise ShellError("Shell command execution is disabled")
        
        command = action.get("command", "").strip()
        if not command:
            raise ShellError("No command provided")
        
        # Security checks
        self._validate_command(command)
        
        try:
            # Get execution parameters
            timeout = min(action.get("timeout", self.timeout), 300)  # Max 5 minutes
            working_dir = action.get("working_dir")
            env_vars = action.get("env_vars", {})
            capture_output = action.get("capture_output", True)
            
            # Validate working directory
            if working_dir:
                working_dir = Path(working_dir)
                if not working_dir.exists() or not working_dir.is_dir():
                    raise ShellError(f"Invalid working directory: {working_dir}")
            
            # Prepare environment
            env = os.environ.copy()
            if env_vars:
                env.update(env_vars)
            
            logger.info(f"Executing command: {command}")
            
            # Execute command
            if capture_output:
                result = await self._execute_with_output(command, timeout, working_dir, env)
            else:
                result = await self._execute_without_output(command, timeout, working_dir, env)
            
            logger.info(f"Command completed with exit code: {result['exit_code']}")
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Command timed out: {command}")
            raise ShellError(f"Command timed out after {timeout} seconds")
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            raise ShellError(f"Command execution failed: {e}")
    
    def _validate_command(self, command: str) -> None:
        """Validate command against security policies"""
        # Parse command to get the base command
        try:
            parsed = shlex.split(command)
        except ValueError as e:
            raise ShellError(f"Invalid command syntax: {e}")
        
        if not parsed:
            raise ShellError("Empty command")
        
        base_command = parsed[0]
        
        # Remove path components to get just the command name
        command_name = os.path.basename(base_command)
        
        # Check blacklist
        if command_name in self.blacklist:
            raise ShellError(f"Command '{command_name}' is not allowed")
        
        # Check whitelist (if not empty)
        if self.whitelist and command_name not in self.whitelist:
            # Allow if command starts with whitelisted command
            if not any(command.startswith(allowed) for allowed in self.whitelist):
                raise ShellError(f"Command '{command_name}' is not in whitelist")
        
        # Check for dangerous patterns
        dangerous_patterns = [
            "> /dev/", "rm -rf", ":(){ :|:& };:", 
            "curl", "wget", "nc ", "netcat",
            "python -c", "perl -e", "ruby -e"
        ]
        
        command_lower = command.lower()
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                raise ShellError(f"Command contains dangerous pattern: {pattern}")
    
    async def _execute_with_output(self, command: str, timeout: int, 
                                 working_dir: Optional[Path], env: Dict[str, str]) -> Dict[str, Any]:
        """Execute command and capture output"""
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir,
            env=env,
            limit=self.max_output_size
        )
        
        try:
            stdout_data, stderr_data = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            # Decode output
            stdout = stdout_data.decode('utf-8', errors='replace')
            stderr = stderr_data.decode('utf-8', errors='replace')
            
            # Truncate if too long
            if len(stdout) > self.max_output_size:
                stdout = stdout[:self.max_output_size] + "\n... (output truncated)"
            if len(stderr) > self.max_output_size:
                stderr = stderr[:self.max_output_size] + "\n... (output truncated)"
            
            return {
                "success": process.returncode == 0,
                "exit_code": process.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "command": command
            }
            
        except asyncio.TimeoutError:
            # Kill the process if it's still running
            if process.returncode is None:
                process.kill()
                await process.wait()
            raise
    
    async def _execute_without_output(self, command: str, timeout: int,
                                    working_dir: Optional[Path], env: Dict[str, str]) -> Dict[str, Any]:
        """Execute command without capturing output"""
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=working_dir,
            env=env
        )
        
        try:
            exit_code = await asyncio.wait_for(process.wait(), timeout=timeout)
            
            return {
                "success": exit_code == 0,
                "exit_code": exit_code,
                "stdout": "",
                "stderr": "",
                "command": command
            }
            
        except asyncio.TimeoutError:
            # Kill the process if it's still running
            if process.returncode is None:
                process.kill()
                await process.wait()
            raise
    
    async def get_system_info(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Get basic system information using safe commands"""
        if not self.enabled:
            return {"success": False, "error": "Shell commands disabled"}
        
        try:
            info_commands = {
                "os": "uname -a",
                "user": "whoami",
                "pwd": "pwd",
                "date": "date",
                "uptime": "uptime" if os.name != "nt" else "systeminfo | findstr /C:\"System Boot Time\"",
                "disk_usage": "df -h" if os.name != "nt" else "dir /-c",
                "processes": "ps aux | head -10" if os.name != "nt" else "tasklist | head -10",
            }
            
            results = {}
            
            for info_type, command in info_commands.items():
                try:
                    # Execute safe info commands
                    process = await asyncio.create_subprocess_shell(
                        command,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        limit=8192  # Smaller limit for info commands
                    )
                    
                    stdout_data, stderr_data = await asyncio.wait_for(
                        process.communicate(),
                        timeout=10  # Short timeout for info commands
                    )
                    
                    if process.returncode == 0:
                        results[info_type] = stdout_data.decode('utf-8', errors='replace').strip()
                    else:
                        results[info_type] = f"Error: {stderr_data.decode('utf-8', errors='replace').strip()}"
                
                except Exception as e:
                    results[info_type] = f"Failed: {str(e)}"
            
            return {
                "success": True,
                "system_info": results
            }
            
        except Exception as e:
            logger.error(f"System info gathering failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get shell module configuration"""
        return {
            "enabled": self.enabled,
            "whitelist": list(self.whitelist),
            "blacklist": list(self.blacklist),
            "timeout": self.timeout,
            "max_output_size": self.max_output_size
        }


# Global shell module instance
shell_module = ShellModule()