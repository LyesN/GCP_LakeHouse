# Tutoriel 2 : Pipeline CSV vers BigQuery avec Airflow

## Prérequis
Ce tutoriel fait suite au **Tutoriel 1** où nous avons mis en place :
- Le bucket GCS avec le fichier `employees_5mb.csv`
- Le dataset BigQuery `lakehouse_employee_data`
- La table `employees` avec schéma défini

## Contexte
- **Public cible** : Data Engineers
- **Stack** : BigQuery + Apache Airflow
- **Objectif** : Orchestrer le pipeline d'ingestion avec Airflow

## Paramètres du projet
- **Projet GCP** : `lake-471013`
- **Dataset BigQuery** : `lakehouse_employee_data`
- **Bucket GCS** : `lakehouse-bucket-20250903`
- **Fichier CSV** : `employees_5mb.csv`

## Plan du tutoriel

1. **[Architecture du pipeline Airflow](#1-architecture-du-pipeline-airflow)**
2. **[Configuration des connexions GCP](#2-configuration-des-connexions-gcp)**
3. **[Création du DAG Airflow](#3-création-du-dag-airflow)**
4. **[Monitoring et alertes](#4-monitoring-et-alertes)**
5. **[Déploiement et bonnes pratiques](#5-déploiement-et-bonnes-pratiques)**

## 1. Architecture du pipeline Airflow

### 1.1 Vue d'ensemble du flux

```
[GCS Bucket] → [Airflow DAG] → [BigQuery Table] → [Validation] → [Notification]
     ↓              ↓              ↓               ↓           ↓
 employees.csv   Orchestration   employees      Tests      Email/Slack
```

### 1.2 Composants du DAG

- **Sensor GCS** : Détecte la présence du fichier CSV
- **Task de validation** : Vérifie l'intégrité du fichier
- **Task d'ingestion** : Charge les données dans BigQuery
- **Task de validation des données** : Contrôle qualité post-ingestion
- **Task de notification** : Alerte en cas de succès/échec

## 2. Configuration des connexions GCP

### 2.1 Connection BigQuery dans Airflow

1. **Accéder à l'interface Airflow**
2. **Admin** → **Connections** → **+ Add Connection**
3. **Configurer la connexion BigQuery** :
   ```
   Connection Id: bigquery_default
   Connection Type: Google BigQuery
   Project Id: lake-471013
   Keyfile Path: /path/to/service-account-key.json
   ```

### 2.2 Connection Google Cloud dans Airflow

```
Connection Id: gcp_default
Connection Type: Google Cloud
Project Id: lake-471013
Keyfile Path: /path/to/service-account-key.json
Scopes: https://www.googleapis.com/auth/cloud-platform
```

### 2.3 Service Account et permissions

Le Service Account doit avoir les rôles :
- `BigQuery Data Editor`
- `BigQuery Job User`
- `Storage Object Viewer`
- `Storage Object Creator` (pour les logs/temporaires)

## 3. Création du DAG Airflow

### 3.1 Structure du fichier DAG

Créer le fichier `employees_ingestion_dag.py` :

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateEmptyTableOperator, BigQueryInsertJobOperator
from airflow.providers.google.cloud.operators.gcs import GCSDeleteObjectsOperator
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from airflow.utils.dates import days_ago

# Configuration par défaut
default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email': ['admin@company.com']
}

# Paramètres du pipeline
PROJECT_ID = 'lake-471013'
DATASET_ID = 'lakehouse_employee_data'
TABLE_ID = 'employees'
GCS_BUCKET = 'lakehouse-bucket-20250903'
GCS_OBJECT = 'employees_5mb.csv'
```

### 3.2 Définition du DAG principal

```python
# Définition du DAG
dag = DAG(
    'employees_csv_ingestion',
    default_args=default_args,
    description='Pipeline ingestion CSV employees vers BigQuery',
    schedule_interval='0 2 * * *',  # Tous les jours à 2h
    catchup=False,
    max_active_runs=1,
    tags=['bigquery', 'gcs', 'employees', 'ingestion']
)
```

### 3.3 Tasks du pipeline

#### A. Sensor pour détecter le fichier

```python
# Task 1: Détecter la présence du fichier CSV dans GCS
detect_file = GCSObjectExistenceSensor(
    task_id='detect_csv_file',
    bucket=GCS_BUCKET,
    object=GCS_OBJECT,
    timeout=300,
    poke_interval=30,
    mode='poke',
    gcp_conn_id='gcp_default',
    dag=dag
)
```

#### B. Validation du fichier

```python
def validate_csv_file(**context):
    """Valide la structure et le contenu du fichier CSV"""
    from google.cloud import storage
    
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(GCS_BUCKET)
    blob = bucket.blob(GCS_OBJECT)
    
    # Télécharger et analyser les premières lignes
    content = blob.download_as_text(encoding='utf-8')
    lines = content.split('\n')
    
    # Vérifications
    if len(lines) < 2:
        raise ValueError("Fichier CSV vide ou pas d'en-tête")
    
    header = lines[0].split(';')
    expected_columns = ['id', 'nom', 'prenom', 'email', 'age', 'ville', 
                       'code_postal', 'telephone', 'salaire', 'departement',
                       'date_embauche', 'statut', 'score', 'latitude', 
                       'longitude', 'commentaire', 'reference', 'niveau', 
                       'categorie', 'timestamp']
    
    if header != expected_columns:
        raise ValueError(f"Structure CSV incorrecte. Attendu: {expected_columns}, Reçu: {header}")
    
    print(f"✅ Fichier CSV validé: {len(lines)-1} lignes de données")
    return True

validate_csv = PythonOperator(
    task_id='validate_csv_structure',
    python_callable=validate_csv_file,
    dag=dag
)
```

#### C. Ingestion BigQuery

```python
# Task 3: Vider la table avant ingestion (optionnel)
truncate_table = BigQueryInsertJobOperator(
    task_id='truncate_employees_table',
    configuration={
        "query": {
            "query": f"DELETE FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}` WHERE TRUE",
            "useLegacySql": False,
        }
    },
    gcp_conn_id='bigquery_default',
    dag=dag
)

# Task 4: Ingestion des données depuis GCS
load_csv_to_bq = BigQueryInsertJobOperator(
    task_id='load_csv_to_bigquery',
    configuration={
        "query": {
            "query": f"""
            LOAD DATA INTO `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
            (id INT64, nom STRING, prenom STRING, email STRING, age INT64, ville STRING,
             code_postal STRING, telephone STRING, salaire FLOAT64, departement STRING,
             date_embauche DATE, statut STRING, score FLOAT64, latitude FLOAT64,
             longitude FLOAT64, commentaire STRING, reference STRING, niveau STRING,
             categorie STRING, timestamp TIMESTAMP)
            FROM FILES (
              format = 'CSV',
              field_delimiter = ';',
              skip_leading_rows = 1,
              uris = ['gs://{GCS_BUCKET}/{GCS_OBJECT}']
            )
            """,
            "useLegacySql": False,
        }
    },
    gcp_conn_id='bigquery_default',
    dag=dag
)
```

#### D. Validation des données chargées

```python
def validate_loaded_data(**context):
    """Valide les données chargées en BigQuery"""
    from google.cloud import bigquery
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Requête de validation
    query = f"""
    SELECT 
      COUNT(*) as total_rows,
      COUNT(DISTINCT id) as unique_ids,
      COUNT(CASE WHEN email LIKE '%@%' THEN 1 END) as valid_emails,
      AVG(age) as avg_age,
      MAX(ingestion_date) as last_ingestion
    FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
    """
    
    results = list(client.query(query))
    row = results[0]
    
    # Validations métier
    if row.total_rows == 0:
        raise ValueError("Aucune donnée chargée")
    
    if row.total_rows != row.unique_ids:
        raise ValueError(f"Doublons détectés: {row.total_rows} lignes, {row.unique_ids} IDs uniques")
    
    if row.valid_emails < row.total_rows * 0.9:  # 90% d'emails valides minimum
        raise ValueError(f"Trop d'emails invalides: {row.valid_emails}/{row.total_rows}")
    
    print(f"✅ Validation réussie:")
    print(f"   - {row.total_rows} lignes chargées")
    print(f"   - {row.unique_ids} IDs uniques")
    print(f"   - {row.valid_emails} emails valides")
    print(f"   - Âge moyen: {row.avg_age:.1f} ans")
    print(f"   - Dernière ingestion: {row.last_ingestion}")
    
    return row.total_rows

validate_data = PythonOperator(
    task_id='validate_loaded_data',
    python_callable=validate_loaded_data,
    dag=dag
)
```

#### E. Archivage du fichier traité

```python
# Task 5: Déplacer le fichier vers un dossier d'archive
archive_processed_file = BigQueryInsertJobOperator(
    task_id='archive_processed_file',
    configuration={
        "query": {
            "query": f"""
            EXPORT DATA
            OPTIONS (
              uri = 'gs://{GCS_BUCKET}/processed/employees_{{{{ ds }}}}.csv',
              format = 'CSV',
              header = true
            )
            AS (
              SELECT * EXCEPT(ingestion_date, source_file)
              FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
              WHERE DATE(ingestion_date) = CURRENT_DATE()
            )
            """,
            "useLegacySql": False,
        }
    },
    gcp_conn_id='bigquery_default',
    dag=dag
)
```

### 3.4 Définition des dépendances

```python
# Définition des dépendances entre tasks
detect_file >> validate_csv >> truncate_table >> load_csv_to_bq >> validate_data >> archive_processed_file

# Task de notification en cas de succès
success_notification = EmailOperator(
    task_id='send_success_email',
    to=['data-team@company.com'],
    subject='✅ Pipeline employees CSV - Succès',
    html_content="""
    <h3>Pipeline d'ingestion employees réussi</h3>
    <p>Le fichier CSV a été traité avec succès.</p>
    <p>Timestamp: {{ ts }}</p>
    <p>Run ID: {{ run_id }}</p>
    """,
    dag=dag
)

validate_data >> success_notification
```

## 4. Monitoring et alertes

### 4.1 Configuration des alertes email

```python
# Configuration des alertes en cas d'échec
def send_failure_alert(context):
    """Envoi d'une alerte détaillée en cas d'échec"""
    
    subject = f"❌ Échec pipeline employees - {context['task_instance'].task_id}"
    
    html_content = f"""
    <h3>Échec du pipeline d'ingestion employees</h3>
    <ul>
        <li><strong>DAG:</strong> {context['dag'].dag_id}</li>
        <li><strong>Task:</strong> {context['task_instance'].task_id}</li>
        <li><strong>Date d'exécution:</strong> {context['execution_date']}</li>
        <li><strong>Log URL:</strong> {context['task_instance'].log_url}</li>
        <li><strong>Erreur:</strong> {context.get('exception', 'Non spécifiée')}</li>
    </ul>
    """
    
    EmailOperator(
        task_id='failure_alert',
        to=['admin@company.com', 'data-team@company.com'],
        subject=subject,
        html_content=html_content
    ).execute(context)

# Application de l'alerte à toutes les tasks
for task in dag.tasks:
    task.on_failure_callback = send_failure_alert
```

### 4.2 Métriques et monitoring

```python
def log_pipeline_metrics(**context):
    """Log des métriques du pipeline pour monitoring"""
    from google.cloud import bigquery
    from google.cloud import monitoring_v3
    
    # Récupérer les stats d'exécution
    client = bigquery.Client(project=PROJECT_ID)
    
    query = f"""
    SELECT 
      COUNT(*) as rows_processed,
      MAX(ingestion_date) as execution_time,
      COUNT(DISTINCT departement) as departments_count
    FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
    WHERE DATE(ingestion_date) = CURRENT_DATE()
    """
    
    results = list(client.query(query))
    metrics = results[0]
    
    # Log des métriques (à adapter selon votre système de monitoring)
    print(f"METRIC: rows_processed={metrics.rows_processed}")
    print(f"METRIC: departments_count={metrics.departments_count}")
    print(f"METRIC: execution_time={metrics.execution_time}")
    
    return metrics

log_metrics = PythonOperator(
    task_id='log_pipeline_metrics',
    python_callable=log_pipeline_metrics,
    dag=dag
)

# Ajouter aux dépendances
validate_data >> log_metrics >> success_notification
```

## 5. Déploiement et bonnes pratiques

### 5.1 Variables d'environnement

Utiliser les Variables Airflow pour la configuration :

```python
from airflow.models import Variable

# Récupération des variables
PROJECT_ID = Variable.get("gcp_project_id", default_var="lake-471013")
DATASET_ID = Variable.get("bq_dataset", default_var="lakehouse_employee_data")
GCS_BUCKET = Variable.get("gcs_bucket", default_var="lakehouse-bucket-20250903")
```

### 5.2 Gestion des erreurs et retry

```python
# Configuration avancée des retries
default_args = {
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'retry_exponential_backoff': True,
    'max_retry_delay': timedelta(minutes=30),
}
```

### 5.3 Tests unitaires

```python
# Exemple de test pour le DAG
def test_dag_loading():
    """Test de chargement du DAG"""
    from airflow.models import DagBag
    
    dagbag = DagBag()
    dag = dagbag.get_dag(dag_id='employees_csv_ingestion')
    
    assert dag is not None
    assert len(dag.tasks) == 7  # Nombre de tasks attendu
    assert 'detect_csv_file' in dag.task_ids
```

### 5.4 Documentation et maintenance

```python
# Documentation du DAG
dag.doc_md = """
## Pipeline d'ingestion CSV Employees

Ce DAG orchestre l'ingestion quotidienne des données employees depuis GCS vers BigQuery.

### Architecture:
1. Détection du fichier CSV dans GCS
2. Validation de la structure
3. Ingestion dans BigQuery
4. Contrôle qualité des données
5. Archivage et notification

### Monitoring:
- Alertes email en cas d'échec
- Métriques logged pour monitoring
- Validation qualité des données

### Maintenance:
- Exécution quotidienne à 2h du matin
- Retry automatique en cas d'échec temporaire
- Logs détaillés pour debugging
"""
```

## 6. Déploiement sur Cloud Composer (Airflow géré GCP)

### 6.1 Création de l'environnement Composer

```bash
# Créer un environnement Cloud Composer
gcloud composer environments create employees-pipeline-env \
    --location=us-east1 \
    --python-version=3 \
    --machine-type=n1-standard-1 \
    --disk-size=30GB \
    --node-count=3
```

### 6.2 Déploiement du DAG

```bash
# Uploader le DAG vers l'environnement Composer
gcloud composer environments storage dags import \
    --environment=employees-pipeline-env \
    --location=us-east1 \
    --source=employees_ingestion_dag.py
```

### 6.3 Configuration des variables

```bash
# Configurer les variables via gcloud
gcloud composer environments run employees-pipeline-env \
    --location=us-east1 \
    variables set -- \
    gcp_project_id lake-471013

gcloud composer environments run employees-pipeline-env \
    --location=us-east1 \
    variables set -- \
    bq_dataset lakehouse_employee_data
```

## Prochaines étapes

- **Monitoring avancé** : Intégration avec Google Cloud Monitoring
- **Pipeline parallèle** : Traitement de plusieurs fichiers CSV
- **Data Lineage** : Suivi de la provenance des données
- **Alertes Slack** : Notifications dans Slack plutôt qu'email

Ce pipeline Airflow offre une orchestration robuste et scalable pour l'ingestion de données CSV vers BigQuery avec monitoring complet et gestion d'erreurs.