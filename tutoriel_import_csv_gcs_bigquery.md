# Tutoriel : Importer un fichier CSV depuis Google Cloud Storage vers BigQuery

## Contexte
- **Public cible** : Data Engineers, Data Analysts
- **Environnement** : GCP Console (environnement DEV)
- **Stack** : BigQuery
- **Objectif** : Créer un pipeline de données automatisé

## Paramètres du projet
- **Projet GCP** : `lakehouse`
- **Dataset BigQuery** : `lakehouse_employee_data`
- **Bucket GCS** : `lakehouse-bucket-20250903`
- **Fichier CSV** : `employees_5mb.csv`
- **Chemin complet** : `gs://lakehouse-bucket-20250903/employees_5mb.csv`

## Prérequis
- Accès à la GCP Console
- Fichier CSV disponible dans Google Cloud Storage
- Permissions appropriées sur BigQuery et GCS

## Plan du tutoriel

1. **[Étape 1](#étape-1--vérification-du-fichier-csv-dans-gcs)** : Vérification du fichier CSV dans GCS
2. **[Étape 2](#étape-2--développement-sur-console-gcp)** : Développement sur Console GCP
   - Création du dataset BigQuery
   - Définition de la table et du schéma
   - Développement du flux d'ingestion en SQL
3. **[Étape 3](#étape-3--test-et-validation-du-flux)** : Test et validation du flux d'ingestion
4. **[Étape 4](#étape-4--intégration-airflow-comme-orchestrateur)** : Intégration Airflow comme orchestrateur
   - Architecture du trigger Airflow
   - Configuration des connexions GCP
   - Monitoring et alertes
5. **[Étape 5](#étape-5--déploiement-et-monitoring-de-production)** : Déploiement et monitoring de production
6. **[Étape 6](#étape-6--optimisations-pour-lentreprise)** : Optimisations pour l'entreprise
   - Partitioning et clustering
   - Gestion des données sensibles
7. **[Bonnes pratiques](#bonnes-pratiques)** et **[Dépannage](#dépannage)**

## Structure du fichier CSV exemple
Le fichier contient les colonnes suivantes avec séparateur `;` :
```
id;nom;prenom;email;age;ville;code_postal;telephone;salaire;departement;date_embauche;statut;score;latitude;longitude;commentaire;reference;niveau;categorie;timestamp
```

## Étape 1 : Vérification du fichier CSV dans GCS

1. Accédez à la **GCP Console**
2. Naviguez vers **Cloud Storage**
3. Localisez votre bucket contenant le fichier CSV
4. Vérifiez que le fichier est accessible et notez son chemin complet

## Étape 2 : Développement sur Console GCP

### Use Case : Data Engineer développe le flux d'ingestion

Un Data Engineer ou UC (User Case) développe directement sur la **Console GCP** l'ensemble du flux d'ingestion de données. Cette approche permet un développement itératif et un contrôle total sur la structure des données.

### 2.1 Création du dataset BigQuery

1. Dans la **GCP Console**, accédez à **BigQuery**
2. Dans l'explorateur, cliquez sur votre projet
3. Cliquez sur **Créer un dataset**
4. Configurez le dataset :
   - **ID du dataset** : `lakehouse_employee_data`
   - **Emplacement** : Europe (ou selon vos besoins)
   - **Expiration** : Par défaut ou selon votre politique d'entreprise

### 2.2 Création de la table avec schéma défini

Le Data Engineer crée la table de destination avec un schéma précis :

```sql
-- Création de la table employees avec schéma typé
CREATE TABLE `lakehouse.lakehouse_employee_data.employees` (
  id INT64 NOT NULL,
  nom STRING,
  prenom STRING,
  email STRING,
  age INT64,
  ville STRING,
  code_postal STRING,
  telephone STRING,
  salaire FLOAT64,
  departement STRING,
  date_embauche DATE,
  statut STRING,
  score FLOAT64,
  latitude FLOAT64,
  longitude FLOAT64,
  commentaire STRING,
  reference STRING,
  niveau STRING,
  categorie STRING,
  timestamp TIMESTAMP,
  -- Métadonnées d'ingestion
  ingestion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  source_file STRING
);
```

### 2.3 Développement du flux d'ingestion en SQL

Le Data Engineer développe une série de requêtes SQL pour l'ingestion :

#### A. Requête de chargement depuis GCS

```sql
-- Flux d'ingestion principal depuis GCS
LOAD DATA INTO `lakehouse.lakehouse_employee_data.employees`
FROM FILES (
  format = 'CSV',
  field_delimiter = ';',
  skip_leading_rows = 1,
  uris = ['gs://lakehouse-bucket-20250903/employees_5mb.csv']
);
```

#### B. Requête de validation et nettoyage

```sql
-- Validation et nettoyage des données
CREATE OR REPLACE TABLE `lakehouse.lakehouse_employee_data.employees_clean` AS
SELECT 
  id,
  TRIM(nom) as nom,
  TRIM(prenom) as prenom,
  LOWER(email) as email,
  CASE 
    WHEN age BETWEEN 18 AND 65 THEN age 
    ELSE NULL 
  END as age,
  ville,
  code_postal,
  telephone,
  salaire,
  departement,
  date_embauche,
  statut,
  score,
  latitude,
  longitude,
  commentaire,
  reference,
  niveau,
  categorie,
  timestamp,
  CURRENT_TIMESTAMP() as processed_date
FROM `lakehouse.lakehouse_employee_data.employees`
WHERE id IS NOT NULL;
```

#### C. Contrôles qualité intégrés

```sql
-- Requêtes de contrôle qualité
SELECT 
  'Total lignes' as metric,
  COUNT(*) as valeur
FROM `lakehouse.lakehouse_employee_data.employees_clean`

UNION ALL

SELECT 
  'Emails invalides' as metric,
  COUNT(*) as valeur  
FROM `lakehouse.lakehouse_employee_data.employees_clean`
WHERE email NOT LIKE '%@%'

UNION ALL

SELECT 
  'Données manquantes critiques' as metric,
  COUNT(*) as valeur
FROM `lakehouse.lakehouse_employee_data.employees_clean`
WHERE nom IS NULL OR prenom IS NULL;
```

## Étape 3 : Test et validation du flux

### 3.1 Tests unitaires des transformations

Le Data Engineer teste chaque étape du flux :

1. **Test de chargement** : Vérification que les données sont correctement importées depuis GCS
2. **Test de transformation** : Validation des règles de nettoyage et normalisation
3. **Test de qualité** : Contrôle des métriques de qualité des données

### 3.2 Validation des performances

```sql
-- Analyse des performances d'ingestion
SELECT 
  job_id,
  creation_time,
  start_time,
  end_time,
  total_bytes_processed,
  total_slot_ms
FROM `region-europe-west1.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE job_type = 'LOAD'
AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY);
```

### 3.3 Tests de régression

Le Data Engineer s'assure que les modifications n'impactent pas les données existantes :
- Comparaison des métriques avant/après
- Validation des schémas
- Tests de non-régression sur les requêtes aval

## Étape 4 : Intégration Airflow comme orchestrateur

### Rôle d'Airflow : Trigger du flux d'ingestion

Une fois que le Data Engineer a développé et testé le flux d'ingestion en SQL sur la **Console GCP**, **Apache Airflow** intervient uniquement comme **orchestrateur et trigger** du processus. Airflow n'exécute pas directement le code SQL mais déclenche l'exécution des requêtes développées.

### 4.1 Architecture du trigger Airflow

**Principe** : Airflow orchestre l'exécution séquentielle des requêtes SQL développées par le Data Engineer.

#### Flux d'orchestration :

1. **Détection de fichier** : Airflow surveille l'arrivée de nouveaux fichiers CSV dans GCS
2. **Trigger d'ingestion** : Lancement du flux d'ingestion BigQuery développé
3. **Monitoring d'exécution** : Suivi de l'état des jobs BigQuery
4. **Validation qualité** : Exécution des contrôles qualité
5. **Notifications** : Alertes en cas de succès/échec

### 4.2 Intégration avec les développements GCP

#### A. Exécution des requêtes SQL développées

Airflow utilise les **operators BigQuery** pour déclencher les requêtes SQL créées par le Data Engineer :

- **BigQueryInsertJobOperator** : Exécute les requêtes `LOAD DATA` développées
- **BigQueryCreateEmptyTableOperator** : Crée les tables si nécessaire
- **BigQueryCheckOperator** : Lance les contrôles qualité SQL

#### B. Gestion des paramètres dynamiques

Airflow injecte des paramètres dynamiques dans les requêtes SQL :

- **Date d'exécution** : `{{ ds }}` pour les partitions temporelles
- **Fichiers source** : Détection automatique des nouveaux fichiers CSV
- **Variables d'environnement** : Différenciation dev/staging/prod

#### C. Orchestration des étapes

L'orchestrateur Airflow séquence l'exécution :

1. **Pré-validation** → Vérification fichier source
2. **Ingestion** → Exécution du `LOAD DATA` développé
3. **Transformation** → Application des règles de nettoyage SQL
4. **Contrôle qualité** → Exécution des requêtes de validation
5. **Post-traitement** → Notifications et métriques

### 4.3 Configuration de l'intégration

#### Connexions GCP dans Airflow

L'intégration nécessite la configuration des connexions :

- **Service Account** : Clé de service avec permissions BigQuery et GCS
- **Project ID** : lakehouse
- **Default location** : Région pour l'exécution des jobs

#### Variables d'environnement

Airflow gère les paramètres via des variables :

- **Dataset names** : `lakehouse_employee_data`, `lakehouse_employee_data_staging`
- **GCS paths** : `gs://lakehouse-bucket-20250903/`
- **Notification emails** : Destinataires des alertes
- **Retry policies** : Nombre de tentatives et délais

### 4.4 Monitoring et alertes via Airflow

#### Tableaux de bord Airflow

1. **DAG View** : Visualisation du flux d'orchestration
2. **Task logs** : Logs détaillés de chaque étape BigQuery
3. **Gantt Chart** : Analyse des performances temporelles

#### Intégration monitoring GCP

Airflow remonte les métriques vers les outils de monitoring GCP :

- **Cloud Logging** : Centralisation des logs d'exécution
- **Cloud Monitoring** : Métriques de performance des jobs
- **Cloud Alerting** : Notifications automatisées

#### Alertes configurées

1. **Échec d'ingestion** : Notification immédiate aux Data Engineers
2. **Dépassement SLA** : Alerte si le traitement dépasse le temps alloué
3. **Anomalies qualité** : Notification si les contrôles détectent des problèmes
4. **Ressources** : Alerte si consommation excessive de slots BigQuery

### 4.5 Gestion de l'environnement d'entreprise

#### Séparation des environnements

Airflow orchestre différents environnements :

- **DEV** : Tests et développements sur datasets de développement
- **STAGING** : Validation avec données anonymisées
- **PRODUCTION** : Exécution sur les données réelles

#### Gestion des permissions

L'orchestrateur Airflow respecte la gouvernance des données :

- **Rôles IAM** : Séparation des accès par environnement
- **Service Accounts** : Comptes dédiés par type d'opération
- **Audit Trail** : Traçabilité complète des exécutions

#### Stratégies de déploiement

1. **Cloud Composer** : Service managé GCP recommandé pour l'entreprise
2. **Airflow sur GKE** : Déploiement containerisé avec contrôle total
3. **VM instances** : Solution simple pour environnements de développement

### 4.6 Avantages de cette approche

**Séparation des responsabilités** :
- **Data Engineers** : Focus sur la logique métier et les transformations SQL
- **Airflow** : Orchestration, scheduling et monitoring
- **GCP BigQuery** : Exécution performante des requêtes

**Flexibilité** :
- Modifications SQL sans redéploiement Airflow
- Tests indépendants des requêtes sur Console GCP
- Réutilisabilité des flux pour différents datasets

**Monitoring centralisé** :
- Vision unifiée de tous les pipelines de données
- Alertes cohérentes pour tous les flux d'ingestion
- Métriques de performance agrégées

## Étape 5 : Déploiement et monitoring de production

### Vérification des données

```sql
-- Vérifier l'import
SELECT COUNT(*) as total_rows
FROM `lakehouse.lakehouse_employee_data.employees`;

-- Aperçu des données
SELECT *
FROM `lakehouse.lakehouse_employee_data.employees`
LIMIT 10;
```

### Monitoring

1. **Cloud Logging** : Surveillez les logs d'import
2. **BigQuery Jobs** : Vérifiez l'historique des jobs d'import
3. **Cloud Monitoring** : Créez des alertes sur les échecs d'import

## Étape 6 : Optimisations pour l'entreprise

### Partitioning et Clustering

```sql
-- Créer une table partitionnée par date d'embauche
CREATE TABLE `lakehouse.lakehouse_employee_data.employees_partitioned`
PARTITION BY DATE(date_embauche)
CLUSTER BY departement, ville
AS SELECT * FROM `lakehouse.lakehouse_employee_data.employees`;
```

### Gestion des données sensibles

1. **Data Loss Prevention (DLP)** : Scanner les données sensibles
2. **IAM** : Contrôler l'accès aux données
3. **Audit Logs** : Tracer les accès aux données

## Bonnes pratiques

- **Validation des données** : Implémentez des contrôles qualité
- **Sauvegarde** : Conservez les versions précédentes
- **Documentation** : Maintenez la documentation à jour
- **Tests** : Testez les imports en environnement de développement
- **Monitoring** : Surveillez les performances et coûts

## Dépannage

### Erreurs communes

- **Erreur de schéma** : Vérifiez le format des données
- **Permissions insuffisantes** : Validez les rôles IAM
- **Quota dépassé** : Surveillez les limites BigQuery
- **Format CSV incorrect** : Vérifiez les séparateurs et encodage

### Logs utiles

```bash
# Logs Cloud Function
gcloud logs read "resource.type=cloud_function" --limit 50

# Jobs BigQuery
bq ls -j --max_results 10
```

Ce pipeline automatisé permettra l'import régulier de vos fichiers CSV depuis GCS vers BigQuery, avec monitoring et gestion d'erreurs appropriés pour un environnement d'entreprise.