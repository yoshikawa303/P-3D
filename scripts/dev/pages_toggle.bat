@echo off
rem P-3D: GitHub Pages 一時公開の切替（Windows ダブルクリック用）。
rem Private なら Public にして Pages へ main を配信、Public なら Private に戻す。詳細は pages_toggle.py。
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (
  py -3 pages_toggle.py %*
) else (
  python pages_toggle.py %*
)
echo.
pause
