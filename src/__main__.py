#!/usr/bin/env python3
# __main__.py - Entry point for High Tide
#
# This module allows running High Tide with:
#   python -m src
#   python -m high_tide
#
# It also serves as the entry point for PyInstaller builds.

import os
import sys
import signal
import locale
import gettext
import platform

VERSION = '1.1.0'

def get_resource_path():
    """Get the path to resources (GResource file, etc.)
    
    Works both for development and PyInstaller builds.
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        return os.path.join(sys._MEIPASS, 'data')
    else:
        # Running from source
        # Try builddir first (after meson build), then data dir
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        
        builddir_path = os.path.join(project_root, 'builddir', 'data')
        if os.path.exists(os.path.join(builddir_path, 'high-tide.gresource')):
            return builddir_path
        
        # Fallback to installed location
        return '/usr/share/high-tide'


def get_locale_path():
    """Get the path to locale files."""
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'locale')
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        return os.path.join(project_root, 'locale')


def get_user_language():
    """Get the user's preferred language from settings.
    
    Returns the language code (e.g., 'de', 'fr') or empty string for system default.
    Must be called after setup_environment() to ensure GSETTINGS_SCHEMA_DIR is set.
    """
    if platform.system() != 'Windows':
        return ''
    
    try:
        import gi
        gi.require_version('Gio', '2.0')
        from gi.repository import Gio
        settings = Gio.Settings.new('io.github.nokse22.high-tide')
        return settings.get_string('language')
    except Exception as e:
        print(f"Could not read language setting: {e}")
        return ''


def setup_environment():
    """Set up environment for Windows."""
    if platform.system() == 'Windows':
        if getattr(sys, 'frozen', False):
            # Ensure GStreamer can find plugins
            gst_plugin_path = os.path.join(sys._MEIPASS, 'gst_plugins')
            if os.path.exists(gst_plugin_path):
                os.environ['GST_PLUGIN_PATH'] = gst_plugin_path
                # Also set GST_PLUGIN_SYSTEM_PATH to prevent searching system paths
                os.environ['GST_PLUGIN_SYSTEM_PATH'] = gst_plugin_path
            
            # Set GStreamer registry path to a writable location
            registry_dir = os.path.join(
                os.environ.get('LOCALAPPDATA', os.path.expanduser('~')),
                'HighTide'
            )
            os.makedirs(registry_dir, exist_ok=True)
            os.environ['GST_REGISTRY'] = os.path.join(registry_dir, 'gst_registry.bin')
            
            # Set up GIO modules path for TLS/HTTPS support
            gio_module_dir = os.path.join(sys._MEIPASS, 'lib', 'gio', 'modules')
            if os.path.exists(gio_module_dir):
                os.environ['GIO_MODULE_DIR'] = gio_module_dir
            
            # Set up GSettings schema path
            schema_dir = os.path.join(sys._MEIPASS, 'share', 'glib-2.0', 'schemas')
            if os.path.exists(schema_dir):
                os.environ['GSETTINGS_SCHEMA_DIR'] = schema_dir
            
            # Set up GI typelib path
            typelib_dir = os.path.join(sys._MEIPASS, 'lib', 'girepository-1.0')
            if os.path.exists(typelib_dir):
                os.environ['GI_TYPELIB_PATH'] = typelib_dir


def main():
    """Main entry point."""
    # Set up Windows environment
    setup_environment()
    
    # Handle SIGINT gracefully
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    # Get user's preferred language (must be after setup_environment for GSettings)
    user_lang = get_user_language()
    
    # Set up localization
    localedir = get_locale_path()
    
    print(f"[DEBUG] Locale directory: {localedir}")
    print(f"[DEBUG] User language setting: '{user_lang}'")
    
    # Check if locale files exist
    if os.path.exists(localedir):
        print(f"[DEBUG] Locale files found: {os.listdir(localedir)}")
    else:
        print(f"[DEBUG] Locale directory does not exist!")
    
    # Apply user's language preference
    if user_lang:
        # Set environment variables to force the language
        os.environ['LANGUAGE'] = user_lang
        os.environ['LANG'] = f'{user_lang}.UTF-8'
        os.environ['LC_ALL'] = f'{user_lang}.UTF-8'
        os.environ['LC_MESSAGES'] = f'{user_lang}.UTF-8'
        
        # Check if the specific .mo file exists
        mo_file = os.path.join(localedir, user_lang, 'LC_MESSAGES', 'high-tide.mo')
        print(f"[DEBUG] Looking for: {mo_file}")
        print(f"[DEBUG] Exists: {os.path.exists(mo_file)}")
        
        # Create translation for the specific language
        try:
            lang_trans = gettext.translation('high-tide', localedir, languages=[user_lang])
            lang_trans.install()
            print(f"[DEBUG] Translation loaded successfully for '{user_lang}'")
            
            # Override gettext.gettext to use this translation
            gettext.gettext = lang_trans.gettext
            gettext.ngettext = lang_trans.ngettext
        except FileNotFoundError as e:
            print(f"[DEBUG] Translation for '{user_lang}' not found: {e}")
            gettext.install('high-tide', localedir)
    else:
        # Use system default
        gettext.bindtextdomain('high-tide', localedir)
        gettext.textdomain('high-tide')
        gettext.install('high-tide', localedir)
    
    # Import GTK and related libraries
    import gi
    gi.require_version('Gtk', '4.0')
    gi.require_version('Adw', '1')
    gi.require_version('Gst', '1.0')
    
    # Conditionally require Secret (not available on Windows)
    if platform.system() != 'Windows':
        gi.require_version('Secret', '1')
    
    from gi.repository import Gio, GLib
    
    # Set up GLib translations for GTK UI elements
    # This is required for .ui file strings to be translated
    if platform.system() == 'Windows':
        # On Windows, we need to use GLib's bindtextdomain
        GLib.setenv('LANGUAGE', user_lang if user_lang else '', True)
        
        # Use ctypes to call bindtextdomain from libintl
        try:
            import ctypes
            libintl = ctypes.CDLL('libintl-8.dll')
            libintl.bindtextdomain(b'high-tide', localedir.encode('utf-8'))
            libintl.textdomain(b'high-tide')
            libintl.bind_textdomain_codeset(b'high-tide', b'UTF-8')
            print(f"[DEBUG] GLib/libintl translations set up for '{user_lang}'")
        except Exception as e:
            print(f"[DEBUG] Failed to set up libintl: {e}")
    
    # Load GResource
    resource_path = get_resource_path()
    gresource_file = os.path.join(resource_path, 'high-tide.gresource')
    
    if os.path.exists(gresource_file):
        resource = Gio.Resource.load(gresource_file)
        resource._register()
    else:
        print(f"WARNING: GResource file not found: {gresource_file}")
        print("Run 'meson compile -C builddir' first to build resources.")
    
    # Import and run the application
    from src.main import main as app_main
    return app_main(VERSION)


if __name__ == '__main__':
    sys.exit(main())
