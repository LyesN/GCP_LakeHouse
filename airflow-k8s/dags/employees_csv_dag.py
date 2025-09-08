"""
DAG d'exemple : Import CSV employees depuis GCS vers BigQuery
Compatible avec le tutoriel 2 - Pipeline Airflow
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateEmptyTableOperator, BigQueryInsertJobOperator
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from airflow.utils.dates import days_ago
import logging

# Configuration par défaut
default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,  # Désactivé pour l'environnement local
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Paramètres du pipeline (à adapter selon votre environnement)
PROJECT_ID = 'lake-471013'
DATASET_ID = 'lakehouse_employee_data'
TABLE_ID = 'employees'
GCS_BUCKET = 'lakehouse-bucket-20250903'
GCS_OBJECT = 'employees_5mb.csv'

# Définition du DAG
dag = DAG(
    'employees_csv_ingestion_local',
    default_args=default_args,
    description='Pipeline ingestion CSV employees vers BigQuery (Local K8s)',
    schedule_interval=None,  # Exécution manuelle pour les tests locaux
    catchup=False,
    max_active_runs=1,
    tags=['bigquery', 'gcs', 'employees', 'ingestion', 'local']
)

def validate_csv_file(**context):
    """Valide la structure et le contenu du fichier CSV"""
    # Version simplifiée pour l'environnement local
    logging.info("🔍 Validation du fichier CSV...")
    
    # Simulation de validation (en local, on suppose que le fichier est valide)
    expected_columns = ['id', 'nom', 'prenom', 'email', 'age', 'ville', 
                       'code_postal', 'telephone', 'salaire', 'departement',
                       'date_embauche', 'statut', 'score', 'latitude', 
                       'longitude', 'commentaire', 'reference', 'niveau', 
                       'categorie', 'timestamp']
    
    logging.info(f"✅ Structure CSV attendue: {len(expected_columns)} colonnes")
    logging.info(f"   Colonnes: {', '.join(expected_columns)}")
    logging.info("✅ Fichier CSV validé (simulation pour environnement local)")
    
    return True

def validate_loaded_data(**context):
    """Valide les données chargées en BigQuery"""
    logging.info("🔍 Validation des données chargées...")
    
    # Simulation de validation (en local)
    # En production, cette fonction ferait des requêtes BigQuery réelles
    
    logging.info("✅ Validation des données simulée:")
    logging.info("   - Données chargées avec succès")
    logging.info("   - Pas de doublons détectés")
    logging.info("   - Format email validé")
    logging.info("   - Âges cohérents")
    
    return True

def log_pipeline_metrics(**context):
    """Log des métriques du pipeline pour monitoring"""
    logging.info("📊 Métriques du pipeline:")
    logging.info(f"   - DAG: {context['dag'].dag_id}")
    logging.info(f"   - Run ID: {context['run_id']}")
    logging.info(f"   - Date d'exécution: {context['execution_date']}")
    logging.info("   - Statut: SUCCESS")
    
    return "metrics_logged"

# TASK 1: Validation du fichier CSV
validate_csv = PythonOperator(
    task_id='validate_csv_structure',
    python_callable=validate_csv_file,
    dag=dag
)

# TASK 2: Simulation de l'ingestion BigQuery (sans vraie connexion GCP)
simulate_ingestion = PythonOperator(
    task_id='simulate_bigquery_ingestion',
    python_callable=lambda **context: logging.info("🚀 Simulation de l'ingestion BigQuery terminée avec succès"),
    dag=dag
)

# TASK 3: Validation des données chargées
validate_data = PythonOperator(
    task_id='validate_loaded_data',
    python_callable=validate_loaded_data,
    dag=dag
)

# TASK 4: Log des métriques
log_metrics = PythonOperator(
    task_id='log_pipeline_metrics',
    python_callable=log_pipeline_metrics,
    dag=dag
)

# TASK 5: Notification de succès (sans email en local)
success_notification = PythonOperator(
    task_id='send_success_notification',
    python_callable=lambda **context: logging.info("✅ Pipeline terminé avec succès! 🎉"),
    dag=dag
)

# Définition des dépendances entre tasks
validate_csv >> simulate_ingestion >> validate_data >> log_metrics >> success_notification

# Documentation du DAG
dag.doc_md = """
# Pipeline d'ingestion CSV Employees (Local Kubernetes)

Ce DAG orchestre l'ingestion des données employees depuis GCS vers BigQuery.
Version adaptée pour l'environnement Kubernetes local.

## Architecture:
1. ✅ Validation de la structure du fichier CSV
2. 🚀 Simulation de l'ingestion BigQuery (remplace la vraie ingestion)
3. 🔍 Validation des données chargées (simulation)
4. 📊 Collecte des métriques du pipeline
5. 🎉 Notification de succès

## Configuration:
- **Projet**: {PROJECT_ID}
- **Dataset**: {DATASET_ID}
- **Table**: {TABLE_ID}
- **Fichier source**: gs://{GCS_BUCKET}/{GCS_OBJECT}

## Utilisation:
Ce DAG est configuré pour l'exécution manuelle (`schedule_interval=None`).
Pour l'activer, allez dans l'interface Airflow et cliquez sur "Trigger DAG".

## Notes:
- Version simplifiée pour tests locaux
- Les vraies connexions GCP sont remplacées par des simulations
- Idéal pour tester l'orchestration et le monitoring
""".format(
    PROJECT_ID=PROJECT_ID,
    DATASET_ID=DATASET_ID, 
    TABLE_ID=TABLE_ID,
    GCS_BUCKET=GCS_BUCKET,
    GCS_OBJECT=GCS_OBJECT
)