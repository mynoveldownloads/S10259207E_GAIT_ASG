@echo off
echo ==========================================
echo   Starting Video Transcription Studio
echo ==========================================

:: Start Flask Backend
echo Starting Backend...
start "Backend (whisper_env)" cmd /k "conda activate whisper_env && cd backend && python app.py"

:: Start React Frontend
echo Starting Frontend...
start "Frontend (Vite)" cmd /k "cd frontend && npm run dev"

echo ==========================================
echo   Both services are starting!
echo   Backend: http://localhost:5000
echo   Frontend: http://localhost:3000
echo ==========================================
echo You can now access the app from other devices via your Tailscale IP on port 3000.
pause
