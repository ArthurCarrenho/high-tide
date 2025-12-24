# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for High Tide Windows build
#
# Usage:
#   pyinstaller windows/high-tide.spec
#
# Requirements:
#   pip install pyinstaller

import os
import sys
import glob
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# MSYS2 MinGW64 path
MINGW_PATH = os.environ.get('MINGW_PREFIX', 'C:/msys64/mingw64')

# Determine icon path - try ICO, then PNG, then None
def find_icon():
    base = os.path.dirname(os.path.abspath(SPEC))
    paths = [
        os.path.join(base, '..', 'data', 'icons', 'hicolor', '256x256', 'apps', 'io.github.nokse22.high-tide.ico'),
        os.path.join(base, '..', 'data', 'icons', 'hicolor', '256x256', 'apps', 'io.github.nokse22.high-tide.png'),
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    return None

def collect_mingw_dlls():
    """Collect essential GTK/GLib DLLs from MSYS2."""
    dlls = []
    bin_path = os.path.join(MINGW_PATH, 'bin')
    
    # Essential DLL patterns for GTK4 + GStreamer
    dll_patterns = [
        'libgtk-4-*.dll',
        'libgdk-4-*.dll', 
        'libadwaita-*.dll',
        'libgio-*.dll',
        'libglib-*.dll',
        'libgobject-*.dll',
        'libgmodule-*.dll',
        'libgirepository-*.dll',
        'libpango*.dll',
        'libcairo*.dll',
        'libharfbuzz*.dll',
        'libfontconfig*.dll',
        'libfreetype*.dll',
        'libpixman*.dll',
        'libpng*.dll',
        'libjpeg*.dll',
        'libtiff*.dll',
        'libwebp*.dll',
        'libfribidi*.dll',
        'libgraphene*.dll',
        'libepoxy*.dll',
        'libintl*.dll',
        'libiconv*.dll',
        'libffi*.dll',
        'libpcre*.dll',
        'zlib*.dll',
        'libexpat*.dll',
        'libbz2*.dll',
        'libbrotli*.dll',
        'libgstreamer*.dll',
        'libgst*.dll',
        'libxml2*.dll',
        'liblzma*.dll',
        'libwinpthread*.dll',
        'libgcc*.dll',
        'libstdc++*.dll',
        'liborc*.dll',
    ]
    
    for pattern in dll_patterns:
        for dll_path in glob.glob(os.path.join(bin_path, pattern)):
            if os.path.isfile(dll_path):
                dlls.append((dll_path, '.'))
    
    return dlls

def collect_typelibs():
    """Collect GObject Introspection typelib files."""
    typelibs = []
    typelib_path = os.path.join(MINGW_PATH, 'lib', 'girepository-1.0')
    
    if os.path.exists(typelib_path):
        for typelib in glob.glob(os.path.join(typelib_path, '*.typelib')):
            typelibs.append((typelib, 'lib/girepository-1.0'))
    
    return typelibs

def collect_gio_modules():
    """Collect GIO modules for TLS/HTTPS support."""
    gio_modules = []
    gio_path = os.path.join(MINGW_PATH, 'lib', 'gio', 'modules')
    
    # Modules to exclude (gnomeproxy requires GNOME schemas not available on Windows)
    excluded_modules = ['libgiognomeproxy.dll', 'libgiolibproxy.dll']
    
    if os.path.exists(gio_path):
        for module in glob.glob(os.path.join(gio_path, '*.dll')):
            module_name = os.path.basename(module)
            if module_name not in excluded_modules:
                gio_modules.append((module, 'lib/gio/modules'))
    
    return gio_modules

def collect_gstreamer_plugins():
    """Collect essential GStreamer plugins."""
    plugins = []
    plugin_path = os.path.join(MINGW_PATH, 'lib', 'gstreamer-1.0')
    
    # Essential plugins for audio streaming
    essential_plugins = [
        # Core elements
        'libgstcoreelements.dll',
        'libgsttypefindfunctions.dll',
        'libgstautodetect.dll',
        'libgstplayback.dll',
        'libgstapp.dll',
        # Audio processing
        'libgstaudioconvert.dll',
        'libgstaudioresample.dll',
        'libgstaudioparsers.dll',
        'libgstvolume.dll',
        'libgstaudiorate.dll',
        # Audio codecs
        'libgstflac.dll',
        'libgstopus.dll',
        'libgstopusparse.dll',
        'libgstvorbis.dll',
        'libgstogg.dll',
        'libgstmpg123.dll',
        'libgstlame.dll',
        'libgstfdkaac.dll',
        'libgstfaad.dll',
        # Container formats
        'libgstisomp4.dll',
        'libgstmatroska.dll',
        # HTTP/Network sources
        'libgstsoup.dll',
        'libgstcurl.dll',
        'libgsttcp.dll',
        'libgstudp.dll',
        # Adaptive streaming (DASH, HLS)
        'libgstadaptivedemux2.dll',
        'libgstdash.dll',
        'libgsthls.dll',
        # Windows audio sinks
        'libgstdirectsound.dll',
        'libgstwasapi.dll',
        'libgstwasapi2.dll',
        # Other essentials
        'libgstgio.dll',
        'libgstid3demux.dll',
        'libgsticydemux.dll',
        'libgstapetag.dll',
        'libgsttags.dll',
        'libgstencoding.dll',
        'libgstpbtypes.dll',
    ]
    
    if os.path.exists(plugin_path):
        for plugin in essential_plugins:
            plugin_file = os.path.join(plugin_path, plugin)
            if os.path.exists(plugin_file):
                plugins.append((plugin_file, 'gst_plugins'))
    
    return plugins

def collect_locales():
    """Collect compiled locale files for translations."""
    locales = []
    locale_dir = os.path.join(PROJECT_ROOT, 'locale')
    
    if os.path.exists(locale_dir):
        for lang in os.listdir(locale_dir):
            mo_file = os.path.join(locale_dir, lang, 'LC_MESSAGES', 'high-tide.mo')
            if os.path.exists(mo_file):
                # Keep the directory structure: locale/<lang>/LC_MESSAGES/high-tide.mo
                locales.append((mo_file, os.path.join('locale', lang, 'LC_MESSAGES')))
    
    return locales

ICON_PATH = find_icon()

# Get project root from spec file location
SPEC_DIR = os.path.dirname(os.path.abspath(SPEC))
PROJECT_ROOT = os.path.dirname(SPEC_DIR)

# Collect all tidalapi submodules
tidalapi_datas, tidalapi_binaries, tidalapi_hiddenimports = collect_all('tidalapi')

# Collect certifi CA bundle for HTTPS requests
certifi_datas, certifi_binaries, certifi_hiddenimports = collect_all('certifi')

# Collect GTK/GObject related modules
gi_hiddenimports = collect_submodules('gi')

# Collect MSYS2 DLLs and typelibs
mingw_dlls = collect_mingw_dlls()
typelibs = collect_typelibs()
gio_modules = collect_gio_modules()
gst_plugins = collect_gstreamer_plugins()
locale_files = collect_locales()

# Data files to include (using absolute paths)
added_files = [
    # GResource file (compiled UI)
    (os.path.join(PROJECT_ROOT, 'builddir', 'data', 'high-tide.gresource'), 'data'),
    # GSettings schema
    (os.path.join(PROJECT_ROOT, 'data', 'io.github.nokse22.high-tide.gschema.xml'), 'share/glib-2.0/schemas'),
    (os.path.join(PROJECT_ROOT, 'data', 'gschemas.compiled'), 'share/glib-2.0/schemas'),
    # Icons
    (os.path.join(PROJECT_ROOT, 'data', 'icons'), 'share/icons'),
    # CSS styles
    (os.path.join(PROJECT_ROOT, 'data', 'style.css'), 'data'),
    (os.path.join(PROJECT_ROOT, 'data', 'style-dark.css'), 'data'),
]

# Filter out files that don't exist
added_files = [(src, dst) for src, dst in added_files if os.path.exists(src)]

# Combine all data files
all_datas = added_files + tidalapi_datas + certifi_datas + typelibs + gio_modules + gst_plugins + locale_files

# Combine all binaries
all_binaries = tidalapi_binaries + certifi_binaries + mingw_dlls

a = Analysis(
    [os.path.join(PROJECT_ROOT, 'src', '__main__.py')],
    pathex=[PROJECT_ROOT],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=[
        'gi',
        'gi.repository.Gtk',
        'gi.repository.Gdk',
        'gi.repository.GLib',
        'gi.repository.GObject',
        'gi.repository.Gio',
        'gi.repository.Adw',
        'gi.repository.Gst',
        'gi.repository.GstAudio',
        'gi.repository.GstVideo',
        'gi.repository.GstPbutils',
        'tidalapi',
        'requests',
        'pystray',
        'PIL',
        'PIL.Image',
        'win10toast',
        'pypresence',
    ] + gi_hiddenimports + tidalapi_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='HighTide',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Enable console for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON_PATH,
    version='version_info.txt' if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'version_info.txt')) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='HighTide',
)
