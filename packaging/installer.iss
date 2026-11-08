; Inno Setup script – per-user installer (no admin rights), Start menu entry, optional autostart.
;   iscc /DAppVersion=1.0.0 packaging\installer.iss
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{8B3E7B2D-5C1A-4C55-9E0A-6D1F1D0C7A11}
AppName=Ditoo Control
AppVersion={#AppVersion}
AppVerName=Ditoo Control {#AppVersion}
AppPublisher=Kantaon
AppPublisherURL=https://github.com/kantaon/ditoo-control
AppSupportURL=https://github.com/kantaon/ditoo-control/issues
DefaultDirName={localappdata}\Programs\Ditoo Control
DefaultGroupName=Ditoo Control
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=Output
OutputBaseFilename=DitooControl-Setup
SetupIconFile=..\src\ditoo_control\ui\icon.ico
UninstallDisplayIcon={app}\DitooControl.exe
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
LicenseFile=..\LICENSE

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "cs"; MessagesFile: "compiler:Languages\Czech.isl"

[CustomMessages]
en.Autostart=Start Ditoo Control when I sign in to Windows
cs.Autostart=Spouštět Ditoo Control po přihlášení do Windows
en.LaunchNow=Start Ditoo Control now
cs.LaunchNow=Spustit Ditoo Control
en.NeedWebView2=The Ditoo Control window needs Microsoft Edge WebView2, which isn't installed on this PC. Without it the app opens in your web browser instead.%n%nOpen the free WebView2 download page now?
cs.NeedWebView2=Okno Ditoo Control potřebuje Microsoft Edge WebView2, které na tomto PC chybí. Bez něj se aplikace otevře ve webovém prohlížeči.%n%nOtevřít stránku s bezplatným stažením WebView2?

[Tasks]
Name: "autostart"; Description: "{cm:Autostart}"; Flags: checkedonce
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\DitooControl\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\Ditoo Control"; Filename: "{app}\DitooControl.exe"
Name: "{userdesktop}\Ditoo Control"; Filename: "{app}\DitooControl.exe"; Tasks: desktopicon
Name: "{userstartup}\Ditoo Control"; Filename: "{app}\DitooControl.exe"; Parameters: "--hidden"; Tasks: autostart

[Run]
Filename: "{app}\DitooControl.exe"; Description: "{cm:LaunchNow}"; Flags: nowait postinstall skipifsilent

[Code]
{ The window uses Microsoft Edge WebView2 (built into Windows 11). Offer the download if it's missing. }
function HasWebView2(): Boolean;
var v: String;
begin
  Result := RegQueryStringValue(HKLM, 'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', v)
    or RegQueryStringValue(HKCU, 'Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', v)
    or RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', v);
  Result := Result and (v <> '') and (v <> '0.0.0.0');
end;

procedure CurStepChanged(CurStep: TSetupStep);
var code: Integer;
begin
  if (CurStep = ssPostInstall) and (not HasWebView2()) and (not WizardSilent()) then
    if MsgBox(CustomMessage('NeedWebView2'), mbConfirmation, MB_YESNO) = IDYES then
      ShellExec('open', 'https://developer.microsoft.com/microsoft-edge/webview2/', '', '', SW_SHOWNORMAL, ewNoWait, code);
end;

[UninstallRun]
Filename: "{cmd}"; Parameters: "/C taskkill /IM DitooControl.exe /F"; Flags: runhidden; RunOnceId: "StopApp"
