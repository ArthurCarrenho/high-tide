# windows_integration.py
#
# Copyright 2025 High Tide Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Windows-specific integration features for High Tide.

This module provides Windows system tray icon, media key integration (SMTC),
toast notifications, startup registration, and other Windows-specific functionality.
"""

import logging
import os
import platform
import subprocess
import sys
import threading
import winreg
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"

# Windows System Tray Icon support
_tray_icon = None
_tray_thread = None

if IS_WINDOWS:
    try:
        import pystray
        from PIL import Image
        HAS_PYSTRAY = True
    except ImportError:
        HAS_PYSTRAY = False
        logger.info("pystray or Pillow not found, system tray icon disabled")
    
    try:
        # Windows Runtime for System Media Transport Controls
        import winsdk.windows.media as windows_media
        import winsdk.windows.media.playback as windows_playback
        import winsdk.windows.storage.streams as windows_streams
        HAS_WINSDK = True
    except ImportError:
        HAS_WINSDK = False
        logger.info("winsdk not found, Windows media controls disabled")
    
    try:
        from win10toast import ToastNotifier
        HAS_WIN10TOAST = True
    except ImportError:
        HAS_WIN10TOAST = False
        logger.warning("win10toast not found, Windows notifications disabled")
else:
    HAS_PYSTRAY = False
    HAS_WINSDK = False
    HAS_WIN10TOAST = False


class WindowsTrayIcon:
    """System tray icon for Windows with playback controls."""
    
    def __init__(
        self,
        on_show: Callable,
        on_play_pause: Callable,
        on_next: Callable,
        on_previous: Callable,
        on_quit: Callable,
    ) -> None:
        """Initialize the Windows system tray icon.
        
        Args:
            on_show: Callback to show/focus the main window
            on_play_pause: Callback to toggle play/pause
            on_next: Callback to skip to next track
            on_previous: Callback to go to previous track
            on_quit: Callback to quit the application
        """
        self.on_show = on_show
        self.on_play_pause = on_play_pause
        self.on_next = on_next
        self.on_previous = on_previous
        self.on_quit = on_quit
        
        self._icon: Optional[Any] = None
        self._thread: Optional[threading.Thread] = None
        self._is_playing = False
        self._current_title = "High Tide"
        self._current_artist = ""
        
    def _load_icon_image(self, icon_path: Optional[str] = None) -> Any:
        """Load an icon image, converting SVG if necessary.
        
        Args:
            icon_path: Path to the icon file (PNG/ICO/SVG).
            
        Returns:
            PIL Image object
        """
        if icon_path and os.path.exists(icon_path):
            # Check if it's an SVG file
            if icon_path.lower().endswith('.svg'):
                # Try to convert SVG to PNG using cairosvg
                try:
                    import cairosvg
                    import io
                    png_data = cairosvg.svg2png(url=icon_path, output_width=64, output_height=64)
                    return Image.open(io.BytesIO(png_data))
                except ImportError:
                    logger.debug("cairosvg not available, using fallback icon")
                except Exception as e:
                    logger.debug(f"Failed to convert SVG: {e}")
            else:
                # Try to open directly (PNG, ICO, etc.)
                try:
                    return Image.open(icon_path)
                except Exception as e:
                    logger.debug(f"Failed to open icon: {e}")
        
        # Create a simple default icon (blue circle with play triangle)
        image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(image)
        # Blue circle background
        draw.ellipse([4, 4, 60, 60], fill=(66, 133, 244, 255))
        # White play triangle
        draw.polygon([(24, 18), (24, 46), (48, 32)], fill=(255, 255, 255, 255))
        return image
        
    def start(self, icon_path: Optional[str] = None) -> bool:
        """Start the system tray icon.
        
        Args:
            icon_path: Path to the icon file (PNG/ICO/SVG). If None, uses a default.
            
        Returns:
            bool: True if started successfully, False otherwise
        """
        if not HAS_PYSTRAY:
            logger.info("pystray not available; system tray icon disabled")
            return False
            
        try:
            # Create or load icon image
            image = self._load_icon_image(icon_path)
            
            # Create menu
            menu = pystray.Menu(
                pystray.MenuItem("Show High Tide", self._on_show_clicked, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    lambda item: "Pause" if self._is_playing else "Play",
                    self._on_play_pause_clicked
                ),
                pystray.MenuItem("Next", self._on_next_clicked),
                pystray.MenuItem("Previous", self._on_previous_clicked),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", self._on_quit_clicked),
            )
            
            self._icon = pystray.Icon(
                "high-tide",
                image,
                "High Tide",
                menu
            )
            
            # Run in separate thread to not block GTK main loop
            self._thread = threading.Thread(target=self._icon.run, daemon=True)
            self._thread.start()
            
            logger.info("Windows system tray icon started")
            return True
            
        except Exception:
            logger.exception("Failed to start system tray icon")
            return False
    
    def stop(self) -> None:
        """Stop and remove the system tray icon."""
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None
            logger.info("Windows system tray icon stopped")
    
    def update_state(self, is_playing: bool, title: str = "", artist: str = "") -> None:
        """Update the tray icon tooltip with current track info.
        
        Args:
            is_playing: Whether music is currently playing
            title: Current track title
            artist: Current track artist
        """
        self._is_playing = is_playing
        self._current_title = title or "High Tide"
        self._current_artist = artist
        
        if self._icon:
            tooltip = f"High Tide - {title}" if title else "High Tide"
            if artist:
                tooltip += f" by {artist}"
            if not is_playing and title:
                tooltip += " (Paused)"
            
            try:
                self._icon.title = tooltip
            except Exception:
                pass
    
    def _on_show_clicked(self, icon, item) -> None:
        self.on_show()
    
    def _on_play_pause_clicked(self, icon, item) -> None:
        self.on_play_pause()
    
    def _on_next_clicked(self, icon, item) -> None:
        self.on_next()
    
    def _on_previous_clicked(self, icon, item) -> None:
        self.on_previous()
    
    def _on_quit_clicked(self, icon, item) -> None:
        self.stop()
        self.on_quit()


class WindowsMediaControls:
    """Windows System Media Transport Controls (SMTC) integration.
    
    Provides media key support (play/pause/next/previous) and
    Now Playing info in Windows media overlay.
    
    Uses Windows.Media.Playback.MediaPlayer which provides automatic
    SMTC integration for desktop apps.
    """
    
    def __init__(
        self,
        on_play: Callable,
        on_pause: Callable,
        on_play_pause: Callable,
        on_next: Callable,
        on_previous: Callable,
        on_stop: Callable,
    ) -> None:
        """Initialize Windows Media Controls.
        
        Args:
            on_play: Callback for play command
            on_pause: Callback for pause command  
            on_play_pause: Callback for play/pause toggle
            on_next: Callback for next track
            on_previous: Callback for previous track
            on_stop: Callback for stop command
        """
        self.on_play = on_play
        self.on_pause = on_pause
        self.on_play_pause = on_play_pause
        self.on_next = on_next
        self.on_previous = on_previous
        self.on_stop = on_stop
        
        self._media_player = None
        self._smtc = None
        self._display_updater = None
        self._initialized = False
        self._current_title = ""
        self._current_artist = ""
        self._current_album = ""
        self._button_pressed_token = None
        
    def initialize(self) -> bool:
        """Initialize the System Media Transport Controls.
        
        Returns:
            bool: True if initialization successful
        """
        if not HAS_WINSDK:
            logger.warning("Cannot initialize SMTC: winsdk not available")
            return False
            
        try:
            # Set AppUserModelId for proper app identification in Windows
            self._set_app_user_model_id()
            
            from winsdk.windows.media.playback import MediaPlayer
            from winsdk.windows.media import MediaPlaybackType, MediaPlaybackStatus
            
            # Create a MediaPlayer - this automatically provides SMTC integration
            self._media_player = MediaPlayer()
            
            # Get the SMTC for this player
            self._smtc = self._media_player.system_media_transport_controls
            self._smtc.is_enabled = True
            self._smtc.is_play_enabled = True
            self._smtc.is_pause_enabled = True
            self._smtc.is_next_enabled = True
            self._smtc.is_previous_enabled = True
            self._smtc.is_stop_enabled = True
            
            # Handle button presses - use add_button_pressed method
            self._button_pressed_token = self._smtc.add_button_pressed(self._on_button_pressed)
            
            # Get display updater
            self._display_updater = self._smtc.display_updater
            self._display_updater.type = MediaPlaybackType.MUSIC
            
            self._initialized = True
            logger.info("Windows Media Controls (SMTC) initialized successfully")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to initialize Windows Media Controls: {e}")
            logger.info("Media keys may not work - this is normal for some Windows configurations")
            self._initialized = False
    
    def _set_app_user_model_id(self) -> None:
        """Set the AppUserModelId for proper Windows app identification."""
        try:
            import ctypes
            from ctypes import wintypes
            
            # SetCurrentProcessExplicitAppUserModelID
            shell32 = ctypes.windll.shell32
            shell32.SetCurrentProcessExplicitAppUserModelID.argtypes = [wintypes.LPCWSTR]
            shell32.SetCurrentProcessExplicitAppUserModelID.restype = ctypes.HRESULT
            
            # Set the AppUserModelId to match our app
            app_id = "io.github.nokse22.high-tide"
            result = shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
            if result == 0:  # S_OK
                logger.debug(f"Set AppUserModelId to: {app_id}")
            else:
                logger.debug(f"Failed to set AppUserModelId: {result}")
        except Exception as e:
            logger.debug(f"Could not set AppUserModelId: {e}")
            return False
    
    def _on_button_pressed(self, sender, args) -> None:
        """Handle button press events from SMTC."""
        try:
            from winsdk.windows.media import SystemMediaTransportControlsButton
            
            button = args.button
            logger.debug(f"SMTC button pressed: {button}")
            
            if button == SystemMediaTransportControlsButton.PLAY:
                self.on_play()
            elif button == SystemMediaTransportControlsButton.PAUSE:
                self.on_pause()
            elif button == SystemMediaTransportControlsButton.NEXT:
                self.on_next()
            elif button == SystemMediaTransportControlsButton.PREVIOUS:
                self.on_previous()
            elif button == SystemMediaTransportControlsButton.STOP:
                self.on_stop()
        except Exception:
            logger.exception("Error handling SMTC button press")
    
    def update_playback_status(self, is_playing: bool) -> None:
        """Update the playback status shown in Windows.
        
        Args:
            is_playing: Whether music is currently playing
        """
        if not self._initialized or not self._smtc:
            return
            
        try:
            from winsdk.windows.media import MediaPlaybackStatus
            
            if is_playing:
                self._smtc.playback_status = MediaPlaybackStatus.PLAYING
            else:
                self._smtc.playback_status = MediaPlaybackStatus.PAUSED
        except Exception:
            logger.exception("Error updating SMTC playback status")
    
    def update_metadata(
        self,
        title: str,
        artist: str,
        album: str = "",
        thumbnail_path: str = "",
        duration_ms: int = 0,
    ) -> None:
        """Update the Now Playing metadata in Windows.
        
        Args:
            title: Track title
            artist: Artist name
            album: Album name
            thumbnail_path: Path to album art image
            duration_ms: Track duration in milliseconds
        """
        if not self._initialized or not self._display_updater:
            return
            
        try:
            from winsdk.windows.media import MediaPlaybackType
            
            self._current_title = title
            self._current_artist = artist
            self._current_album = album
            
            # Update music properties
            self._display_updater.type = MediaPlaybackType.MUSIC
            music_props = self._display_updater.music_properties
            music_props.title = title
            music_props.artist = artist
            music_props.album_title = album
            
            # Set thumbnail if provided
            if thumbnail_path and os.path.exists(thumbnail_path):
                self._set_thumbnail_async(thumbnail_path)
            else:
                self._display_updater.update()
                
        except Exception:
            logger.exception("Error updating SMTC metadata")
    
    def _set_thumbnail_async(self, thumbnail_path: str) -> None:
        """Set the thumbnail asynchronously."""
        import asyncio
        import threading
        
        def run_async():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._set_thumbnail(thumbnail_path))
                loop.close()
            except Exception:
                logger.debug("Could not set SMTC thumbnail")
                try:
                    self._display_updater.update()
                except Exception:
                    pass
        
        # Run in a separate thread to not block GTK main loop
        threading.Thread(target=run_async, daemon=True).start()
    
    async def _set_thumbnail(self, thumbnail_path: str) -> None:
        """Async helper to set thumbnail from file path."""
        try:
            from winsdk.windows.storage import StorageFile
            from winsdk.windows.storage.streams import RandomAccessStreamReference
            
            # Convert path to Windows format
            thumbnail_path = os.path.abspath(thumbnail_path)
            
            file = await StorageFile.get_file_from_path_async(thumbnail_path)
            stream_ref = RandomAccessStreamReference.create_from_file(file)
            self._display_updater.thumbnail = stream_ref
            self._display_updater.update()
            logger.debug(f"SMTC thumbnail set: {thumbnail_path}")
        except Exception as e:
            logger.debug(f"Could not set SMTC thumbnail: {e}")
            self._display_updater.update()
            logger.exception("Error updating SMTC metadata")
    
    def update_position(self, position_ms: int) -> None:
        """Update the current playback position.
        
        Args:
            position_ms: Current position in milliseconds
        """
        if not self._initialized:
            return
        # Timeline updates require MediaPlaybackSession which needs actual playback
        # For now, we skip timeline updates as we're using GStreamer for actual playback
    
    def shutdown(self) -> None:
        """Clean up Windows Media Controls."""
        if self._smtc:
            try:
                # Remove button press handler
                if self._button_pressed_token is not None:
                    self._smtc.remove_button_pressed(self._button_pressed_token)
                self._smtc.is_enabled = False
            except Exception:
                pass
        self._button_pressed_token = None
        self._media_player = None
        self._smtc = None
        self._display_updater = None
        self._initialized = False
        logger.debug("Windows Media Controls shut down")


def check_gstreamer_plugins() -> Dict[str, bool]:
    """Check if required GStreamer plugins are available on Windows.
    
    Returns:
        dict: Mapping of plugin names to availability status
    """
    if not IS_WINDOWS:
        return {}
    
    try:
        from gi.repository import Gst
        Gst.init(None)
        
        required_plugins = {
            # Core playback
            "playbin": "playbin",
            "playbin3": "playbin3", 
            # Audio processing
            "audioconvert": "audioconvert",
            "audioresample": "audioresample",
            # Windows audio outputs
            "directsoundsink": "directsoundsink",
            "wasapisink": "wasapisink",
            # ReplayGain normalization
            "rgvolume": "rgvolume",
            "rglimiter": "rglimiter",
            "taginject": "taginject",
            # Queue for buffering
            "queue": "queue",
        }
        
        results = {}
        for name, element_name in required_plugins.items():
            factory = Gst.ElementFactory.find(element_name)
            results[name] = factory is not None
            
        # Log results
        missing = [name for name, available in results.items() if not available]
        if missing:
            logger.warning(f"Missing GStreamer plugins: {', '.join(missing)}")
        else:
            logger.info("All required GStreamer plugins available")
            
        return results
        
    except Exception:
        logger.exception("Failed to check GStreamer plugins")
        return {}


def get_missing_plugins_message() -> Optional[str]:
    """Get a user-friendly message about missing GStreamer plugins.
    
    Returns:
        str: Message describing missing plugins, or None if all present
    """
    results = check_gstreamer_plugins()
    
    missing = [name for name, available in results.items() if not available]
    
    if not missing:
        return None
    
    # Critical plugins that will break playback
    critical = {"playbin", "playbin3", "audioconvert"}
    critical_missing = set(missing) & critical
    
    if critical_missing:
        return (
            f"Critical GStreamer plugins missing: {', '.join(critical_missing)}.\n"
            "High Tide cannot play audio without these plugins.\n"
            "Please reinstall GStreamer with all plugins from:\n"
            "https://gstreamer.freedesktop.org/download/"
        )
    
    # Audio sink plugins
    sink_plugins = {"directsoundsink", "wasapisink"}
    if sink_plugins.issubset(set(missing)):
        return (
            "No Windows audio output plugins found.\n"
            "Please install GStreamer Good Plugins for Windows audio support."
        )
    
    # Non-critical missing plugins
    if missing:
        return (
            f"Some optional GStreamer plugins are missing: {', '.join(missing)}.\n"
            "Some features may not work correctly."
        )
    
    return None


# Singleton instances for easy access
_tray_icon_instance: Optional[WindowsTrayIcon] = None
_media_controls_instance: Optional[WindowsMediaControls] = None


def get_tray_icon() -> Optional[WindowsTrayIcon]:
    """Get the global tray icon instance."""
    return _tray_icon_instance


def set_tray_icon(instance: WindowsTrayIcon) -> None:
    """Set the global tray icon instance."""
    global _tray_icon_instance
    _tray_icon_instance = instance


def get_media_controls() -> Optional[WindowsMediaControls]:
    """Get the global media controls instance."""
    return _media_controls_instance


def set_media_controls(instance: WindowsMediaControls) -> None:
    """Set the global media controls instance."""
    global _media_controls_instance
    _media_controls_instance = instance


# =============================================================================
# Windows Toast Notifications
# =============================================================================

class WindowsNotifications:
    """Windows toast notification support for Now Playing alerts."""
    
    _instance: Optional["WindowsNotifications"] = None
    _notifier: Optional[Any] = None
    _enabled: bool = True
    _last_track_id: Optional[str] = None
    
    def __init__(self) -> None:
        """Initialize Windows notifications."""
        if HAS_WIN10TOAST:
            try:
                self._notifier = ToastNotifier()
                logger.info("Windows toast notifications initialized")
            except Exception:
                logger.exception("Failed to initialize Windows notifications")
                self._notifier = None
    
    @classmethod
    def get_instance(cls) -> "WindowsNotifications":
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = WindowsNotifications()
        return cls._instance
    
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable notifications."""
        self._enabled = enabled
    
    def show_now_playing(
        self,
        title: str,
        artist: str,
        album: str = "",
        icon_path: Optional[str] = None,
        track_id: Optional[str] = None,
    ) -> bool:
        """Show a Now Playing notification.
        
        Args:
            title: Track title
            artist: Artist name
            album: Album name (optional)
            icon_path: Path to album art (optional)
            track_id: Unique track ID to avoid duplicate notifications
            
        Returns:
            bool: True if notification was shown
        """
        if not self._enabled or not self._notifier:
            return False
        
        # Avoid showing duplicate notifications for same track
        if track_id and track_id == self._last_track_id:
            return False
        self._last_track_id = track_id
        
        try:
            message = f"{artist}"
            if album:
                message += f" • {album}"
            
            # Run in thread to avoid blocking
            def show_toast():
                try:
                    self._notifier.show_toast(
                        title=title,
                        msg=message,
                        icon_path=icon_path if icon_path and os.path.exists(icon_path) else None,
                        duration=5,
                        threaded=True,
                    )
                except Exception:
                    logger.exception("Failed to show toast notification")
            
            threading.Thread(target=show_toast, daemon=True).start()
            return True
            
        except Exception:
            logger.exception("Failed to show Now Playing notification")
            return False
    
    def show_message(self, title: str, message: str, icon_path: Optional[str] = None) -> bool:
        """Show a generic notification message.
        
        Args:
            title: Notification title
            message: Notification message
            icon_path: Path to icon (optional)
            
        Returns:
            bool: True if notification was shown
        """
        if not self._enabled or not self._notifier:
            return False
        
        try:
            def show_toast():
                try:
                    self._notifier.show_toast(
                        title=title,
                        msg=message,
                        icon_path=icon_path if icon_path and os.path.exists(icon_path) else None,
                        duration=5,
                        threaded=True,
                    )
                except Exception:
                    logger.exception("Failed to show toast notification")
            
            threading.Thread(target=show_toast, daemon=True).start()
            return True
            
        except Exception:
            logger.exception("Failed to show notification")
            return False


