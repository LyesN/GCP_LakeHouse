# Déploiement Airflow sur Kubernetes (Windows)

## 🎯 Objectif

Déployer Apache Airflow sur un cluster Kubernetes local (Docker Desktop) sur Windows pour orchestrer des pipelines de données.

## 🛠️ Prérequis

- **Docker Desktop** installé avec Kubernetes activé
- **kubectl** configuré et fonctionnel  
- **Windows 10/11** avec PowerShell ou Invite de commande

### Vérification des prérequis

```bash
# Vérifier Docker
docker --version

# Vérifier kubectl
kubectl version --client

# Vérifier le cluster Kubernetes
kubectl cluster-info
```

## 🚀 Déploiement rapide

### 1. Cloner et naviguer

```bash
cd E:\Téléchargements\GCP_LakeHouse\airflow-k8s
```

### 2. Lancer le déploiement

```bash
scripts\deploy.bat
```

### 3. Vérifier le statut

```bash
scripts\status.bat
```

## 📁 Structure du projet

```
airflow-k8s/
├── manifests/              # Manifests Kubernetes
│   ├── namespace.yaml      # Namespace airflow
│   ├── postgresql.yaml     # Base de données PostgreSQL
│   ├── redis.yaml         # Cache Redis pour Celery
│   ├── airflow-configmap.yaml    # Configuration Airflow
│   ├── airflow-volumes.yaml      # Volumes et DAGs
│   ├── airflow-webserver.yaml    # Interface Web
│   ├── airflow-scheduler.yaml    # Planificateur
│   ├── airflow-worker.yaml       # Workers Celery
│   └── airflow-flower.yaml       # Monitoring Celery
├── scripts/                # Scripts de déploiement
│   ├── deploy.bat         # Script de déploiement complet
│   ├── stop.bat          # Arrêt des services
│   ├── status.bat        # Vérification du statut
│   └── logs.bat          # Consultation des logs
├── configs/               # Configurations personnalisées
├── dags/                 # DAGs Airflow (synchronisés)
└── logs/                 # Logs Airflow
```

## 🌐 Accès aux services

Une fois déployé, les services sont accessibles via :

| Service | URL | Credentials |
|---------|-----|-------------|
| **Airflow Web UI** | http://localhost:32794 | admin / admin123 |
| **Flower (Celery)** | http://localhost:31847 | admin / flower123 |

## 🔧 Architecture déployée

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Webserver     │    │   Scheduler     │    │   Worker(x2)    │
│   Port: 8080    │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                ┌─────────────────────────────────┐
                │          PostgreSQL            │
                │        (Metadata DB)           │
                └─────────────────────────────────┘
                                  │
                ┌─────────────────────────────────┐
                │            Redis               │
                │       (Message Broker)         │
                └─────────────────────────────────┘
```

### Composants déployés

- **PostgreSQL** : Base de données des métadonnées Airflow
- **Redis** : Message broker pour Celery
- **Webserver** : Interface utilisateur Web  
- **Scheduler** : Planification et orchestration des DAGs
- **Workers** : Exécution des tâches (2 replicas)
- **Flower** : Interface de monitoring Celery

## 📋 Commandes utiles

### Scripts principaux

```bash
# Déploiement complet
scripts\deploy.bat

# Vérifier le statut
scripts\status.bat  

# Voir les logs d'un service
scripts\logs.bat webserver
scripts\logs.bat scheduler

# Arrêter Airflow
scripts\stop.bat
```

### Commandes kubectl

```bash
# Voir tous les pods
kubectl get pods -n airflow

# Voir les services
kubectl get services -n airflow

# Logs en temps réel
kubectl logs -n airflow deployment/airflow-webserver -f

# Accéder à un pod
kubectl exec -it -n airflow deployment/airflow-webserver -- bash

# Redémarrer un service
kubectl rollout restart deployment/airflow-webserver -n airflow
```

## 📊 Monitoring et maintenance

### Vérification de santé

```bash
# Status des pods
kubectl get pods -n airflow -w

# Vérifier les ressources
kubectl top pods -n airflow

# Events du namespace
kubectl get events -n airflow --sort-by='.lastTimestamp'
```

### Scaling des workers

```bash
# Augmenter le nombre de workers
kubectl scale deployment airflow-worker --replicas=4 -n airflow

# Vérifier le scaling
kubectl get deployment airflow-worker -n airflow
```

## 🔧 Configuration personnalisée

### Variables d'environnement

Modifiez `manifests/airflow-configmap.yaml` pour personnaliser :

- Connexions de base de données
- Configuration GCP
- Variables Airflow
- Paramètres de sécurité

### Ajout de DAGs

1. Placez vos fichiers DAG dans le dossier `dags/`
2. Redéployez la configuration :

```bash
kubectl delete configmap airflow-dags -n airflow
kubectl apply -f manifests/airflow-volumes.yaml
kubectl rollout restart deployment/airflow-webserver -n airflow
kubectl rollout restart deployment/airflow-scheduler -n airflow
```

## 🛠️ Dépannage

### Problèmes courants

#### Pods en état "Pending"

```bash
# Vérifier les ressources
kubectl describe pod <pod-name> -n airflow

# Vérifier les PVC
kubectl get pvc -n airflow
```

#### Services inaccessibles

```bash
# Vérifier les services
kubectl get services -n airflow

# Vérifier les NodePorts
kubectl describe service airflow-webserver-service -n airflow
```

#### Erreurs de base de données

```bash
# Logs PostgreSQL
scripts\logs.bat postgres

# Réinitialiser la DB (⚠️ Perte de données)
kubectl delete pvc postgres-pvc -n airflow
kubectl apply -f manifests/postgresql.yaml
```

### Nettoyage complet

```bash
# Supprimer tout le namespace (⚠️ Perte de données)
kubectl delete namespace airflow

# Supprimer les PVC orphelins
kubectl get pvc --all-namespaces | grep airflow
```

## 📚 Ressources

- [Documentation Apache Airflow](https://airflow.apache.org/docs/)
- [Airflow sur Kubernetes](https://airflow.apache.org/docs/apache-airflow/stable/kubernetes.html)
- [Docker Desktop Kubernetes](https://docs.docker.com/desktop/kubernetes/)

## 🔐 Sécurité

### Credentials par défaut

⚠️ **Important** : Changez les credentials par défaut en production !

- Airflow : admin / admin123
- Flower : admin / flower123  
- PostgreSQL : airflow / airflow123

### Recommandations

- Utilisez des secrets Kubernetes pour les mots de passe
- Activez HTTPS en production
- Configurez RBAC approprié
- Limitez l'accès réseau avec NetworkPolicies

## 🆘 Support

En cas de problème :

1. Vérifiez les logs avec `scripts\logs.bat [service]`
2. Consultez le statut avec `scripts\status.bat`
3. Vérifiez la documentation officielle Airflow
4. Redémarrez les services si nécessaire