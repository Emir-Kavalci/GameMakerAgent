@echo off
rem Starts the GameMakerAgent Unreal bridge with the Python that ships inside
rem Unreal Engine, so nothing extra has to be installed.
rem Set GMA_UE_ENGINE_DIR to an engine folder (for example C:\Program Files\Epic Games\UE_5.7)
rem to choose the engine yourself.
setlocal EnableDelayedExpansion
set "PY_REL=Engine\Binaries\ThirdParty\Python3\Win64\python.exe"
set "PY="

if defined GMA_UE_ENGINE_DIR if exist "%GMA_UE_ENGINE_DIR%\%PY_REL%" set "PY=%GMA_UE_ENGINE_DIR%\%PY_REL%"

rem Engines installed with the Epic Games Launcher are listed in the registry.
if not defined PY (
  for /f "tokens=2,*" %%A in ('reg query "HKLM\SOFTWARE\EpicGames\Unreal Engine" /s /v InstalledDirectory 2^>nul ^| findstr /i "InstalledDirectory"') do (
    if exist "%%B\%PY_REL%" set "PY=%%B\%PY_REL%"
  )
)

rem The default install folder, in case the registry has nothing.
if not defined PY (
  for /d %%D in ("%ProgramFiles%\Epic Games\UE_5*") do (
    if exist "%%D\%PY_REL%" set "PY=%%D\%PY_REL%"
  )
)

if not defined PY (
  echo GameMakerAgent: no Unreal Engine 5 installation found. Set GMA_UE_ENGINE_DIR to your engine folder. 1>&2
  exit /b 1
)

"%PY%" -I -u "%~dp0unreal_bridge.py"
