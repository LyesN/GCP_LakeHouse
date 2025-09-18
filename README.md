# GCP Data Lakehouse Framework

Framework standardisé pour la construction de pipelines de données sur Google Cloud Platform, basé sur une architecture en couches et des patterns Data Warehouse éprouvés.

## 📋 Vue d'ensemble

Ce repository implémente un framework complet de Data Lakehouse sur GCP avec :
- **Architecture en couches** : RAW (Cloud Storage) → STG (Tables externes) → ODS (Tables matérialisées)
- **Patterns Data Warehouse** : Ingestion, transformation et stockage optimisés BigQuery
- **Standards et patterns** définis dans `framework.md`
- **Templates réutilisables** pour l'ingestion de données
- **Tooling** de génération de données d'exemple

## 🏗️ Architecture

```
RAW (Cloud Storage) → STG (01_STG) → ODS (02_ODS)
```

### Stack Technique Autorisé
- **BigQuery** : Data Warehouse principal
- **Dataform** : ELT et orchestration
- **Cloud Storage** : Data Lake (fichiers raw)
- **Cloud Composer** : Orchestration complexe
- **Cloud Functions** : Microservices serverless

## 📁 Structure du Projet

```
├── framework.md              # 📖 Documentation du framework et patterns
├── CLAUDE.md                 # ⚙️  Configuration et règles de développement
├── Bigquery/                 # 🗄️  Scripts DDL BigQuery
│   └── 00_ddl/              # Scripts de création de tables
├── Dataform/                # 🔄 Transformations ELT
│   ├── 01_stg/              # Tables staging (externes)
│   ├── 02_ods/              # Tables opérationnelles (matérialisées)
│   └── 03_dwh/              # Data Warehouse (agrégations)
├── docs/                    # 📚 Documentation technique détaillée
├── tools/                   # 🛠️  Générateurs de données d'exemple
│   ├── generate_employees_csv.py
│   └── generate_contract_csv.py
└── tutos/                   # 🎓 Tutoriels d'implémentation
    ├── tuto1_bases_ingestion_sql.md
    ├── tuto2_ingestion_bigquery_colab.ipynb
    └── tuto3_pipeline_dataform.md
```

## 🚀 Démarrage Rapide

1. **Consulter le framework** : Lire `framework.md` pour comprendre les standards
2. **Choisir un pattern** : Identifier le pattern adapté à votre cas d'usage
3. **Utiliser les templates** : S'inspirer de l'implémentation `employees` comme référence
4. **Suivre les tutoriels** : Commencer par `tutos/tuto1_bases_ingestion_sql.md`

## 📊 Patterns et Templates

Pour des raisons de **productivité** et de **cohérence**, le framework propose une liste de patterns communs associés à des exemples de leurs livrables.

L'exemple **employees** illustre un pattern complet avec tous ses fichiers types, permettant :
- 🔄 **Réutilisation** : Templates prêts à adapter pour de nouveaux cas d'usage
- 🤖 **Génération automatique** : Code standardisé générable par l'IA
- ✅ **Cohérence** : Respect automatique des standards du framework

## 🎯 Public Cible

- **Data Engineers** : Implémentation des pipelines
- **Data Architects** : Conception des flux de données
- **Équipes Data** : Utilisation des standards GCP

## 🔧 Prérequis

- Accès à GCP Console avec permissions BigQuery et GCS
- Dataform workspace configuré
- Cloud Composer (optionnel, pour orchestration complexe)

## 📚 Documentation

### Framework et Standards
- 📖 **[framework.md](framework.md)** - Framework complet et patterns d'implémentation
- ⚙️ **[CLAUDE.md](CLAUDE.md)** - Configuration et règles de développement

### Documentation Technique
- 🏗️ **[Architecture Lakehouse](docs/architecture-lakehouse-alimente-fichier.md)** - Architecture visuelle et exemples
- 📊 **Diagrammes** : `docs/Architecture-pipline-data.png` et variantes

### Tutoriels
- 🎓 **[Bases d'ingestion SQL](tutos/tuto1_bases_ingestion_sql.md)** - Fondamentaux
- 🔄 **[Pipeline Dataform](tutos/tuto3_pipeline_dataform.md)** - Transformations ELT
- 📊 **[Notebook BigQuery](tutos/tuto2_ingestion_bigquery_colab.ipynb)** - Analyse interactive

## 🛠️ Outils Inclus

- **Générateur CSV employees** : `tools/generate_employees_csv.py`
- **Générateur CSV contracts** : `tools/generate_contract_csv.py`
- **Données d'exemple** : Disponibles dans `tools/data/`

## 📈 Évolutions

Ce framework est conçu pour évoluer. Les nouveaux patterns doivent :
1. Respecter l'architecture en couches
2. Utiliser uniquement la stack GCP autorisée
3. Suivre les conventions de nommage
4. Être documentés avec tutoriels associés

## 🔗 Ressources Externes

- [Bonnes pratiques BigQuery](https://cloud.google.com/bigquery/docs/load-transform-export-intro?hl=fr)
- [Documentation Dataform](https://cloud.google.com/dataform/docs)
- [Guide Cloud Composer](https://cloud.google.com/composer/docs)