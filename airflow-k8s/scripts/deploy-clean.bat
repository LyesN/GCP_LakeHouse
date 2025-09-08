@echo off
chcp 65001 >nul

:: Se placer dans le repertoire du script
cd /d "%~dp0\.."

echo =====================================================
echo    DEPLOIEMENT AIRFLOW SUR KUBERNETES (Windows)
echo =====================================================
echo.
echo [INFO] Repertoire de travail: %CD%
echo.

:: Verification des prerequis
echo [ETAPE 1/6] Verification des prerequis...
kubectl version --client >nul 2>&1
if errorlevel 1 (
    echo [ERROR] kubectl n'est pas installe ou pas dans le PATH
    echo    Installez kubectl: https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/
    pause
    exit /b 1
)

docker version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker n'est pas installe ou pas demarre
    echo    Installez Docker Desktop et demarrez-le
    pause
    exit /b 1
)

echo [OK] kubectl et Docker sont disponibles

:: Verification du cluster Kubernetes
echo.
echo [ETAPE 2/6] Verification du cluster Kubernetes...
kubectl cluster-info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Pas de cluster Kubernetes actif
    echo    Demarrez Docker Desktop et activez Kubernetes
    pause
    exit /b 1
)

echo [OK] Cluster Kubernetes detecte

:: Creation du namespace
echo.
echo [ETAPE 3/6] Creation du namespace airflow...
if not exist "manifests\namespace.yaml" (
    echo [ERROR] Fichier manifests\namespace.yaml introuvable
    echo    Verifiez que vous etes dans le bon repertoire
    echo    Repertoire actuel: %CD%
    pause
    exit /b 1
)
kubectl apply -f manifests/namespace.yaml
if errorlevel 1 (
    echo [ERROR] Erreur creation du namespace
    pause
    exit /b 1
)

echo [OK] Namespace cree

:: Deploiement des bases de donnees
echo.
echo [ETAPE 4/6] Deploiement PostgreSQL et Redis...
kubectl apply -f manifests/postgresql.yaml
kubectl apply -f manifests/redis.yaml
if errorlevel 1 (
    echo [ERROR] Erreur deploiement des bases de donnees
    pause
    exit /b 1
)

echo [INFO] Attente du demarrage de PostgreSQL (30s)...
timeout /t 30 /nobreak >nul

:: Configuration Airflow
echo.
echo [ETAPE 5/6] Configuration et volumes Airflow...
kubectl apply -f manifests/airflow-configmap.yaml
kubectl apply -f manifests/airflow-volumes-fixed.yaml
if errorlevel 1 (
    echo [ERROR] Erreur configuration Airflow
    pause
    exit /b 1
)

echo [OK] Configuration appliquee

echo [INFO] Attente de l'initialisation des DAGs (60s)...
timeout /t 60 /nobreak >nul

:: Deploiement des services Airflow
echo.
echo [ETAPE 6/6] Deploiement des services Airflow...
echo   - Webserver...
kubectl apply -f manifests/airflow-webserver.yaml
echo   - Scheduler...
kubectl apply -f manifests/airflow-scheduler.yaml
echo   - Workers...
kubectl apply -f manifests/airflow-worker.yaml
echo   - Flower (monitoring)...
kubectl apply -f manifests/airflow-flower.yaml

if errorlevel 1 (
    echo [ERROR] Erreur deploiement des services Airflow
    pause
    exit /b 1
)

echo.
echo =====================================================
echo        [SUCCESS] DEPLOIEMENT AIRFLOW TERMINE!
echo =====================================================
echo.
echo [INFO] INFORMATIONS DE CONNEXION:
echo.
echo   Web UI Airflow: http://localhost:32194
echo      Username: admin
echo      Password: admin123
echo.
echo   Flower (Celery): http://localhost:31847  
echo      Username: admin
echo      Password: flower123
echo.
echo [INFO] COMMANDES UTILES:
echo.
echo   # Voir les pods
echo   kubectl get pods -n airflow
echo.
echo   # Voir les services
echo   kubectl get services -n airflow
echo.
echo   # Voir les logs du webserver
echo   kubectl logs -n airflow deployment/airflow-webserver
echo.
echo   # Voir les logs du scheduler
echo   kubectl logs -n airflow deployment/airflow-scheduler
echo.
echo [INFO] Attente du demarrage des services (peut prendre 2-3 minutes)...
echo    Surveillez: kubectl get pods -n airflow -w
echo.

:: Attendre que les pods soient prets
echo [INFO] Verification du statut des pods...
:wait_loop
kubectl get pods -n airflow --no-headers 2>nul | findstr "Running" >nul
if errorlevel 1 (
    echo   [INFO] Services en cours de demarrage... (Ctrl+C pour arreter l'attente)
    timeout /t 10 /nobreak >nul
    goto wait_loop
)

echo [OK] Services demarres!
echo.
echo [SUCCESS] Airflow est maintenant accessible sur: http://localhost:32194
echo.
pause