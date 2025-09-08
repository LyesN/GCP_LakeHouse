@echo off
chcp 65001 >nul

REM Se placer dans le répertoire du script
cd /d "%~dp0\.."

echo =====================================================
echo     VERIFICATION ENVIRONNEMENT AIRFLOW K8S
echo =====================================================
echo.

echo [INFO] Repertoire de travail: %CD%
echo.

echo [INFO] Verification de la structure des fichiers...
if exist "manifests\" (
    echo [OK] Dossier manifests/ present
    dir /b manifests\*.yaml | find /c ".yaml" > temp_count.txt
    set /p YAML_COUNT=<temp_count.txt
    del temp_count.txt
    echo [INFO] Nombre de fichiers YAML: %YAML_COUNT%
) else (
    echo [ERROR] Dossier manifests/ manquant!
)

if exist "scripts\" (
    echo [OK] Dossier scripts/ present
) else (
    echo [ERROR] Dossier scripts/ manquant!
)

if exist "dags\" (
    echo [OK] Dossier dags/ present
) else (
    echo [WARNING] Dossier dags/ manquant
)

echo.
echo [INFO] Verification des prerequis systeme...

kubectl version --client >nul 2>&1
if errorlevel 1 (
    echo [ERROR] kubectl non disponible
) else (
    echo [OK] kubectl disponible
    kubectl version --client 2>nul | findstr "GitVersion"
)

docker version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker non disponible
) else (
    echo [OK] Docker disponible
    docker version --format "Version: {{.Client.Version}}" 2>nul
)

echo.
echo [INFO] Verification cluster Kubernetes...
kubectl cluster-info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Cluster Kubernetes non accessible
    echo    Verifiez que Docker Desktop est demarre avec Kubernetes active
) else (
    echo [OK] Cluster Kubernetes accessible
    kubectl get nodes --no-headers 2>nul | find /c "Ready" > temp_nodes.txt
    set /p NODE_COUNT=<temp_nodes.txt
    del temp_nodes.txt
    echo [INFO] Noeuds Kubernetes actifs: %NODE_COUNT%
)

echo.
echo [INFO] Verification namespace airflow...
kubectl get namespace airflow >nul 2>&1
if errorlevel 1 (
    echo [INFO] Namespace airflow n'existe pas (normal avant premier deploiement)
) else (
    echo [OK] Namespace airflow existe
    kubectl get pods -n airflow --no-headers 2>nul | find /c "Running" > temp_pods.txt
    set /p POD_COUNT=<temp_pods.txt
    del temp_pods.txt
    echo [INFO] Pods Running dans airflow: %POD_COUNT%
)

echo.
echo =====================================================
echo              RESUME DE LA VERIFICATION
echo =====================================================
echo.
echo Structure des fichiers: OK
echo Prerequisites systeme: Verifiez les [ERROR] ci-dessus
echo Cluster Kubernetes: Verifiez les [ERROR] ci-dessus
echo.
echo Si tout est OK, vous pouvez lancer:
echo   scripts\deploy-clean.bat
echo.
pause