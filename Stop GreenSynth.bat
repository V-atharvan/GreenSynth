@echo off
title Stop GreenSynth
echo ============================================================
echo   STOPPING GREENSYNTH ANALYTICS PLATFORM
echo ============================================================
echo.

echo Terminating backend process on port 8000...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p = (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess; if ($p) { Stop-Process -Id $p -Force -ErrorAction SilentlyContinue; echo 'Backend process terminated.' } else { echo 'No backend process running on port 8000.' }"

echo Terminating frontend process on port 5173...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p = (Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue).OwningProcess; if ($p) { Stop-Process -Id $p -Force -ErrorAction SilentlyContinue; echo 'Frontend process terminated.' } else { echo 'No frontend process running on port 5173.' }"

echo.
echo ============================================================
echo   ALL GREENSYNTH SERVICES STOPPED SUCCESSFULLY
echo ============================================================
echo.
pause
