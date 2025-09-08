@echo off
chcp 65001 >nul

REM Se placer dans le répertoire du script
cd /d "%~dp0\.."

echo =====================================================
echo         LOGS AIRFLOW KUBERNETES
echo =====================================================

if "%1"=="" (
    echo Usage: logs-clean.bat [service]
    echo.
    echo Services disponibles:
    echo   webserver  - Interface Web Airflow
    echo   scheduler  - Planificateur de taches
    echo   worker     - Workers Celery
    echo   flower     - Interface monitoring Celery
    echo   postgres   - Base de donnees PostgreSQL
    echo   redis      - Cache Redis
    echo.
    echo Exemples:
    echo   logs-clean.bat webserver
    echo   logs-clean.bat scheduler
    echo.
    pause
    exit /b 1
)

set SERVICE=%1

if "%SERVICE%"=="webserver" (
    echo [INFO] Logs Airflow Webserver:
    kubectl logs -n airflow deployment/airflow-webserver --tail=100 -f
) else if "%SERVICE%"=="scheduler" (
    echo [INFO] Logs Airflow Scheduler:
    kubectl logs -n airflow deployment/airflow-scheduler --tail=100 -f
) else if "%SERVICE%"=="worker" (
    echo [INFO] Logs Airflow Workers:
    kubectl logs -n airflow deployment/airflow-worker --tail=100 -f
) else if "%SERVICE%"=="flower" (
    echo [INFO] Logs Flower:
    kubectl logs -n airflow deployment/airflow-flower --tail=100 -f
) else if "%SERVICE%"=="postgres" (
    echo [INFO] Logs PostgreSQL:
    kubectl logs -n airflow deployment/postgres --tail=100 -f
) else if "%SERVICE%"=="redis" (
    echo [INFO] Logs Redis:
    kubectl logs -n airflow deployment/redis --tail=100 -f
) else (
    echo [ERROR] Service '%SERVICE%' non reconnu
    echo.
    echo Services valides: webserver, scheduler, worker, flower, postgres, redis
    pause
    exit /b 1
)