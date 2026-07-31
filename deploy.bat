@echo off
echo ====================================
echo   DEPLOIEMENT AUTOMATIQUE VERS GITHUB
echo ====================================
echo.

git init
git add .
git commit -m "Mise a jour automatique Render"
git branch -M main

set /p repo="Collez le lien de votre depot GitHub (ex: https://github.com/votre_nom/invi_projet.git) : "

git remote remove origin >nul 2>&1
git remote add origin %repo%
git push -u origin main --force

echo.
echo ====================================
echo   SUCCES ! Votre projet est en ligne sur Render !
echo ====================================
pause
