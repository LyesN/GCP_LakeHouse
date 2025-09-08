@echo off
chcp 65001 >nul

REM Se placer dans le répertoire du script
cd /d "%~dp0\.."

echo =====================================================
echo        AJOUTER UN DAG AIRFLOW
echo =====================================================

if "%1"=="" (
    echo Usage: add-dag-clean.bat [chemin_vers_fichier_dag.py]
    echo.
    echo Exemple: add-dag-clean.bat C:\mes_dags\mon_nouveau_dag.py
    echo.
    pause
    exit /b 1
)

set DAG_FILE=%1

if not exist "%DAG_FILE%" (
    echo [ERROR] Fichier DAG non trouve: %DAG_FILE%
    pause
    exit /b 1
)

echo [INFO] Fichier DAG: %DAG_FILE%

REM Extraire le nom du fichier
for %%f in ("%DAG_FILE%") do set DAG_NAME=%%~nxf

echo [INFO] Nom du DAG: %DAG_NAME%

REM Copier le fichier dans le dossier dags local
if not exist "dags" mkdir dags
copy "%DAG_FILE%" "dags\%DAG_NAME%"

if errorlevel 1 (
    echo [ERROR] Erreur copie du fichier DAG
    pause
    exit /b 1
)

echo [OK] Fichier copie dans dags\%DAG_NAME%

REM Copier le DAG dans le PVC via un pod temporaire
echo [INFO] Ajout du DAG dans le volume persistent...

REM Creer un pod temporaire pour copier le fichier
kubectl run dag-copy-temp --image=busybox:1.35 -n airflow --restart=Never --rm -i --tty -- /bin/sh -c "
echo 'Creation du repertoire de destination...'
mkdir -p /opt/airflow/dags
echo 'Copie du fichier DAG...'
" --overrides='
{
  "spec": {
    "containers": [
      {
        "name": "dag-copy-temp",
        "image": "busybox:1.35",
        "command": ["/bin/sh", "-c", "sleep 30"],
        "volumeMounts": [
          {
            "name": "dags-volume",
            "mountPath": "/opt/airflow/dags"
          }
        ]
      }
    ],
    "volumes": [
      {
        "name": "dags-volume",
        "persistentVolumeClaim": {
          "claimName": "airflow-dags-pvc"
        }
      }
    ]
  }
}' 2>nul

if errorlevel 1 (
    echo [WARNING] Methode directe echouee, utilisation de kubectl cp...
    
    REM Methode alternative: copier via kubectl cp
    kubectl create -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: dag-copy-helper
  namespace: airflow
spec:
  containers:
  - name: helper
    image: busybox:1.35
    command: ["/bin/sleep", "300"]
    volumeMounts:
    - name: dags-volume
      mountPath: /opt/airflow/dags
  volumes:
  - name: dags-volume
    persistentVolumeClaim:
      claimName: airflow-dags-pvc
  restartPolicy: Never
EOF

    echo [INFO] Attente du demarrage du pod helper...
    kubectl wait --for=condition=ready pod/dag-copy-helper -n airflow --timeout=60s
    
    kubectl cp "dags\%DAG_NAME%" airflow/dag-copy-helper:/opt/airflow/dags/%DAG_NAME%
    
    kubectl delete pod dag-copy-helper -n airflow
)

echo [OK] DAG ajoute au volume persistent

REM Redemarrer les services pour prendre en compte le nouveau DAG
echo [INFO] Redemarrage des services Airflow...
kubectl rollout restart deployment/airflow-webserver -n airflow
kubectl rollout restart deployment/airflow-scheduler -n airflow

echo [OK] Services redemarres

echo.
echo =====================================================
echo           [SUCCESS] DAG AJOUTE AVEC SUCCES!
echo =====================================================
echo.
echo [INFO] DAG ajoute: %DAG_NAME%
echo [INFO] Emplacement local: dags\%DAG_NAME%
echo [INFO] Services redemarres pour prendre en compte le nouveau DAG
echo.
echo [INFO] Le DAG devrait apparaitre dans l'interface Web dans 1-2 minutes
echo [INFO] Interface Web: http://localhost:32794
echo.
pause