#!/usr/bin/env python3
"""
Example usage of Coact Client

This script demonstrates how to use the Coact Client programmatically.
"""

import asyncio
import logging
from coact_client.app import app

# Configure logging for example
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Example usage of Coact Client"""
    
    print("🤖 Coact Client Example Usage")
    print("=" * 40)
    
    try:
        # Initialize the application
        print("1. Initializing application...")
        await app.initialize()
        
        # Check status
        print("2. Checking status...")
        status = app.get_status()
        print(f"   - Version: {status['version']}")
        print(f"   - Authenticated: {status['authenticated']}")
        print(f"   - Device Enrolled: {status['device_enrolled']}")
        print(f"   - Supported Actions: {len(status['supported_actions'])}")
        
        # If not authenticated, show login instructions
        if not status['authenticated']:
            print("\n❌ Not authenticated!")
            print("   Please run: coact login")
            return
        
        # If device not enrolled, show enrollment instructions
        if not status['device_enrolled']:
            print("\n❌ Device not enrolled!")
            print("   Please run: coact enroll")
            return
        
        print("\n✅ Client is ready!")
        
        # Show device info
        from coact_client.core.device import device_manager
        device_info = device_manager.get_device_info()
        if device_info:
            print(f"   - Device ID: {device_info.device_id}")
            print(f"   - Device Name: {device_info.device_name}")
            print(f"   - Platform: {device_info.platform}")
        
        # Show supported actions
        print(f"\n📋 Supported Actions ({len(status['supported_actions'])}):")
        for action in sorted(status['supported_actions']):
            print(f"   - {action}")
        
        print("\n🚀 To start the client:")
        print("   python -m coact_client.cli start")
        print("   # or")
        print("   coact start")
        
        print("\n📊 To monitor performance:")
        print("   coact status")
        print("   coact metrics")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're authenticated: coact login")
        print("2. Make sure device is enrolled: coact enroll")
        print("3. Check configuration: coact config")
    
    finally:
        # Clean shutdown
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())