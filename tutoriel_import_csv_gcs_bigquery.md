# Tutoriel : Importer un fichier CSV depuis Google Cloud Storage vers BigQuery

## Contexte
- **Public cible** : Data Engineers, Data Analysts
- **Environnement** : GCP Console (environnement DEV)
- **Stack** : BigQuery
- **Objectif** : Créer un pipeline de données automatisé

## Prérequis
- Accès à la GCP Console
- Fichier CSV disponible dans Google Cloud Storage
- Permissions appropriées sur BigQuery et GCS

## Plan du tutoriel

1. **[Étape 1](#étape-1--vérification-du-fichier-csv-dans-gcs)** : Vérification du fichier CSV dans GCS
2. **[Étape 2](#étape-2--création-du-dataset-bigquery)** : Création du dataset BigQuery
3. **[Étape 3](#étape-3--import-du-fichier-csv)** : Import manuel du fichier CSV
   - Configuration via l'interface BigQuery
   - Définition du schéma de données
4. **[Étape 4](#étape-4--automatisation-avec-apache-airflow)** : Automatisation avec Apache Airflow
   - Architecture du pipeline
   - Configuration des operators
   - Monitoring et bonnes pratiques
5. **[Étape 5](#étape-5--vérification-et-monitoring)** : Vérification et monitoring
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

## Étape 2 : Création du dataset BigQuery

1. Dans la **GCP Console**, accédez à **BigQuery**
2. Dans l'explorateur, cliquez sur votre projet
3. Cliquez sur **Créer un dataset**
4. Configurez le dataset :
   - **ID du dataset** : `employee_data`
   - **Emplacement** : Europe (ou selon vos besoins)
   - **Expiration** : Par défaut ou selon votre politique

## Étape 3 : Import du fichier CSV

### Via l'interface BigQuery

1. Sélectionnez votre dataset `employee_data`
2. Cliquez sur **Créer une table**
3. Configurez l'import :
   - **Créer une table à partir de** : Google Cloud Storage
   - **Sélectionner un fichier depuis GCS bucket** : `gs://votre-bucket/votre-fichier.csv`
   - **Format de fichier** : CSV
   - **Nom de la table** : `employees`

### Configuration avancée

4. Dans **Schéma** :
   - Cochez **Détection automatique**
   - Ou définissez manuellement le schéma basé sur l'exemple :

```json
[
  {"name": "id", "type": "INTEGER", "mode": "REQUIRED"},
  {"name": "nom", "type": "STRING", "mode": "NULLABLE"},
  {"name": "prenom", "type": "STRING", "mode": "NULLABLE"},
  {"name": "email", "type": "STRING", "mode": "NULLABLE"},
  {"name": "age", "type": "INTEGER", "mode": "NULLABLE"},
  {"name": "ville", "type": "STRING", "mode": "NULLABLE"},
  {"name": "code_postal", "type": "STRING", "mode": "NULLABLE"},
  {"name": "telephone", "type": "STRING", "mode": "NULLABLE"},
  {"name": "salaire", "type": "FLOAT", "mode": "NULLABLE"},
  {"name": "departement", "type": "STRING", "mode": "NULLABLE"},
  {"name": "date_embauche", "type": "DATE", "mode": "NULLABLE"},
  {"name": "statut", "type": "STRING", "mode": "NULLABLE"},
  {"name": "score", "type": "FLOAT", "mode": "NULLABLE"},
  {"name": "latitude", "type": "FLOAT", "mode": "NULLABLE"},
  {"name": "longitude", "type": "FLOAT", "mode": "NULLABLE"},
  {"name": "commentaire", "type": "STRING", "mode": "NULLABLE"},
  {"name": "reference", "type": "STRING", "mode": "NULLABLE"},
  {"name": "niveau", "type": "STRING", "mode": "NULLABLE"},
  {"name": "categorie", "type": "STRING", "mode": "NULLABLE"},
  {"name": "timestamp", "type": "TIMESTAMP", "mode": "NULLABLE"}
]
```

5. Dans **Options avancées** :
   - **Nombre de lignes d'en-tête à ignorer** : 1
   - **Séparateur de champ** : Point-virgule (;)
   - **Ignorer les lignes inconnues** : Activé
   - **Autoriser les champs en désordre** : Activé

## Étape 4 : Automatisation avec Apache Airflow

### Architecture du pipeline Airflow

L'orchestration se fait via Apache Airflow avec les composants suivants :

1. **DAG principal** : Orchestration des tâches d'import
2. **Operators GCP** : Intégration native avec BigQuery et GCS
3. **Scheduling** : Planification des exécutions
4. **Monitoring** : Suivi des performances et alertes

### Structure du pipeline

Le pipeline Airflow se compose de plusieurs tâches :

1. **Vérification des prérequis**
   - Validation de la présence du fichier CSV dans GCS
   - Vérification des permissions BigQuery
   - Contrôle de l'espace disponible

2. **Préparation des données**
   - Validation du format CSV
   - Contrôle qualité des données (optionnel)
   - Archivage des versions précédentes

3. **Import vers BigQuery**
   - Utilisation du `GCSToBigQueryOperator`
   - Configuration du job d'import
   - Gestion des erreurs et retry

4. **Post-traitement**
   - Validation des données importées
   - Mise à jour des métadonnées
   - Notifications de succès/échec

### Configuration du DAG

Le DAG Airflow doit être configuré avec :

- **dag_id** : `csv_import_to_bigquery`
- **schedule_interval** : `'0 2 * * *'` (quotidien à 2h)
- **start_date** : Date de début du pipeline
- **catchup** : `False` pour éviter les rattrapages
- **max_active_runs** : `1` pour éviter les conflits

### Operators Airflow utilisés

1. **GoogleCloudStorageObjectExistsSensor**
   - Attendre la disponibilité du fichier CSV
   - Timeout configurable
   - Mode poke ou reschedule

2. **GCSToBigQueryOperator**
   - Import direct de GCS vers BigQuery
   - Configuration du schéma
   - Gestion des options CSV (délimiteur, en-têtes)

3. **BigQueryCheckOperator**
   - Validation post-import
   - Contrôle du nombre de lignes
   - Vérification de la qualité des données

4. **EmailOperator** (optionnel)
   - Notifications en cas de succès/échec
   - Rapports de performance

### Configuration des connexions

Dans l'interface Airflow Admin > Connections :

1. **google_cloud_default**
   - Connection Type : Google Cloud
   - Project Id : votre-projet-gcp
   - Keyfile JSON : Clé de service avec permissions appropriées

### Monitoring et alertes

1. **Airflow UI**
   - Suivi en temps réel des DAG runs
   - Logs détaillés par tâche
   - Graphique de dépendances

2. **Métriques personnalisées**
   - Nombre de lignes importées
   - Temps d'exécution
   - Taux de succès/échec

3. **Intégration avec monitoring GCP**
   - Cloud Logging pour les logs centralisés
   - Cloud Monitoring pour les métriques
   - Alerting Policy pour les notifications

### Bonnes pratiques Airflow

1. **Gestion des dépendances**
   - Variables Airflow pour la configuration
   - Connections sécurisées
   - Séparation des environnements (dev/prod)

2. **Retry et récupération**
   - Configuration des retries automatiques
   - Stratégie de backoff exponentiel
   - Alertes sur échecs répétés

3. **Performance**
   - Parallélisation des tâches indépendantes
   - Pool de workers approprié
   - Optimisation des ressources

### Déploiement

1. **Environnement Airflow**
   - Cloud Composer (recommandé pour GCP)
   - Airflow auto-géré sur GKE
   - Instance Compute Engine avec Airflow

2. **Versioning**
   - DAGs stockés dans un repository Git
   - CI/CD pour le déploiement
   - Tests automatisés des DAGs

## Étape 5 : Vérification et monitoring

### Vérification des données

```sql
-- Vérifier l'import
SELECT COUNT(*) as total_rows
FROM `votre-projet.employee_data.employees`;

-- Aperçu des données
SELECT *
FROM `votre-projet.employee_data.employees`
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
CREATE TABLE `votre-projet.employee_data.employees_partitioned`
PARTITION BY DATE(date_embauche)
CLUSTER BY departement, ville
AS SELECT * FROM `votre-projet.employee_data.employees`;
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