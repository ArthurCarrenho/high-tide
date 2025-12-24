<div align="center">
  <img height="128" src="data/icons/hicolor/scalable/apps/io.github.nokse22.high-tide.svg" alt="High Tide Logo"/>
  
  # High Tide for Windows
  
  <p align="center">
    <strong>Windows client for TIDAL streaming service</strong>
  </p>
  
  <p align="center">
    <a href="https://www.gnu.org/licenses/gpl-3.0">
      <img src="https://img.shields.io/badge/License-GPLv3-blue.svg" alt="License: GPL v3"/>
    </a>
    <a href="https://www.python.org/">
      <img src="https://img.shields.io/badge/Made%20with-Python-ff7b3f.svg" alt="Made with Python"/>
    </a>
    <a href="https://github.com/Nokse22/high-tide">
      <img src="https://img.shields.io/badge/Fork%20of-High%20Tide-00BFFF.svg" alt="Fork of High Tide"/>
    </a>
  </p>
</div>

> [!IMPORTANT] 
> Not affiliated in any way with TIDAL, this is a third-party unofficial client

> [!WARNING]
> This is an experimental port and may be unstable. Please report any bugs you find.

> [!NOTE]
> This is a Windows port of [High Tide](https://github.com/Nokse22/high-tide) by [@ArthurCarrenho](https://github.com/ArthurCarrenho).
> For the original Linux version by @Nokse22(https://github.com/Nokse22), please visit the [upstream repository](https://github.com/Nokse22/high-tide).

<table>
  <tr>
    <th><img src="data/resources/screenshot 1.png"/></th>
    <th><img src="data/resources/screenshot 2.png"/></th>
  </tr>
</table>

## 🚀 Installation

### 📦 Download Installer (Recommended)

1. Download the latest `HighTide-X.X.X-Setup.exe` from the [Releases page](https://github.com/ArthurCarrenho/high-tide-windows/releases)
2. Run the installer
3. High Tide will be available in your Start Menu

That's it! 🎉

### 📁 Portable Version

If you prefer not to install, download the portable ZIP from the [Releases page](https://github.com/ArthurCarrenho/high-tide-windows/releases):

1. Download `HighTide-X.X.X-Portable.zip`
2. Extract to any folder
3. Run `HighTide.exe`

---

## ✨ Windows Features

### 🔔 System Tray Icon
When minimized or running in background, High Tide shows an icon in your notification area. Right-click for:
- Show/Hide the main window
- Play/Pause
- Next/Previous track
- Quit the application

The tooltip shows the currently playing track.

### 🎵 Media Keys (SMTC)
Control playback with your keyboard's media keys or from the Windows media overlay:
- Play/Pause, Next, Previous
- Track info and album art displayed in Windows media controls

### 📢 Now Playing Notifications
Receive Windows toast notifications when tracks change:
- Track name
- Artist name
- Album name

### 🚀 Run at Startup
Go to **Preferences → Windows → Run at Windows startup** to have High Tide start automatically when you log in.

### 🔗 Handle tidal:// Links
Enable **Preferences → Windows → Handle tidal:// links** to open TIDAL links from your web browser directly in High Tide.

### 🔊 Audio Output
High Tide supports two Windows audio backends:
- **DirectSound** (default): Better compatibility
- **WASAPI**: Lower latency

You can select the audio backend in **Preferences → Audio → Preferred Audio Sink**.


---

## 🛠️ Building from Source

### Prerequisites

#### 1. MSYS2 with GTK4 and Libadwaita
Install [MSYS2](https://www.msys2.org/), then in MSYS2 MINGW64 terminal:

```bash
pacman -S mingw-w64-x86_64-gtk4 mingw-w64-x86_64-libadwaita mingw-w64-x86_64-python-gobject mingw-w64-x86_64-python-pip mingw-w64-x86_64-gstreamer mingw-w64-x86_64-gst-plugins-base mingw-w64-x86_64-gst-plugins-good mingw-w64-x86_64-gst-plugins-bad mingw-w64-x86_64-gst-plugins-ugly mingw-w64-x86_64-meson mingw-w64-x86_64-gettext-tools
```

#### 2. Python Dependencies
```bash
pip install tidalapi requests pystray pillow winsdk
```

### Build & Run

```bash
# Clone the repository
git clone https://github.com/ArthurCarrenho/high-tide-windows.git
cd high-tide

# Build with meson
meson setup builddir
meson compile -C builddir

# Run in development
python -m src
```

### Building the Installer

1. Install [Inno Setup](https://jrsoftware.org/isdl.php)
2. Install PyInstaller: `pip install pyinstaller`
3. Run the build script:

```bash
# Build everything (executable + installer)
python windows/build.py --installer

# Clean build
python windows/build.py --clean --installer
```

Build outputs:
- **Portable**: `dist/HighTide/` folder
- **Installer**: `dist/HighTide-X.X.X-Setup.exe`

---

## 🐛 Troubleshooting

### No audio output
1. Try switching between WASAPI and DirectSound in preferences
2. Check Windows audio device settings

### System tray icon not appearing
Make sure `pystray` and `pillow` are installed.

### Media keys not working
Make sure `winsdk` is installed for SMTC support.

### Login issues
High Tide uses Windows Credential Manager. If you experience issues:
1. Open Windows Credential Manager
2. Look for entries starting with "high-tide"
3. Remove them and log in again

---

## 🔄 Differences from Linux Version

| Feature | Linux | Windows |
|---------|-------|---------|
| Media controls | MPRIS (D-Bus) | SMTC |
| Audio sinks | PulseAudio, ALSA, PipeWire | WASAPI, DirectSound |
| Secret storage | libsecret | Windows Credential Manager |
| System tray | Shell extension | Native (pystray) |
| Notifications | Desktop notifications | Toast notifications |
| Startup | Desktop entry | Windows Registry |

---

## 🤝 Contributing

Contributions are welcome! Feel free to:
- 🐛 Report bugs
- 💡 Suggest features
- 🔧 Submit pull requests

For the original Linux version, please contribute to the [upstream repository](https://github.com/Nokse22/high-tide).

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](COPYING) file for details.

## 🙏 Acknowledgments

- [Nokse22](https://github.com/Nokse22) for creating the original High Tide
- The [High Tide community](https://matrix.to/#/%23high-tide:matrix.org) for their work on the Linux version
- [python-tidal](https://github.com/tamland/python-tidal) for the TIDAL API library

---

<div align="center">
  <p>Windows port made with ❤️ by <a href="https://github.com/ArthurCarrenho">ArthurCarrenho</a></p>
  <p>
    <a href="https://github.com/ArthurCarrenho/high-tide-windows">View on GitHub</a> • 
    <a href="https://github.com/ArthurCarrenho/high-tide-windows/issues">Report Bug</a> • 
    <a href="https://github.com/ArthurCarrenho/high-tide-windows/issues">Request Feature</a> •
    <a href="https://github.com/Nokse22/high-tide">Upstream Project</a>
  </p>
</div>
