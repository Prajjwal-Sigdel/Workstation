"""
Test script for SystemController
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.system_controller import SystemController


async def test_controller():
    """Test system controller functionality"""
    print("Testing System Controller...")
    
    # Initialize controller
    controller = SystemController()
    print("✓ Controller initialized")
    
    # Connect to D-Bus
    connected = await controller.connect()
    if not connected:
        print("✗ Failed to connect to D-Bus")
        return
    
    print("✓ Connected to D-Bus")
    
    # Activate inhibitor
    print("\nActivating inhibitor for 10 seconds...")
    success = await controller.inhibit_idle("Testing inhibitor")
    
    if success:
        print("✓ Inhibitor active - screen should NOT dim")
        print("  Try waiting for your normal idle timeout...")
        
        # Wait 10 seconds
        for i in range(10, 0, -1):
            print(f"  Waiting {i} seconds...", end='\r')
            await asyncio.sleep(1)
        
        print("\n\n✓ Test period complete")
        
        # Check status
        is_inhibited = await controller.is_inhibited()
        print(f"  Is inhibited: {is_inhibited}")
        
        # Release inhibitor
        print("\nReleasing inhibitor...")
        await controller.uninhibit_idle()
        print("✓ Inhibitor released - normal power management restored")
    else:
        print("✗ Failed to activate inhibitor")
    
    # Cleanup
    await controller.cleanup()
    print("\n✓ Test complete")


if __name__ == "__main__":
    asyncio.run(test_controller())