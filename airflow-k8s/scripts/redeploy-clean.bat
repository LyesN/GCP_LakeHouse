@echo off
chcp 65001 >nul

:: Se placer dans le repertoire du script
cd /d "%~dp0\.."

echo =====================================================
echo       REDEPLOIEMENT COMPLET AIRFLOW CORRIGE
echo =====================================================
echo.

echo [INFO] Repertoire de travail: %CD%
echo.

echo [ETAPE 1/3] Arret complet de l'infrastructure...
call scripts\stop-clean.bat

echo.
echo [ETAPE 2/3] Suppression complete du namespace...
echo [WARNING] Suppression de toutes les donnees Airflow!
choice /M "Continuer la suppression complete"
if errorlevel 2 (
    echo [INFO] Arret du redeploiement
    pause
    exit /b 0
)

kubectl delete namespace airflow --ignore-not-found=true
echo [INFO] Attente de la suppression complete (30s)...
timeout /t 30 /nobreak >nul

echo [OK] Namespace supprime

echo.
echo [ETAPE 3/3] Redeploiement avec corrections...
call scripts\deploy-clean.bat

echo.
echo =====================================================
echo     [SUCCESS] REDEPLOIEMENT COMPLET TERMINE!
echo =====================================================
echo.
echo [INFO] Airflow a ete completement redeploye avec les corrections
echo [INFO] Les DAGs devraient maintenant apparaitre correctement
echo.
pause