@echo off
setlocal EnableDelayedExpansion
title GreenSynth Status

echo ============================================================
echo   GREEN SYNTH ANALYTICS — SYSTEM AND SERVICE STATUS
echo ============================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$bConn = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue;" ^
  "$fConn = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue;" ^
  "Write-Host '  SERVICE STATUS:';" ^
  "Write-Host '  --------------------------------------------------';" ^
  "if ($bConn) {" ^
  "  $bProc = (Get-Process -Id $bConn[0].OwningProcess -ErrorAction SilentlyContinue).ProcessName;" ^
  "  Write-Host ('  * Backend  (Port 8000) : RUNNING (PID: ' + $bConn[0].OwningProcess + ', Process: ' + $bProc + ')');" ^
  "  try {" ^
  "    $h = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 2;" ^
  "    Write-Host ('    - Status           : ' + $h.status);" ^
  "    Write-Host ('    - Version          : ' + $h.version);" ^
  "    Write-Host ('    - Database Mode    : ' + $h.database);" ^
  "    Write-Host ('    - Storage Backend  : ' + $h.storage_backend);" ^
  "  } catch {" ^
  "    Write-Host '    - Health Endpoint  : Not responding';" ^
  "  }" ^
  "} else {" ^
  "  Write-Host '  * Backend  (Port 8000) : NOT RUNNING';" ^
  "};" ^
  "Write-Host '';" ^
  "if ($fConn) {" ^
  "  $fProc = (Get-Process -Id $fConn[0].OwningProcess -ErrorAction SilentlyContinue).ProcessName;" ^
  "  Write-Host ('  * Frontend (Port 5173) : RUNNING (PID: ' + $fConn[0].OwningProcess + ', Process: ' + $fProc + ')');" ^
  "  Write-Host '    - URL              : http://localhost:5173';" ^
  "} else {" ^
  "  Write-Host '  * Frontend (Port 5173) : NOT RUNNING';" ^
  "};" ^
  "Write-Host '  --------------------------------------------------';"

echo.
echo ============================================================
echo   CHECK COMPLETE
echo ============================================================
echo.
pause