def get_notifications() -> WindowsNotifications:
    """Get the Windows notifications instance."""
    return WindowsNotifications.get_instance()


# =============================================================================
# Windows Startup Registration
# =============================================================================

# Registry key for current user startup programs
_STARTUP_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_APP_NAME = "HighTide"


def is_startup_enabled() -> bool:
    """Check if High Tide is set to run at Windows startup.
    
    Returns:
        bool: True if startup is enabled
    """
    if not IS_WINDOWS:
        return False
    
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _STARTUP_REG_KEY, 0, winreg.KEY_READ) as key:
            try:
                winreg.QueryValueEx(key, _APP_NAME)
                return True
            except FileNotFoundError:
                return False
    except Exception:
        logger.exception("Failed to check startup status")
        return False


def set_startup_enabled(enabled: bool) -> bool:
    """Enable or disable High Tide running at Windows startup.
    
    Args:
        enabled: True to enable startup, False to disable
        
    Returns:
        bool: True if operation succeeded
    """
    if not IS_WINDOWS:
        return False
    
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _STARTUP_REG_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                # Get the startup command
                startup_cmd = get_startup_command()
                if startup_cmd:
                    winreg.SetValueEx(key, _APP_NAME, 0, winreg.REG_SZ, startup_cmd)
                    logger.info(f"Enabled startup: {startup_cmd}")
                    return True
                else:
                    logger.error("Could not determine executable path for startup")
                    return False
            else:
                try:
                    winreg.DeleteValue(key, _APP_NAME)
                    logger.info("Disabled startup")
                except FileNotFoundError:
                    pass  # Already not set
                return True
    except Exception:
        logger.exception("Failed to set startup status")
        return False


