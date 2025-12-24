; High Tide Windows Installer
; Inno Setup Script
;
; Requirements:
;   - Inno Setup 6.x (https://jrsoftware.org/isinfo.php)
;   - Build the app first with: python windows/build.py
;
; Build installer:
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" windows\installer.iss

#define MyAppName "High Tide for Windows"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "ArthurCarrenho"
#define MyAppURL "https://github.com/ArthurCarrenho/high-tide"
#define MyAppExeName "HighTide.exe"
#define MyAppUserModelId "io.github.nokse22.high-tide"

[Setup]
; Unique application ID
AppId={{B8E7F3D2-5A1C-4E8B-9F2D-3C4E5A6B7C8D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; License file
LicenseFile=..\COPYING
; Output settings
OutputDir=..\dist
OutputBaseFilename=HighTide-{#MyAppVersion}-Setup
; Compression
Compression=lzma2/ultra64
SolidCompression=yes
; Installer appearance
WizardStyle=modern
SetupIconFile=..\data\icons\hicolor\256x256\apps\io.github.nokse22.high-tide.ico
; Privileges - per-user install by default
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; Architecture
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Uninstall
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "dutch"; MessagesFile: "compiler:Languages\Dutch.isl"
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode
Name: "registerprotocol"; Description: "Register as handler for tidal:// links"; GroupDescription: "Integration:"
Name: "startup"; Description: "Run High Tide at Windows startup"; GroupDescription: "Integration:"; Flags: unchecked

[Files]
; Main application files from PyInstaller output
Source: "..\dist\HighTide\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; GStreamer plugins (if bundled separately)
; Source: "gstreamer\*"; DestDir: "{app}\gstreamer"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; AppUserModelID: "{#MyAppUserModelId}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; AppUserModelID: "{#MyAppUserModelId}"
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon; AppUserModelID: "{#MyAppUserModelId}"

[Registry]
; tidal:// protocol handler
Root: HKCU; Subkey: "Software\Classes\tidal"; ValueType: string; ValueName: ""; ValueData: "URL:TIDAL Protocol"; Flags: uninsdeletekey; Tasks: registerprotocol
Root: HKCU; Subkey: "Software\Classes\tidal"; ValueType: string; ValueName: "URL Protocol"; ValueData: ""; Tasks: registerprotocol
Root: HKCU; Subkey: "Software\Classes\tidal\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"; Tasks: registerprotocol
Root: HKCU; Subkey: "Software\Classes\tidal\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: registerprotocol

; Run at startup
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "HighTide"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: startup

[Run]
; Launch app after install (schemas are pre-compiled during build)
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up cache and config on uninstall (optional)
Type: filesandordirs; Name: "{localappdata}\high-tide"

[Code]
// Check if MSYS2/MinGW GStreamer is installed
function IsMSYS2GStreamerInstalled: Boolean;
begin
  Result := FileExists('C:\msys64\mingw64\bin\gst-launch-1.0.exe') or 
            FileExists('C:\msys64\mingw64\bin\libgstreamer-1.0-0.dll');
end;

// Check if standalone GStreamer is installed
function IsGStreamerInstalled: Boolean;
var
  GstPath: String;
begin
  Result := RegQueryStringValue(HKLM, 'SOFTWARE\GStreamer1.0\x86_64', 'InstallDir', GstPath) or
            RegQueryStringValue(HKCU, 'SOFTWARE\GStreamer1.0\x86_64', 'InstallDir', GstPath) or
            IsMSYS2GStreamerInstalled;
end;

function InitializeSetup: Boolean;
begin
  Result := True;
  
  // Warn if GStreamer is not detected
  if not IsGStreamerInstalled then
  begin
    if MsgBox('GStreamer does not appear to be installed. High Tide requires GStreamer for audio playback.' + #13#10 + #13#10 +
              'You can install GStreamer from:' + #13#10 +
              '  - https://gstreamer.freedesktop.org/download/' + #13#10 +
              '  - Or via MSYS2: pacman -S mingw-w64-x86_64-gstreamer' + #13#10 + #13#10 +
              'Do you want to continue anyway?',
              mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
    end;
  end;
end;
