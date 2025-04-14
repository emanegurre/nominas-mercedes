[Setup]
AppName=Comparador de Nóminas
AppVersion=1.0
DefaultDirName={pf}\ComparadorNominas
DefaultGroupName=Comparador de Nóminas
OutputDir=.
OutputBaseFilename=ComparadorNominas_Setup
Compression=lzma
SolidCompression=yes
SetupIconFile=icon.ico

[Files]
; Archivos ejecutables y de aplicación
Source: "dist\interfaz_usuario.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Archivos de documentación
Source: "guia_usuario.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "documentacion_tecnica.md"; DestDir: "{app}\docs"; Flags: ignoreversion

; Archivos de datos de ejemplo
Source: "ejemplos\*"; DestDir: "{app}\ejemplos"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Comparador de Nóminas"; Filename: "{app}\interfaz_usuario.exe"
Name: "{group}\Guía de Usuario"; Filename: "{app}\docs\guia_usuario.md"
Name: "{group}\Documentación Técnica"; Filename: "{app}\docs\documentacion_tecnica.md"
Name: "{commondesktop}\Comparador de Nóminas"; Filename: "{app}\interfaz_usuario.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear un icono en el escritorio"; GroupDescription: "Iconos adicionales:"

[Run]
Filename: "{app}\interfaz_usuario.exe"; Description: "Iniciar Comparador de Nóminas"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  // Verificar que el sistema operativo sea Windows 11
  if not (CheckWin32Version(10, 0) and (GetWindowsVersion >= $0A00)) then
  begin
    MsgBox('Este software requiere Windows 11 o superior para funcionar correctamente.', mbError, MB_OK);
    Result := False;
  end
  else
    Result := True;
end;
