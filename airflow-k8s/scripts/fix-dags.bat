@echo off
chcp 65001 >nul

:: Se placer dans le repertoire du script
cd /d "%~dp0\.."

echo =====================================================
echo     CORRECTION DU PROBLEME DES DAGS AIRFLOW
echo =====================================================
echo.

echo [INFO] Repertoire de travail: %CD%
echo.

echo [ETAPE 1/5] Suppression de l'ancienne ConfigMap problematique...
kubectl delete configmap airflow-dags -n airflow --ignore-not-found=true

if errorlevel 1 (
    echo [WARNING] Erreur suppression ConfigMap (peut-etre inexistante)
) else (
    echo [OK] Ancienne ConfigMap supprimee
)

echo.
echo [ETAPE 2/5] Application des nouveaux volumes corriges...
kubectl apply -f manifests/airflow-volumes-fixed.yaml

if errorlevel 1 (
    echo [ERROR] Erreur application des volumes corriges
    pause
    exit /b 1
)

echo [OK] Nouveaux volumes appliques

echo.
echo [ETAPE 3/5] Attente de l'initialisation des DAGs...
echo [INFO] Verification du job d'initialisation...

:: Attendre que le job soit complete (timeout 2 minutes)
kubectl wait --for=condition=complete job/airflow-dags-init -n airflow --timeout=120s

if errorlevel 1 (
    echo [WARNING] Timeout du job d'initialisation, verification manuelle...
    kubectl get job airflow-dags-init -n airflow
    echo [INFO] Logs du job:
    kubectl logs job/airflow-dags-init -n airflow
) else (
    echo [OK] Job d'initialisation termine avec succes
)

echo.
echo [ETAPE 4/5] Redemarrage des services Airflow...

echo   - Redemarrage du webserver...
kubectl rollout restart deployment/airflow-webserver -n airflow

echo   - Redemarrage du scheduler...
kubectl rollout restart deployment/airflow-scheduler -n airflow

if errorlevel 1 (
    echo [ERROR] Erreur redemarrage des services
    pause
    exit /b 1
)

echo [OK] Services redemarres

echo.
echo [ETAPE 5/5] Verification du statut des pods...

:: Attendre le redemarrage des pods
echo [INFO] Attente du redemarrage des pods (30s)...
timeout /t 30 /nobreak >nul

kubectl get pods -n airflow

echo.
echo =====================================================
echo      [SUCCESS] CORRECTION DES DAGS TERMINEE!
echo =====================================================
echo.
echo [INFO] Les DAGs devraient maintenant apparaitre dans l'interface
echo [INFO] Attendez 1-2 minutes puis actualisez la page web
echo.
echo [INFO] Interface Airflow: http://localhost:32194
echo [INFO] Username: admin / Password: admin123
echo.
echo [INFO] DAGs attendus:
echo   1. example_kubernetes_dag - DAG d'exemple
echo   2. employees_csv_ingestion_local - DAG tutoriel CSV
echo.
echo [INFO] Si les DAGs n'apparaissent toujours pas, verifiez:
echo   scripts\logs-clean.bat scheduler
echo.
pause