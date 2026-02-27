"""
Idle Monitor
Listens to KDE idle state changes via D-Bus and triggers face detection
"""

import asyncio
from dbus_next.aio import MessageBus
from dbus_next import BusType, MessageType
from typing import Callable, Optional
import signal

from src.utils.logger import get_logger


class IdleMonitor:
    """Monitors KDE idle state using D-Bus ScreenSaver interface"""
    
    def __init__(self, on_idle_callback: Callable[[bool], None]):
        """
        Initialize idle monitor
        
        Args:
            on_idle_callback: Function called when idle state changes
                             Receives boolean: True = idle, False = active
        """
        self.logger = get_logger(__name__)
        self.on_idle_callback = on_idle_callback
        self.bus: Optional[MessageBus] = None
        self.is_running = False
        
        # D-Bus service details for KDE ScreenSaver
        self.service_name = "org.freedesktop.ScreenSaver"
        self.object_path = "/org/freedesktop/ScreenSaver"
        self.interface_name = "org.freedesktop.ScreenSaver"
        self.signal_name = "ActiveChanged"
    
    async def connect(self) -> bool:
        """
        Connect to D-Bus session bus
        
        Returns:
            True if connected successfully
        """
        try:
            self.bus = await MessageBus(bus_type=BusType.SESSION).connect()
            self.logger.info("✓ Connected to D-Bus session bus")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to D-Bus: {e}")
            return False
    
    async def start(self) -> None:
        """Start monitoring idle events"""
        if not self.bus:
            if not await self.connect():
                self.logger.error("Cannot start - D-Bus not connected")
                return
        
        try:
            # Add message handler for signals
            self.bus.add_message_handler(self._handle_signal)
            
            self.is_running = True
            self.logger.info(f"✓ Monitoring idle events on {self.interface_name}")
            self.logger.info(f"  Listening for signal: {self.signal_name}")
            self.logger.info(f"  Waiting for idle timeout... (don't touch keyboard/mouse)")
            
        except Exception as e:
            self.logger.error(f"Failed to start idle monitoring: {e}")
            self.is_running = False
    
    def _handle_signal(self, msg) -> bool:
        """
        Handle incoming D-Bus signals
        
        Args:
            msg: D-Bus message
        
        Returns:
            True to continue processing
        """
        # Check if this is the ActiveChanged signal from ScreenSaver
        if (msg.message_type == MessageType.SIGNAL and
            msg.member == self.signal_name and
            msg.path == self.object_path):
            
            # Extract idle state from signal
            if msg.body and len(msg.body) > 0:
                is_idle = bool(msg.body[0])
                
                if is_idle:
                    self.logger.info(" System is now IDLE - checking for user presence")
                else:
                    self.logger.info(" System is now ACTIVE - user activity detected")
                
                # Trigger callback
                try:
                    self.on_idle_callback(is_idle)
                except Exception as e:
                    self.logger.error(f"Error in idle callback: {e}")
        
        return True  # Continue processing messages
    
    async def stop(self) -> None:
        """Stop monitoring and cleanup"""
        self.is_running = False
        
        if self.bus:
            self.bus.disconnect()
            self.logger.info("Disconnected from D-Bus")
    
    async def run_forever(self) -> None:
        """Run event loop forever (for standalone use)"""
        self.logger.info("Starting idle monitor event loop...")
        
        # Handle shutdown signals
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda: asyncio.create_task(self.stop())
            )
        
        await self.start()
        
        # Keep running until stopped
        while self.is_running:
            await asyncio.sleep(1)
        
        self.logger.info("Idle monitor stopped")


async def test_idle_monitor():
    """Test function for standalone testing"""
    
    def on_idle_changed(is_idle: bool):
        """Callback for idle state changes"""
        if is_idle:
            print("\n IDLE detected - Face detection would trigger here")
        else:
            print("\n ACTIVE - User is back")
    
    # Create monitor
    monitor = IdleMonitor(on_idle_callback=on_idle_changed)
    
    print("Idle Monitor Test")
    print("=" * 50)
    print("Waiting for idle events...")
    print("Let your system sit idle to test.")
    print("Press Ctrl+C to stop.\n")
    
    try:
        await monitor.run_forever()
    except KeyboardInterrupt:
        print("\n\nStopping...")
        await monitor.stop()


if __name__ == "__main__":
    asyncio.run(test_idle_monitor())