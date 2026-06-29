; Instalador do Ditar — per-user (sem UAC), instala em %LocalAppData%\Ditar.
; Cobre AC-3 (sem admin), AC-4 (autostart opcional), AC-6 (icone). Ver
; governance/_specs/R1-tem-exe/spec.md e tasks.md (tasks 10-11).
;
; Compilar:
;   "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" build\installer.iss
; (consome a pasta onedir em build\dist\Ditar — rode o PyInstaller antes.)

#define MyAppName "Ditar"
#define MyAppVersion "1.3.7"
#define MyAppPublisher "Eliezer Carsoni"
#define MyAppExeName "Ditar.exe"

[Setup]
AppId={{A2D986DC-87CA-4D0B-B25C-A9A9453A7282}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
; --- per-user, SEM elevacao (AC-3) ---
PrivilegesRequired=lowest
DefaultDirName={localappdata}\{#MyAppName}
DisableProgramGroupPage=yes
DisableDirPage=auto
; saida e identidade
OutputDir=installer-output
OutputBaseFilename=Ditar-Setup-{#MyAppVersion}
SetupIconFile=..\app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
WizardStyle=modern
; x64 (o bundle traz DLLs CUDA x64)
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; compressao (balanço tamanho x tempo; AC-8 < 2GB)
Compression=lzma2/normal
SolidCompression=yes
; auto-update: o updater fecha o Ditar via .bat destacado antes de instalar (ADR-0003);
; o app e windowed (sem janela), entao CloseApplications/RestartApplications do Inno nao o pegam.

[Languages]
Name: "ptbr"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "startup"; Description: "Iniciar o {#MyAppName} com o Windows"; GroupDescription: "Inicializacao:"; Flags: unchecked
Name: "desktopicon"; Description: "Criar atalho na area de trabalho"; GroupDescription: "Atalhos:"

[Files]
Source: "dist\Ditar\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autoprograms}\Transcrever (linha de comando)"; Filename: "{app}\Transcrever.exe"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Autostart (AC-4): grava a chave Run do usuario só se a task "startup" for marcada.
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; \
  ValueName: "Ditar"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: startup

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar o {#MyAppName} agora"; Flags: nowait postinstall skipifsilent
