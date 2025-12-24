from .cache import HTCache
from .discord_rpc import *
from .player_object import PlayerObject, RepeatType
from .secret_storage import SecretStore
from .utils import *
from .windows_integration import (
    IS_WINDOWS,
    WindowsTrayIcon,
    WindowsMediaControls,
    check_gstreamer_plugins,
    get_missing_plugins_message,
    get_tray_icon,
    set_tray_icon,
    get_notifications,
    is_startup_enabled,
    set_startup_enabled,
    is_protocol_handler_registered,
    register_protocol_handler,
    unregister_protocol_handler,
)
