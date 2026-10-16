#ifndef AppVersion
  #define AppVersion "0.1.1"
#endif
#ifndef PayloadDir
  #define PayloadDir "build\payload"
#endif
#ifndef CaddyExePath
  #define CaddyExePath "build\caddy\caddy.exe"
#endif
#ifndef CaddyLicensePath
  #define CaddyLicensePath "build\caddy\LICENSE"
#endif

[Setup]
AppId={{8F2CA779-4C93-49A4-B40E-1D05EE812BF1}
AppName=MS Contable
AppVersion={#AppVersion}
DefaultDirName={autopf}\MS Contable
DefaultGroupName=MS Contable
SetupIconFile={#SourcePath}\mscontable-setup.ico
UninstallDisplayIcon={app}\windows\mscontable.ico
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=dist\https
OutputBaseFilename=MSContable-Setup-{#AppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
UninstallDisplayName=MS Contable

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
Source: "{#PayloadDir}\app\*"; DestDir: "{app}"; Excludes: "windows\launch.ps1,windows\launch-hidden.vbs,windows\initialize.ps1"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#PayloadDir}\python\*"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#CaddyExePath}"; DestDir: "{app}\caddy"; DestName: "caddy.exe"; Flags: ignoreversion
Source: "{#CaddyLicensePath}"; DestDir: "{app}\licenses"; DestName: "Caddy-LICENSE.txt"; Flags: ignoreversion
Source: "Caddyfile"; DestDir: "{app}\caddy"; Flags: ignoreversion
Source: "launch.ps1"; DestDir: "{app}\windows"; Flags: ignoreversion
Source: "launch-hidden.vbs"; DestDir: "{app}\windows"; Flags: ignoreversion
Source: "initialize.ps1"; DestDir: "{app}\windows"; Flags: ignoreversion
Source: "prepare-https.ps1"; DestDir: "{app}\windows"; Flags: ignoreversion
Source: "configure-hosts.ps1"; DestDir: "{app}\windows"; Flags: ignoreversion
Source: "uninstall.ps1"; DestDir: "{app}\windows"; Flags: ignoreversion
Source: "..\..\static\images\favicon.ico"; DestDir: "{app}\windows"; DestName: "mscontable.ico"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\MS Contable"; Filename: "{app}\windows\launch-hidden.vbs"; IconFilename: "{app}\windows\mscontable.ico"; Tasks: startmenuicon
Name: "{autodesktop}\MS Contable"; Filename: "{app}\windows\launch-hidden.vbs"; IconFilename: "{app}\windows\mscontable.ico"; Tasks: desktopicon

[Tasks]
Name: "startmenuicon"; Description: "Crear acceso directo en el menú Inicio"; GroupDescription: "Accesos directos:"; Flags: checkedonce
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Run]
Filename: "{sys}\wscript.exe"; Parameters: """{app}\windows\launch-hidden.vbs"""; Description: "Abrir MS Contable al finalizar"; Flags: postinstall skipifsilent nowait runasoriginaluser

[UninstallRun]
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\windows\configure-hosts.ps1"" -Action Remove"; RunOnceId: "RemoveMSContableHost"; Flags: runhidden waituntilterminated
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\windows\uninstall.ps1"""; RunOnceId: "StopMSContable"; Flags: runhidden waituntilterminated

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  PowerShellPath: String;
  ScriptPath: String;
  Parameters: String;
begin
  if CurStep = ssPostInstall then
  begin
    WizardForm.StatusLabel.Caption := 'Configurando MS Contable...';
    WizardForm.StatusLabel.Update;
    WizardForm.Update;

    PowerShellPath := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');
    ScriptPath := ExpandConstant('{app}\windows\configure-hosts.ps1');
    Parameters := '-NoProfile -ExecutionPolicy Bypass -File "' + ScriptPath + '" -Action Add';

    if not Exec(PowerShellPath, Parameters, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
      RaiseException('No se pudo configurar el nombre local mscontable en Windows.');
    if ResultCode <> 0 then
      RaiseException('No se pudo configurar el nombre local mscontable. Revisá si ya existe una asignación en el archivo hosts.');

    WizardForm.StatusLabel.Caption := 'Instalando certificado HTTPS...';
    WizardForm.StatusLabel.Update;
    WizardForm.Update;

    ScriptPath := ExpandConstant('{app}\windows\prepare-https.ps1');
    Parameters := '-NoProfile -STA -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + ScriptPath + '"';
    if not ExecAsOriginalUser(PowerShellPath, Parameters, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) or (ResultCode <> 0) then
    begin
      ScriptPath := ExpandConstant('{app}\windows\uninstall.ps1');
      Parameters := '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + ScriptPath + '"';
      ExecAsOriginalUser(PowerShellPath, Parameters, '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      Exec(PowerShellPath, '-NoProfile -ExecutionPolicy Bypass -File "' + ExpandConstant('{app}\windows\configure-hosts.ps1') + '" -Action Remove', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      RaiseException('No se pudo preparar HTTPS para MS Contable. La entrada local se quitó; ejecutá nuevamente el instalador para reintentar.');
    end;

    WizardForm.StatusLabel.Caption := 'Preparando la base de datos...';
    WizardForm.StatusLabel.Update;
    WizardForm.Update;

    ScriptPath := ExpandConstant('{app}\windows\initialize.ps1');
    Parameters := '-NoProfile -STA -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + ScriptPath + '"';
    if not ExecAsOriginalUser(PowerShellPath, Parameters, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) or (ResultCode <> 0) then
    begin
      ScriptPath := ExpandConstant('{app}\windows\uninstall.ps1');
      Parameters := '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + ScriptPath + '"';
      ExecAsOriginalUser(PowerShellPath, Parameters, '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      Exec(PowerShellPath, '-NoProfile -ExecutionPolicy Bypass -File "' + ExpandConstant('{app}\windows\configure-hosts.ps1') + '" -Action Remove', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      RaiseException('No se pudo inicializar MS Contable. Revisá los datos ingresados y ejecutá nuevamente el instalador.');
    end;
  end;
end;
