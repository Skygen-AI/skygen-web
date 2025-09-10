"""
Desktop Environment Control Module

Integrates desktop_env library to provide full desktop automation capabilities
through virtual machine environments.
"""

import asyncio
import logging
import tempfile
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
import threading
from datetime import datetime

from coact_client.config.settings import settings

logger = logging.getLogger(__name__)

try:
    from desktop_env.desktop_env import DesktopEnv
    HAS_DESKTOP_ENV = True
except ImportError:
    HAS_DESKTOP_ENV = False
    logger.warning("desktop_env library not available")


class DesktopEnvError(Exception):
    """Desktop environment specific errors"""
    pass


class DesktopEnvModule:
    """Desktop Environment Control Module
    
    This module provides advanced desktop automation capabilities through
    the desktop_env library, including VM management and complex task execution.
    """
    
    def __init__(self, 
                 provider_name: str = "vmware",
                 vm_path: str = None,
                 headless: bool = True,
                 action_space: str = "pyautogui"):
        """Initialize Desktop Environment Module
        
        Args:
            provider_name: VM provider (vmware, virtualbox, docker, aws, etc.)
            vm_path: Path to VM file or VM identifier
            headless: Whether to run VM in headless mode
            action_space: Action space to use (pyautogui, computer_13, etc.)
        """
        self.provider_name = provider_name
        self.vm_path = vm_path
        self.headless = headless
        self.action_space = action_space
        
        # Environment settings
        self.cache_dir = settings.cache_dir / "desktop_env"
        self.cache_dir.mkdir(exist_ok=True)
        
        # Environment instance
        self._env: Optional[DesktopEnv] = None
        self._env_lock = threading.Lock()
        self._initialized = False
        
        # Task management
        self.current_task_config = None
        self.observation_history = []
        
        if not HAS_DESKTOP_ENV:
            logger.warning("desktop_env library not available - module will have limited functionality")
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the desktop environment"""
        if not HAS_DESKTOP_ENV:
            raise DesktopEnvError("desktop_env library not available")
        
        try:
            # Initialize in background thread to avoid blocking
            def _init_env():
                with self._env_lock:
                    if not self._initialized:
                        self._env = DesktopEnv(
                            provider_name=self.provider_name,
                            path_to_vm=self.vm_path,
                            headless=self.headless,
                            action_space=self.action_space,
                            cache_dir=str(self.cache_dir),
                            screen_size=(1920, 1080),  # Can be configured
                            require_a11y_tree=True,
                            require_terminal=False
                        )
                        self._initialized = True
                        logger.info(f"Desktop environment initialized with {self.provider_name} provider")
            
            await asyncio.get_event_loop().run_in_executor(None, _init_env)
            
            return {
                "success": True,
                "provider": self.provider_name,
                "action_space": self.action_space,
                "vm_path": self.vm_path,
                "headless": self.headless
            }
            
        except Exception as e:
            logger.error(f"Failed to initialize desktop environment: {e}")
            raise DesktopEnvError(f"Initialization failed: {e}")
    
    async def reset_environment(self, task_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Reset the desktop environment to clean state"""
        if not self._env:
            await self.initialize()
        
        try:
            def _reset():
                with self._env_lock:
                    observation = self._env.reset(task_config=task_config)
                    return observation
            
            observation = await asyncio.get_event_loop().run_in_executor(None, _reset)
            
            self.current_task_config = task_config
            self.observation_history = [observation]
            
            # Process observation for return
            result = {
                "success": True,
                "reset_timestamp": datetime.utcnow().isoformat(),
                "task_config": task_config,
                "observation": self._process_observation(observation)
            }
            
            logger.info("Desktop environment reset successfully")
            return result
            
        except Exception as e:
            logger.error(f"Failed to reset desktop environment: {e}")
            raise DesktopEnvError(f"Reset failed: {e}")
    
    def _process_observation(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """Process and clean observation data for JSON serialization"""
        processed = {}
        
        # Handle screenshot
        if "screenshot" in observation and observation["screenshot"] is not None:
            # Save screenshot to file
            timestamp = int(datetime.utcnow().timestamp())
            screenshot_path = self.cache_dir / f"screenshot_{timestamp}.png"
            
            # Convert PIL Image to file
            if hasattr(observation["screenshot"], "save"):
                observation["screenshot"].save(screenshot_path)
                processed["screenshot_path"] = str(screenshot_path)
                processed["screenshot_size"] = observation["screenshot"].size
            
        # Handle accessibility tree
        if "accessibility_tree" in observation:
            processed["accessibility_tree"] = observation["accessibility_tree"]
        
        # Handle terminal output
        if "terminal" in observation:
            processed["terminal"] = observation["terminal"]
        
        # Handle instruction
        if "instruction" in observation:
            processed["instruction"] = observation["instruction"]
        
        return processed
    
    async def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action in the desktop environment
        
        Args:
            action: Action dict containing action details
                   For pyautogui: {"command": "pyautogui.click(100, 200)"}
                   For computer_13: {"action_type": "CLICK", "coordinates": [100, 200]}
        """
        if not self._env:
            await self.initialize()
        
        try:
            def _step():
                with self._env_lock:
                    # Prepare action based on action space
                    if self.action_space == "pyautogui":
                        # Handle pyautogui commands
                        if "command" in action:
                            command = action["command"]
                        else:
                            # Convert structured action to pyautogui command
                            command = self._convert_to_pyautogui(action)
                    else:
                        # Use action as-is for other action spaces
                        command = action
                    
                    # Execute step
                    observation, reward, done, info = self._env.step(command)
                    return observation, reward, done, info
            
            observation, reward, done, info = await asyncio.get_event_loop().run_in_executor(None, _step)
            
            # Store observation
            self.observation_history.append(observation)
            
            result = {
                "success": True,
                "action": action,
                "observation": self._process_observation(observation),
                "reward": reward,
                "done": done,
                "info": info,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Action executed successfully: {action}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute action: {e}")
            raise DesktopEnvError(f"Action execution failed: {e}")
    
    def _convert_to_pyautogui(self, action: Dict[str, Any]) -> str:
        """Convert structured action to pyautogui command"""
        action_type = action.get("type", "").upper()
        
        if action_type == "CLICK":
            coords = action.get("coordinates", [0, 0])
            button = action.get("button", "left")
            return f"pyautogui.click({coords[0]}, {coords[1]}, button='{button}')"
        
        elif action_type == "TYPE":
            text = action.get("text", "")
            return f"pyautogui.typewrite('{text}')"
        
        elif action_type == "KEY":
            key = action.get("key", "")
            return f"pyautogui.press('{key}')"
        
        elif action_type == "SCROLL":
            clicks = action.get("clicks", 1)
            x = action.get("x", 0)
            y = action.get("y", 0)
            return f"pyautogui.scroll({clicks}, x={x}, y={y})"
        
        elif action_type == "MOVE":
            coords = action.get("coordinates", [0, 0])
            return f"pyautogui.moveTo({coords[0]}, {coords[1]})"
        
        else:
            # Return raw command if available
            return action.get("command", "pass")
    
    async def take_screenshot(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Take a screenshot of the current desktop"""
        if not self._env:
            await self.initialize()
        
        try:
            def _get_screenshot():
                with self._env_lock:
                    return self._env.controller.get_screenshot()
            
            screenshot = await asyncio.get_event_loop().run_in_executor(None, _get_screenshot)
            
            # Save screenshot
            timestamp = int(datetime.utcnow().timestamp())
            screenshot_path = self.cache_dir / f"screenshot_{timestamp}.png"
            
            if hasattr(screenshot, "save"):
                screenshot.save(screenshot_path)
                
                return {
                    "success": True,
                    "screenshot_path": str(screenshot_path),
                    "screenshot_size": screenshot.size,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                raise DesktopEnvError("Invalid screenshot format")
                
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            raise DesktopEnvError(f"Screenshot failed: {e}")
    
    async def get_accessibility_tree(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Get accessibility tree of the current desktop"""
        if not self._env:
            await self.initialize()
        
        try:
            def _get_tree():
                with self._env_lock:
                    return self._env.controller.get_accessibility_tree()
            
            tree = await asyncio.get_event_loop().run_in_executor(None, _get_tree)
            
            return {
                "success": True,
                "accessibility_tree": tree,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get accessibility tree: {e}")
            raise DesktopEnvError(f"Accessibility tree failed: {e}")
    
    async def evaluate_task(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate if the current task is completed"""
        if not self._env:
            raise DesktopEnvError("Environment not initialized")
        
        try:
            def _evaluate():
                with self._env_lock:
                    return self._env.evaluate()
            
            score = await asyncio.get_event_loop().run_in_executor(None, _evaluate)
            
            return {
                "success": True,
                "evaluation_score": score,
                "task_completed": score >= 1.0,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to evaluate task: {e}")
            raise DesktopEnvError(f"Task evaluation failed: {e}")
    
    async def get_vm_info(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about the current VM"""
        if not self._env:
            await self.initialize()
        
        try:
            def _get_info():
                with self._env_lock:
                    platform = self._env.vm_platform
                    screen_size = self._env.vm_screen_size
                    return platform, screen_size
            
            platform, screen_size = await asyncio.get_event_loop().run_in_executor(None, _get_info)
            
            return {
                "success": True,
                "vm_platform": platform,
                "vm_screen_size": screen_size,
                "provider": self.provider_name,
                "action_space": self.action_space,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get VM info: {e}")
            raise DesktopEnvError(f"VM info failed: {e}")
    
    async def execute_complex_task(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a complex task with multiple steps
        
        Args:
            action: {
                "task_config": {...},  # Task configuration
                "actions": [...],      # List of actions to execute
                "evaluate": bool       # Whether to evaluate completion
            }
        """
        task_config = action.get("task_config")
        actions = action.get("actions", [])
        should_evaluate = action.get("evaluate", True)
        
        # Reset environment with task config
        reset_result = await self.reset_environment(task_config)
        
        results = []
        
        try:
            # Execute each action
            for i, single_action in enumerate(actions):
                logger.info(f"Executing step {i+1}/{len(actions)}")
                
                result = await self.execute_action(single_action)
                results.append(result)
                
                # Check if task is done
                if result.get("done", False):
                    logger.info("Task marked as done by environment")
                    break
            
            # Evaluate task if requested
            evaluation_result = None
            if should_evaluate:
                evaluation_result = await self.evaluate_task({})
            
            return {
                "success": True,
                "task_config": task_config,
                "total_steps": len(results),
                "action_results": results,
                "evaluation": evaluation_result,
                "completed": evaluation_result.get("task_completed", False) if evaluation_result else None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Complex task execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "completed_steps": len(results),
                "action_results": results
            }
    
    async def close(self) -> None:
        """Close the desktop environment"""
        if self._env:
            try:
                def _close():
                    with self._env_lock:
                        self._env.close()
                
                await asyncio.get_event_loop().run_in_executor(None, _close)
                logger.info("Desktop environment closed")
                
            except Exception as e:
                logger.error(f"Error closing desktop environment: {e}")
            finally:
                self._env = None
                self._initialized = False


# Global desktop environment module instance
desktop_env_module = DesktopEnvModule()