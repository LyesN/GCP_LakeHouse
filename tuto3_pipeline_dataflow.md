# Tutoriel 3 : Pipeline CSV vers BigQuery avec Dataflow

## Prérequis
Ce tutoriel fait suite au **Tutoriel 1** où nous avons mis en place :
- Le bucket GCS avec le fichier `employees_5mb.csv`
- Le dataset BigQuery `lakehouse_employee_data`
- La table `employees` avec schéma défini

## Contexte
- **Public cible** : Data Engineers
- **Stack** : BigQuery + Apache Beam / Dataflow
- **Objectif** : Traitement distribué et scalable des données CSV

## Paramètres du projet
- **Projet GCP** : `lake-471013`
- **Dataset BigQuery** : `lakehouse_employee_data`
- **Bucket GCS** : `lakehouse-bucket-20250903`
- **Fichier CSV** : `employees_5mb.csv`
- **Région Dataflow** : `us-east1`

## Plan du tutoriel

1. **[Architecture du pipeline Dataflow](#1-architecture-du-pipeline-dataflow)**
2. **[Développement avec Apache Beam](#2-développement-avec-apache-beam)**
3. **[Transformations des données](#3-transformations-des-données)**
4. **[Déploiement sur Dataflow](#4-déploiement-sur-dataflow)**
5. **[Monitoring et optimisations](#5-monitoring-et-optimisations)**

## 1. Architecture du pipeline Dataflow

### 1.1 Vue d'ensemble du flux

```
[GCS CSV] → [Dataflow Pipeline] → [Transformations] → [BigQuery] → [Validation]
     ↓              ↓                    ↓              ↓           ↓
 Source Data    Beam Pipeline      Clean & Enrich     Sink        QA Checks
```

### 1.2 Avantages de Dataflow vs BigQuery LOAD

- **Scalabilité automatique** : Traitement distribué de gros volumes
- **Transformations complexes** : Logique métier avancée pendant l'ingestion  
- **Résilience** : Gestion automatique des erreurs et retry
- **Flexibilité** : Support multi-sources et multi-sinks
- **Stream + Batch** : Même code pour données temps réel et batch

## 2. Développement avec Apache Beam

### 2.1 Configuration de l'environnement

#### A. Installation des dépendances Python

```bash
# Créer un environnement virtuel
python -m venv dataflow-env
source dataflow-env/bin/activate  # Linux/Mac
# ou
dataflow-env\Scripts\activate  # Windows

# Installation Apache Beam avec extras GCP
pip install apache-beam[gcp]==2.52.0
pip install google-cloud-bigquery
pip install pandas
```

#### B. Configuration du projet

```bash
# Structure du projet
mkdir employees-dataflow-pipeline
cd employees-dataflow-pipeline

# Structure des dossiers
mkdir src
mkdir src/transforms
mkdir src/utils
mkdir tests
mkdir configs
```

### 2.2 Pipeline principal Apache Beam

Créer le fichier `src/employees_pipeline.py` :

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, GoogleCloudOptions, StandardOptions, WorkerOptions
from apache_beam.io import ReadFromText, WriteToBigQuery
from apache_beam.io.gcp.bigquery import BigQueryDisposition
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, List
import re

# Configuration des logs
logging.basicConfig(level=logging.INFO)

class EmployeeTransforms:
    """Transformations pour les données employees"""
    
    @staticmethod
    def parse_csv_line(line: str) -> Dict[str, Any]:
        """Parse une ligne CSV et retourne un dictionnaire"""
        if not line or line.startswith('id;'):  # Skip header
            return None
            
        fields = line.split(';')
        if len(fields) != 20:  # Vérifier le nombre de colonnes
            logging.error(f"Ligne invalide (nombre de colonnes): {line}")
            return None
            
        try:
            record = {
                'id': int(fields[0]) if fields[0] else None,
                'nom': fields[1].strip() if fields[1] else None,
                'prenom': fields[2].strip() if fields[2] else None,
                'email': fields[3].strip().lower() if fields[3] else None,
                'age': int(fields[4]) if fields[4] and fields[4].isdigit() else None,
                'ville': fields[5].strip() if fields[5] else None,
                'code_postal': fields[6].strip() if fields[6] else None,
                'telephone': fields[7].strip() if fields[7] else None,
                'salaire': float(fields[8]) if fields[8] else None,
                'departement': fields[9].strip().upper() if fields[9] else None,
                'date_embauche': fields[10] if fields[10] else None,
                'statut': fields[11].strip().upper() if fields[11] else None,
                'score': float(fields[12]) if fields[12] else None,
                'latitude': float(fields[13]) if fields[13] else None,
                'longitude': float(fields[14]) if fields[14] else None,
                'commentaire': fields[15].strip() if fields[15] else None,
                'reference': fields[16].strip() if fields[16] else None,
                'niveau': fields[17].strip() if fields[17] else None,
                'categorie': fields[18].strip() if fields[18] else None,
                'timestamp': fields[19].strip() if fields[19] else None,
            }
            return record
            
        except (ValueError, IndexError) as e:
            logging.error(f"Erreur parsing ligne: {line}, erreur: {e}")
            return None
    
    @staticmethod
    def validate_record(record: Dict[str, Any]) -> Dict[str, Any]:
        """Valide et enrichit un enregistrement"""
        if not record:
            return None
            
        # Validation des champs obligatoires
        if not record.get('id') or not record.get('nom') or not record.get('prenom'):
            logging.warning(f"Enregistrement manque champs obligatoires: {record.get('id', 'NO_ID')}")
            return None
            
        # Validation de l'email
        email = record.get('email', '')
        email_valid = bool(re.match(r'^[^@]+@[^@]+\.[^@]+$', email)) if email else False
        
        # Validation de l'âge
        age = record.get('age')
        if age and (age < 16 or age > 70):
            logging.warning(f"Âge suspect pour ID {record['id']}: {age}")
            record['age'] = None
            
        # Validation du salaire
        salaire = record.get('salaire')
        if salaire and salaire <= 0:
            record['salaire'] = None
            
        # Validation des coordonnées GPS
        latitude = record.get('latitude')
        longitude = record.get('longitude')
        if latitude and (latitude < -90 or latitude > 90):
            record['latitude'] = None
        if longitude and (longitude < -180 or longitude > 180):
            record['longitude'] = None
            
        # Normalisation du téléphone
        telephone = record.get('telephone', '')
        if telephone:
            record['telephone'] = re.sub(r'[^\d+]', '', telephone)
            
        # Enrichissement avec métadonnées
        record['ingestion_date'] = datetime.utcnow().isoformat()
        record['source_file'] = 'gs://lakehouse-bucket-20250903/employees_5mb.csv'
        record['email_valid'] = email_valid
        record['has_missing_data'] = any(v is None for k, v in record.items() 
                                       if k in ['age', 'salaire', 'email'])
        
        return record
    
    @staticmethod
    def enrich_with_business_logic(record: Dict[str, Any]) -> Dict[str, Any]:
        """Enrichissement avec logique métier"""
        if not record:
            return None
            
        # Calcul du niveau de séniorité
        date_embauche = record.get('date_embauche')
        if date_embauche:
            try:
                embauche = datetime.strptime(date_embauche, '%Y-%m-%d')
                years_service = (datetime.now() - embauche).days / 365.25
                
                if years_service >= 10:
                    seniority = 'EXPERT'
                elif years_service >= 5:
                    seniority = 'SENIOR'
                elif years_service >= 2:
                    seniority = 'CONFIRME'
                else:
                    seniority = 'JUNIOR'
                    
                record['seniority_level'] = seniority
                record['years_of_service'] = round(years_service, 2)
            except ValueError:
                logging.warning(f"Date embauche invalide pour ID {record['id']}: {date_embauche}")
                record['seniority_level'] = 'UNKNOWN'
                record['years_of_service'] = None
        
        # Classification salariale
        salaire = record.get('salaire')
        if salaire:
            if salaire >= 80000:
                salary_band = 'HIGH'
            elif salaire >= 50000:
                salary_band = 'MEDIUM'
            else:
                salary_band = 'LOW'
            record['salary_band'] = salary_band
        
        return record

class DataQualityMetrics(beam.DoFn):
    """Collecte de métriques de qualité des données"""
    
    def __init__(self):
        self.total_records = beam.metrics.Metrics.counter('pipeline', 'total_records')
        self.valid_records = beam.metrics.Metrics.counter('pipeline', 'valid_records')
        self.invalid_records = beam.metrics.Metrics.counter('pipeline', 'invalid_records')
        self.missing_email = beam.metrics.Metrics.counter('quality', 'missing_email')
        self.invalid_age = beam.metrics.Metrics.counter('quality', 'invalid_age')
        
    def process(self, element):
        self.total_records.inc()
        
        if element:
            self.valid_records.inc()
            
            # Métriques de qualité
            if not element.get('email') or not element.get('email_valid'):
                self.missing_email.inc()
                
            if not element.get('age'):
                self.invalid_age.inc()
                
            yield element
        else:
            self.invalid_records.inc()

def run_pipeline(argv=None):
    """Pipeline principal"""
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_path', required=True,
                       help='Chemin du fichier CSV dans GCS')
    parser.add_argument('--output_table', required=True,
                       help='Table BigQuery de sortie (projet:dataset.table)')
    parser.add_argument('--project', required=True,
                       help='Projet GCP')
    parser.add_argument('--region', default='us-east1',
                       help='Région Dataflow')
    parser.add_argument('--temp_location', required=True,
                       help='Emplacement temporaire GCS')
    parser.add_argument('--staging_location', required=True,
                       help='Emplacement staging GCS')
    
    known_args, pipeline_args = parser.parse_known_args(argv)
    
    # Configuration des options Dataflow
    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(GoogleCloudOptions).project = known_args.project
    pipeline_options.view_as(GoogleCloudOptions).region = known_args.region
    pipeline_options.view_as(GoogleCloudOptions).temp_location = known_args.temp_location
    pipeline_options.view_as(GoogleCloudOptions).staging_location = known_args.staging_location
    pipeline_options.view_as(StandardOptions).runner = 'DataflowRunner'
    pipeline_options.view_as(WorkerOptions).machine_type = 'n1-standard-2'
    pipeline_options.view_as(WorkerOptions).max_num_workers = 10
    pipeline_options.view_as(WorkerOptions).autoscaling_algorithm = 'THROUGHPUT_BASED'
    
    # Schéma BigQuery
    bigquery_schema = {
        'fields': [
            {'name': 'id', 'type': 'INTEGER', 'mode': 'REQUIRED'},
            {'name': 'nom', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'prenom', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'email', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'age', 'type': 'INTEGER', 'mode': 'NULLABLE'},
            {'name': 'ville', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'code_postal', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'telephone', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'salaire', 'type': 'FLOAT', 'mode': 'NULLABLE'},
            {'name': 'departement', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'date_embauche', 'type': 'DATE', 'mode': 'NULLABLE'},
            {'name': 'statut', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'score', 'type': 'FLOAT', 'mode': 'NULLABLE'},
            {'name': 'latitude', 'type': 'FLOAT', 'mode': 'NULLABLE'},
            {'name': 'longitude', 'type': 'FLOAT', 'mode': 'NULLABLE'},
            {'name': 'commentaire', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'reference', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'niveau', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'categorie', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'timestamp', 'type': 'TIMESTAMP', 'mode': 'NULLABLE'},
            {'name': 'ingestion_date', 'type': 'TIMESTAMP', 'mode': 'NULLABLE'},
            {'name': 'source_file', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'email_valid', 'type': 'BOOLEAN', 'mode': 'NULLABLE'},
            {'name': 'has_missing_data', 'type': 'BOOLEAN', 'mode': 'NULLABLE'},
            {'name': 'seniority_level', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'years_of_service', 'type': 'FLOAT', 'mode': 'NULLABLE'},
            {'name': 'salary_band', 'type': 'STRING', 'mode': 'NULLABLE'},
        ]
    }
    
    # Pipeline principal
    with beam.Pipeline(options=pipeline_options) as pipeline:
        
        employees = (
            pipeline
            | 'Lire fichier CSV' >> ReadFromText(known_args.input_path)
            | 'Parser CSV' >> beam.Map(EmployeeTransforms.parse_csv_line)
            | 'Filtrer lignes nulles' >> beam.Filter(lambda x: x is not None)
            | 'Valider données' >> beam.Map(EmployeeTransforms.validate_record)
            | 'Filtrer enregistrements invalides' >> beam.Filter(lambda x: x is not None)
            | 'Enrichir données' >> beam.Map(EmployeeTransforms.enrich_with_business_logic)
            | 'Collecte métriques' >> beam.ParDo(DataQualityMetrics())
            | 'Écrire vers BigQuery' >> WriteToBigQuery(
                table=known_args.output_table,
                schema=bigquery_schema,
                write_disposition=BigQueryDisposition.WRITE_TRUNCATE,  # Remplace la table
                create_disposition=BigQueryDisposition.CREATE_IF_NEEDED
            )
        )

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run_pipeline()
```

## 3. Transformations des données

### 3.1 Pipeline de validation avancée

Créer le fichier `src/transforms/data_validation.py` :

```python
import apache_beam as beam
from apache_beam.transforms.combiners import Count
import logging

class AdvancedDataValidation:
    """Validations avancées des données"""
    
    @staticmethod
    def detect_outliers(records, field_name, threshold_std=2):
        """Détecte les valeurs aberrantes basées sur l'écart-type"""
        
        class ComputeStats(beam.CombineFn):
            def create_accumulator(self):
                return []
            
            def add_input(self, accumulator, input):
                value = input.get(field_name)
                if value is not None:
                    accumulator.append(value)
                return accumulator
            
            def merge_accumulators(self, accumulators):
                merged = []
                for acc in accumulators:
                    merged.extend(acc)
                return merged
            
            def extract_output(self, accumulator):
                if not accumulator:
                    return {'mean': 0, 'std': 0, 'count': 0}
                    
                mean = sum(accumulator) / len(accumulator)
                variance = sum((x - mean) ** 2 for x in accumulator) / len(accumulator)
                std = variance ** 0.5
                
                return {
                    'mean': mean,
                    'std': std,
                    'count': len(accumulator),
                    'min': min(accumulator),
                    'max': max(accumulator)
                }
        
        # Calculer les statistiques
        stats = records | f'Compute {field_name} stats' >> beam.CombineGlobally(ComputeStats())
        
        # Identifier les outliers
        def flag_outliers(record, stats_side_input):
            stats = stats_side_input[0]  # stats est un singleton
            value = record.get(field_name)
            
            if value is not None and stats['std'] > 0:
                z_score = abs((value - stats['mean']) / stats['std'])
                if z_score > threshold_std:
                    record[f'{field_name}_outlier'] = True
                    record[f'{field_name}_z_score'] = z_score
                    logging.warning(f"Outlier détecté pour {field_name}: {value} (z-score: {z_score:.2f})")
                else:
                    record[f'{field_name}_outlier'] = False
                    record[f'{field_name}_z_score'] = z_score
            
            return record
        
        return (records 
               | f'Flag {field_name} outliers' >> beam.Map(flag_outliers, beam.pvalue.AsSingleton(stats)))

class DataProfiling(beam.DoFn):
    """Profileur de données pour analyses"""
    
    def __init__(self):
        # Counters pour différentes métriques
        self.null_counts = {}
        self.data_types = {}
        
    def process(self, element):
        if not element:
            return
            
        for field_name, value in element.items():
            # Counter pour les valeurs nulles
            if field_name not in self.null_counts:
                self.null_counts[field_name] = beam.metrics.Metrics.counter('profile', f'null_{field_name}')
                
            if value is None or value == '':
                self.null_counts[field_name].inc()
        
        yield element
```

### 3.2 Transformations métier avancées

Créer le fichier `src/transforms/business_logic.py` :

```python
import apache_beam as beam
from datetime import datetime, timedelta
import logging

class BusinessEnrichment:
    """Enrichissement avec logique métier avancée"""
    
    @staticmethod
    def calculate_performance_score(records):
        """Calcule un score de performance basé sur plusieurs critères"""
        
        def enrich_performance(record):
            if not record:
                return record
                
            score_components = []
            
            # Score basé sur l'ancienneté
            years_service = record.get('years_of_service', 0)
            if years_service:
                seniority_score = min(years_service * 10, 50)  # Max 50 points
                score_components.append(seniority_score)
            
            # Score basé sur le salaire dans le département
            # (Nécessiterait un side input avec stats par département)
            salaire = record.get('salaire')
            if salaire:
                # Score simple basé sur le salaire (à améliorer avec percentiles)
                salary_score = min(salaire / 1000, 50)  # Max 50 points
                score_components.append(salary_score)
            
            # Score de complétude des données
            total_fields = 20  # Nombre total de champs attendus
            completed_fields = sum(1 for v in record.values() if v is not None and v != '')
            completeness_score = (completed_fields / total_fields) * 20  # Max 20 points
            score_components.append(completeness_score)
            
            # Score final
            if score_components:
                record['performance_score'] = sum(score_components)
                record['performance_tier'] = (
                    'ELITE' if record['performance_score'] >= 90 else
                    'HIGH' if record['performance_score'] >= 70 else
                    'MEDIUM' if record['performance_score'] >= 50 else
                    'LOW'
                )
            
            return record
        
        return records | 'Enrich performance scores' >> beam.Map(enrich_performance)
    
    @staticmethod
    def segment_employees(records):
        """Segmentation des employés pour analyses ciblées"""
        
        def create_segments(record):
            if not record:
                return record
                
            segments = []
            
            # Segmentation par âge
            age = record.get('age')
            if age:
                if age < 30:
                    segments.append('YOUNG_TALENT')
                elif age < 45:
                    segments.append('MID_CAREER')
                else:
                    segments.append('SENIOR_WORKFORCE')
            
            # Segmentation par niveau de salaire
            salaire = record.get('salaire')
            if salaire:
                if salaire > 75000:
                    segments.append('HIGH_EARNER')
                elif salaire < 35000:
                    segments.append('ENTRY_LEVEL')
            
            # Segmentation par risque de turnover
            years_service = record.get('years_of_service', 0)
            if 1 <= years_service <= 3:  # Période critique de turnover
                segments.append('TURNOVER_RISK')
            elif years_service > 10:
                segments.append('LOYAL_EMPLOYEE')
            
            # Segmentation par qualité des données
            if record.get('has_missing_data', False):
                segments.append('INCOMPLETE_PROFILE')
            
            record['employee_segments'] = segments
            record['segment_count'] = len(segments)
            
            return record
        
        return records | 'Create employee segments' >> beam.Map(create_segments)

class GeospatialEnrichment:
    """Enrichissement géospatial"""
    
    @staticmethod
    def calculate_distance_to_hq(records, hq_lat=40.7128, hq_lon=-74.0060):
        """Calcule la distance jusqu'au siège social"""
        
        def calculate_distance(record):
            import math
            
            if not record:
                return record
                
            lat = record.get('latitude')
            lon = record.get('longitude')
            
            if lat is not None and lon is not None:
                # Formule haversine pour calculer la distance
                R = 6371  # Rayon de la Terre en km
                
                lat1, lon1 = math.radians(lat), math.radians(lon)
                lat2, lon2 = math.radians(hq_lat), math.radians(hq_lon)
                
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                
                a = (math.sin(dlat/2)**2 + 
                     math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
                c = 2 * math.asin(math.sqrt(a))
                distance = R * c
                
                record['distance_to_hq_km'] = round(distance, 2)
                
                # Catégorisation de la distance
                if distance < 50:
                    record['location_category'] = 'LOCAL'
                elif distance < 200:
                    record['location_category'] = 'REGIONAL'
                else:
                    record['location_category'] = 'REMOTE'
            
            return record
        
        return records | 'Calculate distance to HQ' >> beam.Map(calculate_distance)
```

## 4. Déploiement sur Dataflow

### 4.1 Script de lancement

Créer le fichier `deploy_pipeline.sh` :

```bash
#!/bin/bash

# Configuration
PROJECT_ID="lake-471013"
REGION="us-east1"
JOB_NAME="employees-ingestion-$(date +%Y%m%d-%H%M%S)"
TEMP_LOCATION="gs://lakehouse-bucket-20250903/temp"
STAGING_LOCATION="gs://lakehouse-bucket-20250903/staging"
INPUT_PATH="gs://lakehouse-bucket-20250903/employees_5mb.csv"
OUTPUT_TABLE="lake-471013:lakehouse_employee_data.employees_dataflow"

# Vérification des prérequis
echo "🔍 Vérification des prérequis..."
gsutil ls $TEMP_LOCATION > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "📁 Création du dossier temp..."
    gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://lakehouse-bucket-20250903/ 2>/dev/null || true
    gsutil mkdir $TEMP_LOCATION
fi

gsutil mkdir $STAGING_LOCATION 2>/dev/null || true

# Activation des APIs nécessaires
echo "🔌 Activation des APIs..."
gcloud services enable dataflow.googleapis.com --project=$PROJECT_ID
gcloud services enable bigquery.googleapis.com --project=$PROJECT_ID

# Lancement du pipeline
echo "🚀 Lancement du pipeline Dataflow..."
echo "   Job Name: $JOB_NAME"
echo "   Input: $INPUT_PATH"  
echo "   Output: $OUTPUT_TABLE"

python src/employees_pipeline.py \
    --project=$PROJECT_ID \
    --region=$REGION \
    --input_path=$INPUT_PATH \
    --output_table=$OUTPUT_TABLE \
    --temp_location=$TEMP_LOCATION \
    --staging_location=$STAGING_LOCATION \
    --job_name=$JOB_NAME \
    --max_num_workers=5 \
    --machine_type=n1-standard-2 \
    --disk_size_gb=50 \
    --save_main_session \
    --setup_file=./setup.py

echo "✅ Pipeline lancé avec succès!"
echo "🔗 Suivre le job: https://console.cloud.google.com/dataflow/jobs?project=$PROJECT_ID"
```

### 4.2 Configuration du setup.py

Créer le fichier `setup.py` :

```python
from setuptools import setup, find_packages

setup(
    name='employees-dataflow-pipeline',
    version='1.0.0',
    description='Pipeline Dataflow pour ingestion CSV employees vers BigQuery',
    author='Data Team',
    author_email='data-team@company.com',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'apache-beam[gcp]==2.52.0',
        'google-cloud-bigquery>=3.0.0',
        'pandas>=1.3.0',
    ],
    python_requires='>=3.8',
)
```

### 4.3 Pipeline avec template Dataflow

Créer le fichier `src/template_pipeline.py` :

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.value_provider import RuntimeValueProvider

def run_template_pipeline():
    """Pipeline paramétrisé pour template Dataflow"""
    
    class CustomPipelineOptions(PipelineOptions):
        @classmethod
        def _add_argparse_args(cls, parser):
            parser.add_value_provider_argument('--input_path', type=str,
                                             help='Chemin du fichier CSV')
            parser.add_value_provider_argument('--output_table', type=str,
                                             help='Table BigQuery de sortie')
    
    pipeline_options = PipelineOptions()
    custom_options = pipeline_options.view_as(CustomPipelineOptions)
    
    with beam.Pipeline(options=pipeline_options) as pipeline:
        
        result = (
            pipeline
            | 'Read CSV' >> ReadFromText(custom_options.input_path)
            | 'Parse and Transform' >> beam.Map(EmployeeTransforms.parse_csv_line)
            | 'Filter Valid' >> beam.Filter(lambda x: x is not None)
            | 'Validate' >> beam.Map(EmployeeTransforms.validate_record)
            | 'Enrich' >> beam.Map(EmployeeTransforms.enrich_with_business_logic)
            | 'Write to BigQuery' >> WriteToBigQuery(
                table=custom_options.output_table,
                schema=BIGQUERY_SCHEMA,
                write_disposition=BigQueryDisposition.WRITE_TRUNCATE,
                create_disposition=BigQueryDisposition.CREATE_IF_NEEDED
            )
        )

if __name__ == '__main__':
    run_template_pipeline()
```

### 4.4 Création du template Dataflow

```bash
# Script pour créer un template réutilisable
#!/bin/bash

PROJECT_ID="lake-471013"
TEMPLATE_PATH="gs://lakehouse-bucket-20250903/templates/employees-ingestion-template"
STAGING_LOCATION="gs://lakehouse-bucket-20250903/staging"
TEMP_LOCATION="gs://lakehouse-bucket-20250903/temp"

echo "📋 Création du template Dataflow..."

python src/template_pipeline.py \
    --project=$PROJECT_ID \
    --runner=DataflowRunner \
    --template_location=$TEMPLATE_PATH \
    --staging_location=$STAGING_LOCATION \
    --temp_location=$TEMP_LOCATION \
    --setup_file=./setup.py

echo "✅ Template créé: $TEMPLATE_PATH"
echo "🔧 Utilisation du template:"
echo "gcloud dataflow jobs run employees-job-name \\"
echo "    --gcs-location=$TEMPLATE_PATH \\"
echo "    --region=us-east1 \\"  
echo "    --parameters input_path=gs://bucket/file.csv,output_table=project:dataset.table"
```

## 5. Monitoring et optimisations

### 5.1 Monitoring avec Cloud Monitoring

Créer le fichier `src/monitoring/dataflow_metrics.py` :

```python
import apache_beam as beam
from google.cloud import monitoring_v3
import time
import logging

class DataflowMetricsCollector(beam.DoFn):
    """Collecteur de métriques custom pour Cloud Monitoring"""
    
    def __init__(self, project_id):
        self.project_id = project_id
        self.client = None
        self.processed_count = beam.metrics.Metrics.counter('custom', 'processed_records')
        self.error_count = beam.metrics.Metrics.counter('custom', 'error_records')
        
    def setup(self):
        self.client = monitoring_v3.MetricServiceClient()
        
    def process(self, element):
        try:
            # Traitement de l'élément
            self.processed_count.inc()
            
            # Métriques métier custom
            if element.get('salaire', 0) > 100000:
                high_salary_metric = beam.metrics.Metrics.counter('business', 'high_salary_employees')
                high_salary_metric.inc()
                
            if element.get('has_missing_data', False):
                data_quality_metric = beam.metrics.Metrics.counter('quality', 'incomplete_records')
                data_quality_metric.inc()
            
            yield element
            
        except Exception as e:
            self.error_count.inc()
            logging.error(f"Erreur traitement record: {e}")
            # Ne pas faire yield pour éliminer l'enregistrement erroné

class PerformanceMonitoring:
    """Monitoring des performances du pipeline"""
    
    @staticmethod
    def add_processing_timestamp(records):
        """Ajoute timestamp de processing pour latency tracking"""
        
        def add_timestamp(record):
            if record:
                record['processing_timestamp'] = time.time()
            return record
            
        return records | 'Add processing timestamp' >> beam.Map(add_timestamp)
    
    @staticmethod
    def calculate_throughput(records):
        """Calcule le throughput du pipeline"""
        
        class ThroughputCalculator(beam.DoFn):
            def __init__(self):
                self.throughput_metric = beam.metrics.Metrics.counter('performance', 'records_per_second')
                self.start_time = time.time()
                self.batch_size = 1000
                self.processed_in_batch = 0
                
            def process(self, element):
                self.processed_in_batch += 1
                
                if self.processed_in_batch % self.batch_size == 0:
                    elapsed = time.time() - self.start_time
                    if elapsed > 0:
                        throughput = self.batch_size / elapsed
                        logging.info(f"Throughput: {throughput:.2f} records/sec")
                    
                    self.start_time = time.time()
                    
                yield element
                
        return records | 'Calculate throughput' >> beam.ParDo(ThroughputCalculator())
```

### 5.2 Alertes et notifications

Créer le fichier `src/monitoring/alerts.py` :

```python
import apache_beam as beam
from google.cloud import pubsub_v1
import json
import logging

class AlertingSystem(beam.DoFn):
    """Système d'alertes pour le pipeline"""
    
    def __init__(self, project_id, topic_name):
        self.project_id = project_id
        self.topic_name = topic_name
        self.publisher = None
        self.error_threshold = 100  # Seuil d'erreurs avant alerte
        self.error_count = 0
        
    def setup(self):
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(self.project_id, self.topic_name)
        
    def process(self, element):
        try:
            # Vérifications de qualité qui déclenchent des alertes
            if element.get('has_missing_data', False):
                self.send_data_quality_alert(element)
                
            if element.get('salary_outlier', False):
                self.send_outlier_alert(element)
                
            yield element
            
        except Exception as e:
            self.error_count += 1
            logging.error(f"Erreur processing: {e}")
            
            if self.error_count >= self.error_threshold:
                self.send_critical_alert(e)
                self.error_count = 0  # Reset counter
                
    def send_data_quality_alert(self, record):
        """Alerte qualité des données"""
        alert_data = {
            'type': 'DATA_QUALITY_WARNING',
            'employee_id': record.get('id'),
            'message': 'Données incomplètes détectées',
            'timestamp': time.time(),
            'severity': 'WARNING'
        }
        self.publish_alert(alert_data)
        
    def send_outlier_alert(self, record):
        """Alerte valeurs aberrantes"""
        alert_data = {
            'type': 'OUTLIER_DETECTED',
            'employee_id': record.get('id'),
            'field': 'salaire',
            'value': record.get('salaire'),
            'z_score': record.get('salaire_z_score'),
            'message': 'Valeur aberrante détectée dans le salaire',
            'timestamp': time.time(),
            'severity': 'INFO'
        }
        self.publish_alert(alert_data)
        
    def send_critical_alert(self, error):
        """Alerte critique système"""
        alert_data = {
            'type': 'CRITICAL_ERROR',
            'message': f'Trop d\'erreurs dans le pipeline: {str(error)}',
            'error_count': self.error_count,
            'timestamp': time.time(),
            'severity': 'CRITICAL'
        }
        self.publish_alert(alert_data)
        
    def publish_alert(self, alert_data):
        """Publie l'alerte dans Pub/Sub"""
        try:
            message_data = json.dumps(alert_data).encode('utf-8')
            future = self.publisher.publish(self.topic_path, message_data)
            logging.info(f"Alerte publiée: {alert_data['type']}")
        except Exception as e:
            logging.error(f"Erreur publication alerte: {e}")
```

### 5.3 Optimisations de performance

```python
# Optimisations dans le pipeline principal
class OptimizedEmployeePipeline:
    """Pipeline optimisé pour de gros volumes"""
    
    @staticmethod
    def create_optimized_pipeline(pipeline_options):
        
        # Configuration optimisée des workers
        pipeline_options.view_as(WorkerOptions).machine_type = 'n1-highmem-2'
        pipeline_options.view_as(WorkerOptions).disk_type = 'pd-ssd'
        pipeline_options.view_as(WorkerOptions).disk_size_gb = 100
        pipeline_options.view_as(WorkerOptions).use_public_ips = False  # Réseau privé plus rapide
        
        with beam.Pipeline(options=pipeline_options) as pipeline:
            
            # Traitement par batch pour optimiser les performances
            employees = (
                pipeline
                | 'Read CSV' >> ReadFromText(input_path)
                | 'Batch elements' >> beam.BatchElements(
                    min_batch_size=1000, max_batch_size=5000)
                | 'Process batch' >> beam.ParDo(BatchProcessor())
                | 'Flatten results' >> beam.FlatMap(lambda batch: batch)
                | 'Write to BigQuery' >> WriteToBigQuery(
                    table=output_table,
                    batch_size=1000,  # Batch size pour BigQuery
                    write_disposition=BigQueryDisposition.WRITE_TRUNCATE,
                    create_disposition=BigQueryDisposition.CREATE_IF_NEEDED
                )
            )

class BatchProcessor(beam.DoFn):
    """Traitement optimisé par batch"""
    
    def process(self, batch):
        processed_batch = []
        
        for line in batch:
            try:
                record = EmployeeTransforms.parse_csv_line(line)
                if record:
                    record = EmployeeTransforms.validate_record(record)
                    if record:
                        record = EmployeeTransforms.enrich_with_business_logic(record)
                        processed_batch.append(record)
            except Exception as e:
                logging.warning(f"Erreur traitement ligne: {e}")
                continue
                
        yield processed_batch
```

## 6. Tests et déploiement

### 6.1 Tests unitaires

Créer le fichier `tests/test_transforms.py` :

```python
import unittest
import apache_beam as beam
from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import assert_that, equal_to
from src.employees_pipeline import EmployeeTransforms

class TestEmployeeTransforms(unittest.TestCase):
    
    def test_parse_csv_line_valid(self):
        """Test parsing d'une ligne CSV valide"""
        line = "1;Dupont;Jean;jean.dupont@email.com;30;Paris;75001;0123456789;50000;IT;2020-01-15;ACTIF;85.5;48.8566;2.3522;Excellent;REF001;SENIOR;A;2020-01-15T10:30:00"
        
        result = EmployeeTransforms.parse_csv_line(line)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['nom'], 'Dupont')
        self.assertEqual(result['email'], 'jean.dupont@email.com')
        self.assertEqual(result['salaire'], 50000.0)
    
    def test_parse_csv_line_invalid(self):
        """Test parsing d'une ligne CSV invalide"""
        line = "1;Dupont"  # Ligne incomplète
        
        result = EmployeeTransforms.parse_csv_line(line)
        
        self.assertIsNone(result)
    
    def test_validate_record(self):
        """Test validation d'un enregistrement"""
        record = {
            'id': 1,
            'nom': 'Dupont',
            'prenom': 'Jean',
            'email': 'jean.dupont@email.com',
            'age': 30,
            'salaire': 50000
        }
        
        result = EmployeeTransforms.validate_record(record)
        
        self.assertIsNotNone(result)
        self.assertTrue(result['email_valid'])
        self.assertIsNotNone(result['ingestion_date'])
    
    def test_pipeline_integration(self):
        """Test d'intégration du pipeline complet"""
        with TestPipeline() as p:
            input_data = [
                "1;Dupont;Jean;jean@email.com;30;Paris;75001;0123;50000;IT;2020-01-15;ACTIF;85;48.8;2.3;Comment;REF;SENIOR;A;2020-01-15T10:00:00"
            ]
            
            result = (
                p 
                | beam.Create(input_data)
                | beam.Map(EmployeeTransforms.parse_csv_line)
                | beam.Filter(lambda x: x is not None)
                | beam.Map(EmployeeTransforms.validate_record)
            )
            
            # Vérifier qu'au moins un enregistrement est traité
            assert_that(result, lambda records: len(list(records)) > 0)

if __name__ == '__main__':
    unittest.main()
```

### 6.2 Déploiement avec CI/CD

Créer le fichier `.github/workflows/dataflow-deploy.yml` :

```yaml
name: Deploy Dataflow Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

env:
  PROJECT_ID: lake-471013
  REGION: us-east1

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest
    
    - name: Run tests
      run: |
        pytest tests/ -v
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Cloud SDK
      uses: google-github-actions/setup-gcloud@v0
      with:
        project_id: ${{ env.PROJECT_ID }}
        service_account_key: ${{ secrets.GCP_SA_KEY }}
        export_default_credentials: true
    
    - name: Deploy Dataflow Template
      run: |
        chmod +x deploy_template.sh
        ./deploy_template.sh
```

Ce tutoriel couvre l'implémentation complète d'un pipeline Dataflow pour traiter des données CSV à grande échelle avec Apache Beam, incluant les transformations avancées, le monitoring, et les bonnes pratiques de déploiement.