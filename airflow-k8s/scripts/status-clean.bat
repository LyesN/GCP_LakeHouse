@echo off
chcp 65001 >nul

REM Se placer dans le répertoire du script
cd /d "%~dp0\.."

echo =====================================================
echo      STATUS AIRFLOW SUR KUBERNETES
echo =====================================================
echo.

echo [INFO] NAMESPACE AIRFLOW:
kubectl get namespace airflow 2>nul
if errorlevel 1 (
    echo [ERROR] Namespace 'airflow' n'existe pas
    echo    Lancez deploy-clean.bat pour installer Airflow
    echo.
    pause
    exit /b 1
)

echo.
echo [INFO] PODS AIRFLOW:
kubectl get pods -n airflow -o wide

echo.
echo [INFO] SERVICES:
kubectl get services -n airflow

echo.
echo [INFO] PERSISTENT VOLUME CLAIMS:
kubectl get pvc -n airflow

echo.
echo [INFO] CONFIGMAPS:
kubectl get configmaps -n airflow

echo.
echo =====================================================
echo              LIENS D'ACCES
echo =====================================================
echo.
echo Web UI Airflow: http://localhost:32794
echo    Username: admin / Password: admin123
echo.
echo Flower (Celery): http://localhost:31847
echo    Username: admin / Password: flower123
echo.

REM Verifier si les services sont accessibles
echo [INFO] Test de connectivite...
curl -s -o nul -w "%%{http_code}" http://localhost:32794/health 2>nul | findstr "200" >nul
if not errorlevel 1 (
    echo [OK] Airflow Web UI accessible
) else (
    echo [WARNING] Airflow Web UI pas encore accessible
)

curl -s -o nul -w "%%{http_code}" http://localhost:31847 2>nul | findstr "200" >nul
if not errorlevel 1 (
    echo [OK] Flower accessible  
) else (
    echo [WARNING] Flower pas encore accessible
)

echo.
echo [INFO] COMMANDES UTILES:
echo.
echo   # Voir les logs en temps reel
echo   kubectl logs -n airflow deployment/airflow-webserver -f
echo.
echo   # Redemarrer un service
echo   kubectl rollout restart deployment/airflow-webserver -n airflow
echo.
echo   # Acceder a un pod
echo   kubectl exec -it -n airflow deployment/airflow-webserver -- bash
echo.
echo   # Voir les variables d'environnement
echo   kubectl exec -n airflow deployment/airflow-webserver -- env | grep AIRFLOW
echo.
pause