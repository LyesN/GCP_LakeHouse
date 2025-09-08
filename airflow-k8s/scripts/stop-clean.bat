@echo off
chcp 65001 >nul

REM Se placer dans le répertoire du script
cd /d "%~dp0\.."

echo =====================================================
echo      ARRET AIRFLOW SUR KUBERNETES (Windows)
echo =====================================================
echo.

echo [ETAPE 1/3] Arret des services Airflow...
kubectl delete -f manifests/airflow-webserver.yaml --ignore-not-found=true
kubectl delete -f manifests/airflow-scheduler.yaml --ignore-not-found=true
kubectl delete -f manifests/airflow-worker.yaml --ignore-not-found=true
kubectl delete -f manifests/airflow-flower.yaml --ignore-not-found=true

echo [OK] Services Airflow arretes

echo.
echo [ETAPE 2/3] Arret des bases de donnees...
kubectl delete -f manifests/postgresql.yaml --ignore-not-found=true
kubectl delete -f manifests/redis.yaml --ignore-not-found=true

echo [OK] Bases de donnees arretees

echo.
echo [ETAPE 3/3] Nettoyage des configurations...
kubectl delete -f manifests/airflow-configmap.yaml --ignore-not-found=true
kubectl delete -f manifests/airflow-volumes.yaml --ignore-not-found=true

echo [OK] Configurations supprimees

echo.
echo [WARNING] ATTENTION: Le namespace 'airflow' et les PVC sont conserves
echo    Pour les supprimer completement:
echo.
echo    kubectl delete namespace airflow
echo.
echo [SUCCESS] Arret termine!
pause