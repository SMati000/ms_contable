#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif

[Setup]
AppId={{9BCA550C-33D4-4D71-8AA7-D333805A0802}
AppName=MS Contable
AppVersion={#AppVersion}
AppPublisher=MS Contable
DefaultDirName={localappdata}\Programs\MS Contable
DefaultGroupName=MS Contable
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=dist
OutputBaseFilename=MSContable-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=mscontable-setup.ico
UninstallDisplayIcon={app}\static\images\favicon.ico

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
Source: "build\payload\app\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "build\payload\python\*"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\MS Contable"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\windows\launch-hidden.vbs"" Start"; WorkingDir: "{app}"; IconFilename: "{app}\static\images\favicon.ico"; IconIndex: 0
Name: "{autoprograms}\Detener MS Contable"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\windows\launch-hidden.vbs"" Stop"; WorkingDir: "{app}"; IconFilename: "{app}\static\images\favicon.ico"; IconIndex: 0
Name: "{autoprograms}\Inicializar o actualizar MS Contable"; Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\windows\initialize.ps1"""; WorkingDir: "{app}"; IconFilename: "{app}\static\images\favicon.ico"; IconIndex: 0
Name: "{autodesktop}\MS Contable"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\windows\launch-hidden.vbs"" Start"; WorkingDir: "{app}"; IconFilename: "{app}\static\images\favicon.ico"; IconIndex: 0; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Run]
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\windows\initialize.ps1"""; Description: "Preparar MS Contable"; Flags: postinstall runasoriginaluser waituntilterminated skipifsilent

[UninstallRun]
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""{app}\windows\launch.ps1"" -Action Stop"; Flags: runhidden waituntilterminated; RunOnceId: "StopMSContable"

[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
  LauncherPath: String;
  PowerShellPath: String;
  Parameters: String;
begin
  Result := '';
  LauncherPath := ExpandConstant('{app}\windows\launch.ps1');
  PowerShellPath := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');

  if FileExists(LauncherPath) then
  begin
    Parameters := '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + LauncherPath + '" -Action Stop';
    if not Exec(PowerShellPath, Parameters, ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, ResultCode) then
      Result := 'No se pudo detener MS Contable antes de actualizar.'
    else if ResultCode <> 0 then
      Result := 'MS Contable no pudo detenerse antes de actualizar.';
  end;
end;
