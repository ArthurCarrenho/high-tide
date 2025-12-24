#!/usr/bin/env python3
"""
High Tide Windows Build Script

This script automates the Windows build process:
1. Builds the app with meson (compiles UI resources)
2. Compiles GSettings schemas
3. Packages with PyInstaller
4. Optionally creates installer with Inno Setup

Requirements:
    pip install pyinstaller

Usage:
    python windows/build.py [--installer]

Options:
    --installer    Also build the Inno Setup installer (requires Inno Setup 6)
    --clean        Clean build directories before building
    --skip-meson   Skip meson build step (use existing builddir)
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
BUILD_DIR = PROJECT_ROOT / "builddir"
DIST_DIR = PROJECT_ROOT / "dist"
DATA_DIR = PROJECT_ROOT / "data"
WINDOWS_DIR = PROJECT_ROOT / "windows"

# MSYS2 paths
MSYS2_ROOT = Path("C:/msys64/mingw64")
GLIB_COMPILE_SCHEMAS = MSYS2_ROOT / "bin" / "glib-compile-schemas.exe"
MSGFMT = MSYS2_ROOT / "bin" / "msgfmt.exe"

# Locales
PO_DIR = PROJECT_ROOT / "po"
LOCALE_DIR = PROJECT_ROOT / "locale"
LINGUAS = ["fr", "de", "nl", "pt_BR", "es", "it", "zh_TW", "pl"]

# Inno Setup path
INNO_SETUP = Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe")


def run_command(cmd, cwd=None, check=True):
    """Run a command and print output."""
    print(f"$ {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, cwd=cwd, check=check)
    return result.returncode == 0


def clean_build():
    """Clean build directories."""
    print("\n=== Cleaning build directories ===")
    
    dirs_to_clean = [
        PROJECT_ROOT / "build",
        DIST_DIR,
        WINDOWS_DIR / "build",
        LOCALE_DIR,
    ]
    
    for d in dirs_to_clean:
        if d.exists():
            print(f"Removing {d}")
            shutil.rmtree(d)


def build_meson():
    """Build the app with meson to compile UI resources."""
    print("\n=== Building with Meson ===")
    
    if not BUILD_DIR.exists():
        print("Setting up meson build directory...")
        run_command(["meson", "setup", str(BUILD_DIR)], cwd=PROJECT_ROOT)
    
    print("Compiling...")
    run_command(["meson", "compile", "-C", str(BUILD_DIR)], cwd=PROJECT_ROOT)


def compile_schemas():
    """Compile GSettings schemas."""
    print("\n=== Compiling GSettings schemas ===")
    
    if GLIB_COMPILE_SCHEMAS.exists():
        run_command([str(GLIB_COMPILE_SCHEMAS), str(DATA_DIR)])
        print(f"Schemas compiled to {DATA_DIR / 'gschemas.compiled'}")
    else:
        print(f"WARNING: glib-compile-schemas not found at {GLIB_COMPILE_SCHEMAS}")
        print("Trying system PATH...")
        run_command(["glib-compile-schemas", str(DATA_DIR)], check=False)


def compile_locales():
    """Compile .po files to .mo files for localization."""
    print("\n=== Compiling locale files ===")
    
    if not MSGFMT.exists():
        print(f"WARNING: msgfmt not found at {MSGFMT}")
        print("Localization will not be available.")
        return False
    
    # Read LINGUAS file for list of languages
    linguas_file = PO_DIR / "LINGUAS"
    if linguas_file.exists():
        languages = linguas_file.read_text().strip().split()
    else:
        languages = LINGUAS
    
    compiled = 0
    for lang in languages:
        po_file = PO_DIR / f"{lang}.po"
        if not po_file.exists():
            print(f"  WARNING: {po_file} not found")
            continue
        
        # Create locale directory structure: locale/<lang>/LC_MESSAGES/high-tide.mo
        mo_dir = LOCALE_DIR / lang / "LC_MESSAGES"
        mo_dir.mkdir(parents=True, exist_ok=True)
        mo_file = mo_dir / "high-tide.mo"
        
        result = subprocess.run(
            [str(MSGFMT), "-o", str(mo_file), str(po_file)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            compiled += 1
            print(f"  Compiled: {lang}")
        else:
            print(f"  ERROR compiling {lang}: {result.stderr}")
    
    print(f"Compiled {compiled}/{len(languages)} locale files to {LOCALE_DIR}")
    return compiled > 0


def create_icon():
    """Create .ico file from SVG or PNG."""
    print("\n=== Creating Windows icon ===")
    
    ico_path = DATA_DIR / "icons" / "hicolor" / "256x256" / "apps" / "io.github.nokse22.high-tide.ico"
    png_path = DATA_DIR / "icons" / "hicolor" / "256x256" / "apps" / "io.github.nokse22.high-tide.png"
    svg_path = DATA_DIR / "icons" / "hicolor" / "scalable" / "apps" / "io.github.nokse22.high-tide.svg"
    
    if ico_path.exists():
        print(f"Icon already exists: {ico_path}")
        return True
    
    # Try to create from PNG first
    if png_path.exists():
        try:
            from PIL import Image
            img = Image.open(png_path)
            img.save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
            print(f"Created icon from PNG: {ico_path}")
            return True
        except Exception as e:
            print(f"WARNING: Failed to create ICO from PNG: {e}")
    
    # Try to convert SVG to ICO
    if svg_path.exists():
        try:
            import cairosvg
            from PIL import Image
            import io
            
            # Convert SVG to PNG in memory
            png_data = cairosvg.svg2png(url=str(svg_path), output_width=256, output_height=256)
            img = Image.open(io.BytesIO(png_data))
            
            # Create ICO with multiple sizes
            ico_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
            print(f"Created icon from SVG: {ico_path}")
            return True
        except ImportError:
            print("WARNING: cairosvg not installed, cannot convert SVG to ICO")
            print("Install with: pip install cairosvg")
        except Exception as e:
            print(f"WARNING: Failed to convert SVG to ICO: {e}")
    
    print("WARNING: No icon could be created. Build will continue without custom icon.")
    return False


def build_pyinstaller():
    """Build with PyInstaller."""
    print("\n=== Building with PyInstaller ===")
    
    spec_file = WINDOWS_DIR / "high-tide.spec"
    
    if not spec_file.exists():
        print(f"ERROR: Spec file not found: {spec_file}")
        return False
    
    # Change to windows directory for relative paths in spec
    run_command(
        [sys.executable, "-m", "PyInstaller", "--clean", str(spec_file)],
        cwd=WINDOWS_DIR
    )
    
    # Move dist folder to project root
    pyinstaller_dist = WINDOWS_DIR / "dist"
    if pyinstaller_dist.exists():
        if DIST_DIR.exists():
            shutil.rmtree(DIST_DIR)
        shutil.move(str(pyinstaller_dist), str(DIST_DIR))
    
    return True


def copy_gstreamer_plugins():
    """Copy required GStreamer plugins to dist folder."""
    print("\n=== Copying GStreamer plugins ===")
    
    gst_plugin_dir = MSYS2_ROOT / "lib" / "gstreamer-1.0"
    dest_plugin_dir = DIST_DIR / "HighTide" / "lib" / "gstreamer-1.0"
    
    if not gst_plugin_dir.exists():
        print(f"WARNING: GStreamer plugins not found at {gst_plugin_dir}")
        return
    
    dest_plugin_dir.mkdir(parents=True, exist_ok=True)
    
    # Essential plugins for audio playback
    required_plugins = [
        "libgstcoreelements.dll",
        "libgstaudioconvert.dll",
        "libgstaudioresample.dll",
        "libgstplayback.dll",
        "libgstautodetect.dll",
        "libgstdirectsound.dll",
        "libgstwasapi.dll",
        "libgstreplaygain.dll",
        "libgsttypefindfunctions.dll",
        "libgstaudioparsers.dll",
        "libgstmpg123.dll",
        "libgstflac.dll",
        "libgstogg.dll",
        "libgstvorbis.dll",
        "libgstopus.dll",
        "libgstdash.dll",
        "libgstsoup.dll",
        "libgstadaptivedemux2.dll",
    ]
    
    copied = 0
    for plugin in required_plugins:
        src = gst_plugin_dir / plugin
        if src.exists():
            shutil.copy2(src, dest_plugin_dir / plugin)
            copied += 1
        else:
            print(f"  WARNING: Plugin not found: {plugin}")
    
    print(f"Copied {copied}/{len(required_plugins)} GStreamer plugins")


def copy_gtk_resources():
    """Copy GTK/Adwaita resources."""
    print("\n=== Copying GTK resources ===")
    
    dest_share = DIST_DIR / "HighTide" / "share"
    
    # Copy icons theme
    icons_src = MSYS2_ROOT / "share" / "icons" / "Adwaita"
    icons_dest = dest_share / "icons" / "Adwaita"
    if icons_src.exists() and not icons_dest.exists():
        print("Copying Adwaita icons...")
        shutil.copytree(icons_src, icons_dest)
    
    # Copy GLib schemas
    schemas_src = MSYS2_ROOT / "share" / "glib-2.0" / "schemas"
    schemas_dest = dest_share / "glib-2.0" / "schemas"
    if schemas_src.exists():
        schemas_dest.mkdir(parents=True, exist_ok=True)
        # Copy our app schema
        our_schema = DATA_DIR / "io.github.nokse22.high-tide.gschema.xml"
        if our_schema.exists():
            shutil.copy2(our_schema, schemas_dest)
        compiled = DATA_DIR / "gschemas.compiled"
        if compiled.exists():
            shutil.copy2(compiled, schemas_dest)


def build_installer():
    """Build Inno Setup installer."""
    print("\n=== Building Installer ===")
    
    if not INNO_SETUP.exists():
        print(f"ERROR: Inno Setup not found at {INNO_SETUP}")
        print("Download from: https://jrsoftware.org/isinfo.php")
        return False
    
    iss_file = WINDOWS_DIR / "installer.iss"
    if not iss_file.exists():
        print(f"ERROR: Installer script not found: {iss_file}")
        return False
    
    run_command([str(INNO_SETUP), str(iss_file)])
    
    print(f"\nInstaller created in: {DIST_DIR}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Build High Tide for Windows")
    parser.add_argument("--installer", action="store_true", help="Build Inno Setup installer")
    parser.add_argument("--clean", action="store_true", help="Clean build directories first")
    parser.add_argument("--skip-meson", action="store_true", help="Skip meson build step")
    args = parser.parse_args()
    
    print("=" * 60)
    print("High Tide Windows Build")
    print("=" * 60)
    
    if args.clean:
        clean_build()
    
    if not args.skip_meson:
        build_meson()
    
    compile_schemas()
    compile_locales()
    create_icon()
    
    if not build_pyinstaller():
        print("\nERROR: PyInstaller build failed")
        sys.exit(1)
    
    copy_gstreamer_plugins()
    copy_gtk_resources()
    
    if args.installer:
        if not build_installer():
            print("\nWARNING: Installer build failed")
    
    print("\n" + "=" * 60)
    print("Build complete!")
    print("=" * 60)
    print(f"\nOutput directory: {DIST_DIR / 'HighTide'}")
    
    if args.installer:
        installers = list(DIST_DIR.glob("*.exe"))
        if installers:
            print(f"Installer: {installers[0]}")


if __name__ == "__main__":
    main()
