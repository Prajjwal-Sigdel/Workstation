"""
Test script for IdleMonitor
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.monitors.idle_monitor import IdleMonitor
from src.utils.logger import setup_logger


async def test_idle_detection():
    """Test idle detection via D-Bus"""
    
    # Setup logging
    logger = setup_logger('idle_test', 'data/logs/idle_test.log', 'INFO')
    
    print("\n" + "=" * 60)
    print("  KDE Idle Detection Test (via D-Bus)")
    print("=" * 60)
    print("\nThis test monitors KDE's idle state changes.")
    print("Steps:")
    print("  1. Don't touch mouse/keyboard")
    print("  2. Wait for your configured idle timeout")
    print("  3. Watch for idle signal")
    print("  4. Move mouse to see 'active' signal")
    print("\nPress Ctrl+C to stop.")
    print("-" * 60 + "\n")
    
    idle_count = 0
    active_count = 0
    
    def on_idle_changed(is_idle: bool):
        """Callback for idle state changes"""
        nonlocal idle_count, active_count
        
        if is_idle:
            idle_count += 1
            print(f"\n IDLE Event #{idle_count}")
            print("   → System thinks you're away")
            print("   → Face detection would trigger now")
            logger.info(f"Idle event received (count: {idle_count})")
        else:
            active_count += 1
            print(f"\n ACTIVE Event #{active_count}")
            print("   → User activity detected")
            print("   → Face detection not needed")
            logger.info(f"Active event received (count: {active_count})")
    
    # Create and start monitor
    monitor = IdleMonitor(on_idle_callback=on_idle_changed)
    
    try:
        await monitor.run_forever()
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("Test Summary:")
        print(f"  Idle events received: {idle_count}")
        print(f"  Active events received: {active_count}")
        print("=" * 60)
        await monitor.stop()


if __name__ == "__main__":
    asyncio.run(test_idle_detection())