@echo off
setlocal EnableDelayedExpansion
title Stop GreenSynth

echo ============================================================
echo   GREEN SYNTH ANALYTICS — STOPPING SERVICES
echo ============================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$stopped = 0;" ^
  "$ports = @(8000, 5173);" ^
  "foreach ($port in $ports) {" ^
  "  $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue;" ^
  "  if ($conns) {" ^
  "    foreach ($conn in $conns) {" ^
  "      $procId = $conn.OwningProcess;" ^
  "      if ($procId -and $procId -gt 0) {" ^
  "        try {" ^
  "          $proc = Get-Process -Id $procId -ErrorAction Stop;" ^
  "          Write-Host ('  [STOPPING] Port ' + $port + ' (Process: ' + $proc.ProcessName + ', PID: ' + $procId + ')');" ^
  "          Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue;" ^
  "          $stopped++;" ^
  "        } catch {" ^
  "          Write-Host ('  [NOTE] Could not stop PID ' + $procId + ': ' + $_.Exception.Message);" ^
  "        }" ^
  "      }" ^
  "    }" ^
  "  } else {" ^
  "    Write-Host ('  [INFO] Port ' + $port + ' is not in use.');" ^
  "  }" ^
  "};" ^
  "if ($stopped -gt 0) {" ^
  "  Write-Host '`n  All GreenSynth background services have been safely stopped.';" ^
  "} else {" ^
  "  Write-Host '`n  No active GreenSynth services found.';" ^
  "}"

echo.
echo ============================================================
echo   SHUTDOWN COMPLETE
echo ============================================================
echo.
pause
