; Installer Apotek Pahala untuk Windows 7 SP1 x64.
; Dibuat dengan Inno Setup 6.2.2 (versi terakhir yang mendukung Windows 7).

#define MyAppName "Apotek Pahala"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Tim Capstone Design - Sistem Informasi, Universitas Telkom"
#define MyAppExeName "ApotekPahala.exe"

[Setup]
AppId={{8C2E9A54-6D3B-4C21-9F7A-1B5D4E8A2C10}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\ApotekPahala
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\build\win7\installer
OutputBaseFilename=ApotekPahala-Setup-1.0.0-win7-x64
SetupIconFile=assets\apotek-pahala.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
MinVersion=6.1sp1
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
CloseApplications=yes
RestartApplications=no
SetupLogging=yes
AllowNoIcons=yes
DisableWelcomePage=no

[Languages]
; Berkas terjemahan disertakan agar build tidak bergantung pada tambahan
; bahasa di instalasi Inno Setup.
Name: "indonesian"; MessagesFile: "Indonesian.isl"

[Tasks]
Name: "desktopicon"; Description: "Buat ikon di Desktop"; GroupDescription: "Ikon tambahan:"; Flags: checkedonce

[Files]
Source: "..\build\win7\ApotekPahala\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\Panduan Windows 7"; Filename: "{app}\PANDUAN-WINDOWS7.txt"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Jalankan {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Jangan hapus data pengguna di %LOCALAPPDATA%\ApotekPahala.
Type: filesandordirs; Name: "{app}\backend"
Type: filesandordirs; Name: "{app}\docs"
Type: files; Name: "{app}\README.md"