def get_executable_path() -> Optional[str]:
    """Get the path to the High Tide executable.
    
    Returns:
        str: Path to executable, or None if not found
    """
    # If running as a frozen executable (PyInstaller, etc.)
    if getattr(sys, 'frozen', False):
        return sys.executable
    
    # If running as a Python script
    # Try to find the main entry point
    main_script = os.path.abspath(sys.argv[0])
    if os.path.exists(main_script):
        python_exe = sys.executable
        # Return a properly quoted command for the registry
        return f'{python_exe}" "{main_script}'
    
    return None


def get_startup_command() -> Optional[str]:
    """Get the full command to run High Tide at startup.
    
    Returns:
        str: Full command with proper quoting for registry, or None
    """
    # If running as a frozen executable (PyInstaller, etc.)
    if getattr(sys, 'frozen', False):
        return f'"{sys.executable}"'
    
    # If running as a Python script
    main_script = os.path.abspath(sys.argv[0])
    if os.path.exists(main_script):
        python_exe = sys.executable
        return f'"{python_exe}" "{main_script}"'
    
    return None


# =============================================================================
# tidal:// URI Protocol Handler Registration
# =============================================================================

_PROTOCOL_NAME = "tidal"


def is_protocol_handler_registered() -> bool:
    """Check if High Tide is registered as the tidal:// protocol handler.
    
    Returns:
        bool: True if registered
    """
    if not IS_WINDOWS:
        return False
    
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{_PROTOCOL_NAME}", 0, winreg.KEY_READ) as key:
            return True
    except FileNotFoundError:
        return False
    except Exception:
        logger.exception("Failed to check protocol handler status")
        return False


