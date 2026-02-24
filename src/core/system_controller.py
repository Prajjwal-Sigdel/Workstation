"""
System Controller
Controls system behavior using D-Bus (inhibit sleep/dim), shutdown
"""

import asyncio
from dbus_next.aio import MessageBus
from dbus_next import BusType, Message, MessageType
from typing import Optional
import subprocess
import os

from src.utils.logger import get_logger

class SystemController:
    """Controls system power management via D-Bus"""

    def __init__(self):
        """Initialize system controller"""
        self.logger = get_logger(__name__)
        self.bus: Optional[MessageBus] = None
        self.inhibit_cookie: Optional[int] = None
        self.is_connected = False

        # D-Bus service details
        self.pm_service = "org.freedesktop.PowerManagement.Inhibit"
        self.pm_path = "/org/freedesktop/PowerManagement/Inhibit"
        self.pm_interface = "org.freedesktop.PowerManagement.Inhibit"

    async def connect(self) -> bool:
        """
        Connect to D-Bus session bus
        
        Returns:
            True if connected successfully
        """
        try:
            self.bus = await MessageBus(bus_type=BusType.SESSION).connect()
            self.is_connected = True
            self.logger.info("Connected to D-Bus session Bus")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to D-Bus: {e}")
            self.is_connected = False
            return False
    
    async def inhibit_idle(self, reason: str = "User is present") -> bool:
        """
        Inhibit screen dim, lock, and sleep
        
        Args:
            reason: Reason for inhibiting (shown in system logs)
            
        Returns:
            True if inhibitor activated successfully
        """
        if not self.is_connected:
            await self.connect()

        if self.inhibit_cookie is not None:
            self.logger.debug("Inhibitor already active")
            return True
        
        try:
            # Create D-Bus method call
            msg = Message(
                destination=self.pm_service,
                path=self.pm_path,
                interface=self.pm_interface,
                member="Inhibit",
                signature="ss",
                body=["SleepChecker", reason]
            )

            # Send message and wait for reply
            reply = await self.bus.call(msg)

            if reply.message_type == MessageType.METHOD_RETURN:
                self.inhibit_cookie = reply.body[0]
                self.logger.info(f"Inhibitor activated (cookie: {self.inhibit_cookie})")
                return True
            else:
                self.logger.error(f"Failed to inhibit: {reply.body}")
                return False
            
        except Exception as e:
            self.logger.error(f"Error activating inhibitor: {e}")
            return False
    
    async def uninhibit_idle(self) -> bool:
        """
        Release inhibitor lock
        
        Returns:
            True if inhibitor released successfully
        """
        if self.inhibit_cookie is None:
            self.logger.debug("No active inhibitor to release")
            return True
        
        try:
            # Create D-Bus method call
            msg = Message(
                destination=self.pm_service,
                path=self.pm_path,
                interface=self.pm_interface,
                member="UnInhibit",
                signature="u",
                body=[self.inhibit_cookie]
            )

            # Send message
            reply = await self.bus.call(msg)

            if reply.message_type == MessageType.METHOD_RETURN:
                self.logger.info(f"Inhibitor released (cookie: {self.inhibit_cookie})")
                self.inhibit_cookie = None
                return True
            else:
                self.logger.error(f"Failed to uninhibit: {reply.body}")
                return False
            
        except Exception as e:
            self.logger.error(f"Error releasing inhibitor: {e}")
            self.inhibit_cookie = None
            return False
    
    async def is_inhibited(self) -> bool:
        """
        Check if inhibitor is currently active
        
        Returns:
            True if inhibited
        """
        return self.inhibit_cookie is not None
    
    async def list_inhibitors(self) -> list:
        """
        List all active inhibitor (for debugging)
        
        Returns:
            List of active inhibitors
        """
        if not self.is_connected:
            await self.connect()
        
        try:
            msg = Message(
                destination=self.pm_service,
                path=self.pm_path,
                interface=self.pm_interface,
                member="HasInhibit"
            )

            reply = await self.bus.call(msg)

            if reply.message_type == MessageType.METHOD_RETURN:
                has_inhibit = reply.body[0]
                self.logger.debug(f"System has inhibitors: {has_inhibit}")
                return [has_inhibit]
            
            return []
        
        except Exception as e:
            self.logger.error(f"Error listing inhibitors: {e}")
            return []
        
    def shutdown_system(self) -> bool:
        """
        Shutdown the system (non-async)
        
        Returns:
            True if shutdown initiated
        """
        try: 
            self.logger.warning("Initiating SYSTEM SHUTDOWN (unknown person detected)")

            # Use systemctl to shutdown
            subprocess.run(
                ["systemctl", "poweroff"],
                check=True,
                timeout=5
            )

            return True
        
        except subprocess.TimeoutExpired:
            self.logger.error("Shutdown command timed out")
            return False
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Shutdown command failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error initiating Shutdown: {e}")
            return False
        
    def lock_screen(self) -> bool:
        """
        Lock the screen immediately
        
        Returns:
            True if screen locked
        """
        try:
            self.logger.info("Locking screen")

            # KDE lock command
            subprocess.run(
                ["qbus", "org.freedesktop.ScreenSaver", "/ScreenSaver", "Lock"],
                check=True,
                timeout=5
            )

            return True
        
        except Exception as e:
            self.logger.error(f"Error locking screen: {e}")
            return False
        
    async def cleanup(self) -> None:
        """Cleanup resources and release inhibitor"""
        if self.inhibit_cookie is not None:
            await self.uninhibit_idle()

        if self.bus:
            self.bus.disconnect()
            self.logger.info("Disconnected from D-Bus")
