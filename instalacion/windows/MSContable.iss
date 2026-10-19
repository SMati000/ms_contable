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
AppPublisher=MS Contable
VersionInfoCompany=MS Contable
VersionInfoProductName=MS Contable
Uninstallable=yes
DefaultDirName={autopf}\MS Contable
DefaultGroupName=MS Contable
DisableProgramGroupPage=yes
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
Name: "{app}\Desinstalar MS Contable"; Filename: "{uninstallexe}"; WorkingDir: "{app}"; IconFilename: "{app}\windows\mscontable.ico"
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
var
  KeepUserData: Boolean;

function InitializeUninstall: Boolean;
var
  Form: TSetupForm;
  MessageLabel: TNewStaticText;
  KeepDataButton: TNewButton;
  DeleteDataButton: TNewButton;
  CancelButton: TNewButton;
  DialogResult: Integer;
begin
  KeepUserData := True;
  Result := True;

  if UninstallSilent then
    Exit;

  Form := CreateCustomForm(ScaleX(560), ScaleY(260), False, False);
  try
    Form.Caption := 'Desinstalar MS Contable';
    Form.Position := poScreenCenter;
    Form.BorderStyle := bsDialog;
    Form.BorderIcons := [];

    MessageLabel := TNewStaticText.Create(Form);
    MessageLabel.Parent := Form;
    MessageLabel.Left := ScaleX(16);
    MessageLabel.Top := ScaleY(18);
    MessageLabel.Width := ScaleX(528);
    MessageLabel.Height := ScaleY(140);
    MessageLabel.AutoSize := False;
    MessageLabel.WordWrap := True;
    MessageLabel.Caption := 'Elegí qué hacer con tus datos antes de desinstalar. Si elegís borrarlos, se eliminarán la base de datos, sus copias de seguridad, las claves de cifrado, la configuración y los registros. Esta acción no se puede deshacer.';

    KeepDataButton := TNewButton.Create(Form);
    KeepDataButton.Parent := Form;
    KeepDataButton.Left := ScaleX(16);
    KeepDataButton.Top := ScaleY(198);
    KeepDataButton.Width := ScaleX(220);
    KeepDataButton.Height := ScaleY(36);
    KeepDataButton.Caption := 'Desinstalar y conservar datos';
    KeepDataButton.ModalResult := mrYes;
    KeepDataButton.Default := True;

    DeleteDataButton := TNewButton.Create(Form);
    DeleteDataButton.Parent := Form;
    DeleteDataButton.Left := ScaleX(246);
    DeleteDataButton.Top := ScaleY(198);
    DeleteDataButton.Width := ScaleX(200);
    DeleteDataButton.Height := ScaleY(36);
    DeleteDataButton.Caption := 'Desinstalar y borrar datos';
    DeleteDataButton.ModalResult := mrNo;

    CancelButton := TNewButton.Create(Form);
    CancelButton.Parent := Form;
    CancelButton.Left := ScaleX(456);
    CancelButton.Top := ScaleY(198);
    CancelButton.Width := ScaleX(88);
    CancelButton.Height := ScaleY(36);
    CancelButton.Caption := 'Cancelar';
    CancelButton.ModalResult := mrCancel;
    CancelButton.Cancel := True;

    DialogResult := Form.ShowModal;
    if DialogResult = mrYes then
    begin
      KeepUserData := True;
      Result := True;
    end
    else if DialogResult = mrNo then
    begin
      KeepUserData := False;
      Result := True;
    end
    else
      Result := False;
  finally
    Form.Free;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataRoot: String;
  RemovalFailed: Boolean;
begin
  if (CurUninstallStep = usPostUninstall) and not KeepUserData then
  begin
    DataRoot := ExpandConstant('{localappdata}\MSContable');
    RemovalFailed := False;

    if DirExists(DataRoot + '\data') and not DelTree(DataRoot + '\data', True, True, True) then
      RemovalFailed := True;
    if DirExists(DataRoot + '\config') and not DelTree(DataRoot + '\config', True, True, True) then
      RemovalFailed := True;
    if DirExists(DataRoot + '\logs') and not DelTree(DataRoot + '\logs', True, True, True) then
      RemovalFailed := True;

    if RemovalFailed then
      MsgBox('MS Contable se desinstaló, pero Windows no pudo eliminar todos los datos. Revisá la carpeta ' + DataRoot + '.', mbError, MB_OK);
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  DatabasePath: String;
  DatabaseKeyPath: String;
  DatabaseContents: AnsiString;
