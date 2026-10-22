#define AppName "DuckCapture"
#define AppVersion "0.5.1"
#define AppExe "DuckCapture.exe"

#ifndef DuckCaptureSource
  #error "Use CRIAR-INSTALADOR.bat para informar a pasta isolada dos arquivos."
#endif

[Setup]
AppId={{E7A0BDB1-5D6B-47EA-919E-D755A9C8871F}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=DuckCapture
DefaultDirName={localappdata}\Programs\DuckCapture
DefaultGroupName=DuckCapture
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
WizardStyle=modern
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\DuckCapture.exe
SetupIconFile=..\.build\duckcapture.ico
OutputDir=..\installer_saida
OutputBaseFilename=DuckCapture-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos"; Flags: checkedonce

[Files]
Source: "{#DuckCaptureSource}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\THIRD-PARTY.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENCAS-E-DISTRIBUICAO.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\DuckCapture"; Filename: "{app}\DuckCapture.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\DuckCapture"; Filename: "{app}\DuckCapture.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\DuckCapture.exe"; Description: "Abrir DuckCapture"; Flags: nowait postinstall skipifsilent