def register_protocol_handler() -> bool:
    """Register High Tide as the tidal:// protocol handler.
    
    This allows opening tidal://track/123 links from browsers directly in High Tide.
    
    Returns:
        bool: True if registration succeeded
    """
    if not IS_WINDOWS:
        return False
    
    executable = get_executable_path()
    if not executable:
        logger.error("Could not determine executable path for protocol registration")
        return False
    
    try:
        # Create the protocol key
        protocol_key_path = rf"Software\Classes\{_PROTOCOL_NAME}"
        
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, protocol_key_path) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "URL:TIDAL Protocol")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
        
        # Create the DefaultIcon key
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{protocol_key_path}\DefaultIcon") as key:
            # Use the executable as the icon source
            icon_path = executable.split('"')[0] if '"' in executable else executable
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f"{icon_path},0")
        
        # Create the shell\open\command key
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{protocol_key_path}\shell\open\command") as key:
            # The command to run - %1 will be replaced with the URL
            if getattr(sys, 'frozen', False):
                command = f'"{executable}" "%1"'
            else:
                # Running as script
                python_exe = sys.executable
                main_script = os.path.abspath(sys.argv[0])
                command = f'"{python_exe}" "{main_script}" "%1"'
            
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)
        
        logger.info(f"Registered tidal:// protocol handler: {command}")
        return True
        
    except Exception:
        logger.exception("Failed to register protocol handler")
        return False


def unregister_protocol_handler() -> bool:
    """Unregister High Tide as the tidal:// protocol handler.
    
    Returns:
        bool: True if unregistration succeeded
    """
    if not IS_WINDOWS:
        return False
    
    try:
        def delete_key_recursive(root, path):
            """Recursively delete a registry key and all subkeys."""
            try:
                with winreg.OpenKey(root, path, 0, winreg.KEY_ALL_ACCESS) as key:
                    # First, delete all subkeys
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, 0)
                            delete_key_recursive(root, rf"{path}\{subkey_name}")
                        except OSError:
                            break
                # Now delete the key itself
                winreg.DeleteKey(root, path)
            except FileNotFoundError:
                pass
        
        delete_key_recursive(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{_PROTOCOL_NAME}")
        logger.info("Unregistered tidal:// protocol handler")
        return True
        
    except Exception:
        logger.exception("Failed to unregister protocol handler")
        return False

