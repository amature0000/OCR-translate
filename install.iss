[Setup]
AppName=OCR Translator
AppVersion=1.4.0
DefaultDirName={userappdata}\Programs\OCR Translate
DefaultGroupName=OCR Translate
OutputBaseFilename=OCR-Translator-Setup
PrivilegesRequired=lowest
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
SetupIconFile=app\icon.ico

[Files]
Source: "Python\*"; DestDir: "{app}\python"; Flags: recursesubdirs
Source: "app\*";       DestDir: "{app}\app"; Flags: recursesubdirs

[Run]
; 1) pip 설치
Filename: "{app}\python\python.exe"; Parameters: "get-pip.py --quiet"; WorkingDir: "{app}\python"; StatusMsg: "pip 설치 중..."

; 2) 라이브러리 설치 (임베디드 Lib 폴더에 설치)
Filename: "{app}\python\python.exe"; Parameters: "-m pip install --upgrade pip"; WorkingDir: "{app}\python"; StatusMsg: "pip 업데이트 중..."
Filename: "{app}\python\python.exe"; Parameters: "-m pip install -r ""{app}\app\requirements.txt"" --target ""{app}\python\Lib\site-packages"""; WorkingDir: "{app}\python"; StatusMsg: "요구 라이브러리 설치 중..."

[Icons]
Name: "{userdesktop}\OCR Translate"; Filename: "{app}\python\pythonw.exe"; Parameters: """{app}\app\main.py"""; WorkingDir: "{app}\app"; IconFilename: "{app}\app\icon.ico"