begin
  Result := '';
  NeedsRestart := False;

  if ExpandConstant('{param:SMOKETEST|0}') = '1' then
    Exit;

  DatabasePath := ExpandConstant('{localappdata}\MSContable\data\db.sqlite3');
  DatabaseKeyPath := ExpandConstant('{localappdata}\MSContable\config\database-key.dpapi');
  if not FileExists(DatabasePath) then
    Exit;

  if FileExists(DatabaseKeyPath) then
  begin
    Result := 'La base existente está cifrada con SQLCipher y contiene datos que esta versión del instalador no puede abrir. No se modificó la base. Usá una versión de MS Contable compatible con SQLCipher para conservar esos datos.';
    Exit;
  end;

  if not LoadStringFromFile(DatabasePath, DatabaseContents) then
  begin
    Result := 'No se pudo comprobar la base existente. Cerrá MS Contable y volvé a ejecutar el instalador.';
    Exit;
  end;

  if Copy(DatabaseContents, 1, 16) <> 'SQLite format 3'#0 then
    Result := 'La base existente no es SQLite estándar o está cifrada. Esta versión no puede abrirla; se canceló la instalación para proteger tus datos. Usá una versión compatible con el formato de esa base.';
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  PowerShellPath: String;
  ScriptPath: String;
  Parameters: String;
begin
  if CurStep = ssPostInstall then
  begin
    if ExpandConstant('{param:SMOKETEST|0}') = '1' then
    begin
      if not SaveStringToFile(ExpandConstant('{app}\windows\smoke-test.marker'), '1', False) then
        RaiseException('No se pudo preparar el entorno aislado de prueba.');
      Exit;
    end;

    PowerShellPath := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');
    WizardForm.StatusLabel.Caption := 'Preparando la base de datos...';
    WizardForm.StatusLabel.Update;
    WizardForm.Update;

    ScriptPath := ExpandConstant('{app}\windows\initialize.ps1');
    Parameters := '-NoProfile -STA -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + ScriptPath + '"';
    if not ExecAsOriginalUser(PowerShellPath, Parameters, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) or (ResultCode <> 0) then
      RaiseException('No se pudo inicializar MS Contable. Revisá los datos ingresados y ejecutá nuevamente el instalador.');

    WizardForm.StatusLabel.Caption := 'Configurando el acceso local...';
    WizardForm.StatusLabel.Update;
    WizardForm.Update;

    ScriptPath := ExpandConstant('{app}\windows\configure-hosts.ps1');
    Parameters := '-NoProfile -ExecutionPolicy Bypass -File "' + ScriptPath + '" -Action Add';
    if not Exec(PowerShellPath, Parameters, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) or (ResultCode <> 0) then
      RaiseException('No se pudo configurar el nombre local mscontable. Revisá si ya existe una asignación en el archivo hosts.');

    WizardForm.StatusLabel.Caption := 'Instalando certificado HTTPS...';
    WizardForm.StatusLabel.Update;
    WizardForm.Update;

    ScriptPath := ExpandConstant('{app}\windows\prepare-https.ps1');
    Parameters := '-NoProfile -STA -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + ScriptPath + '" -NoUI';
    if not ExecAsOriginalUser(PowerShellPath, Parameters, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) or (ResultCode <> 0) then
    begin
      Exec(PowerShellPath, '-NoProfile -ExecutionPolicy Bypass -File "' + ExpandConstant('{app}\windows\configure-hosts.ps1') + '" -Action Remove', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      RaiseException('No se pudo preparar HTTPS para MS Contable. Revisá los registros en %LOCALAPPDATA%\MSContable\logs.');
    end;
  end;
end;
