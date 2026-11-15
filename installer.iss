#define MyAppName "FIDEL LKPR Live - updater"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Fidel"
#define MyAppExeName "FidelLKPRUpdater.exe"

[Setup]
AppId={{A4A4B671-9E66-4B7E-9D58-6C2D53D1AFA1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\FIDEL LKPR Live - updater
DefaultGroupName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=assets\app_icon.ico
OutputDir=installer
OutputBaseFilename=Fidel_LKPR_Updater_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch FIDEL LKPR Live - updater"; Flags: postinstall nowait skipifsilent
