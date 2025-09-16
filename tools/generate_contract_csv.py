import csv
import random
import uuid
from datetime import datetime, timedelta
from faker import Faker
import os
import sys
import logging
from typing import List, Any

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

fake = Faker('fr_FR')

# Constantes conformes au framework GCP Data Lakehouse
TYPES_CONTRAT = ['CDI', 'CDD', 'Stage', 'Freelance', 'Prestation', 'Consultant']
STATUTS_CONTRAT = ['actif', 'expire', 'suspendu', 'resilié', 'en_cours', 'signe']
DEPARTEMENTS = ['IT', 'RH', 'Marketing', 'Finance', 'Commercial', 'Production', 'Logistique', 'R&D', 'Direction', 'Support']
PRIORITES = ['haute', 'moyenne', 'basse', 'critique']
DEVISES = ['EUR', 'USD', 'GBP']

# Schéma conforme au framework médaillon (ordre et types respectés)
SCHEMA_ODS = {
    'contract_id': {'type': 'INT64', 'required': True, 'min_val': 1},
    'numero_contrat': {'type': 'STRING', 'max_length': 50},
    'nom_client': {'type': 'STRING', 'max_length': 100},
    'entreprise': {'type': 'STRING', 'max_length': 100},
    'email_contact': {'type': 'STRING', 'max_length': 100},
    'type_contrat': {'type': 'STRING', 'max_length': 20},
    'departement': {'type': 'STRING', 'max_length': 50},
    'montant_total': {'type': 'FLOAT64', 'min_val': 1000.0, 'max_val': 5000000.0},
    'devise': {'type': 'STRING', 'max_length': 3},
    'date_signature': {'type': 'DATE', 'min_date': '2020-01-01', 'max_date': '2024-12-31'},
    'date_debut': {'type': 'DATE', 'min_date': '2020-01-01', 'max_date': '2024-12-31'},
    'date_fin': {'type': 'DATE', 'min_date': '2020-01-01', 'max_date': '2025-12-31'},
    'duree_mois': {'type': 'INT64', 'min_val': 1, 'max_val': 60},
    'statut': {'type': 'STRING', 'max_length': 20},
    'priorite': {'type': 'STRING', 'max_length': 15},
    'description': {'type': 'STRING', 'max_length': 500},
    'referent_interne': {'type': 'STRING', 'max_length': 100},
    'montant_mensuel': {'type': 'FLOAT64', 'min_val': 100.0, 'max_val': 500000.0},
    'pourcentage_completion': {'type': 'FLOAT64', 'min_val': 0.0, 'max_val': 100.0},
    'timestamp': {'type': 'TIMESTAMP'}
}

def clean_field(value: Any, max_length: int = None) -> str:
    """
    Nettoie un champ pour éviter les problèmes avec le délimiteur CSV.
    Conforme aux standards du framework GCP Data Lakehouse.
    """
    if value is None:
        return ''

    if isinstance(value, str):
        # Nettoyer les caractères problématiques
        cleaned = value.replace(';', ',').replace('\n', ' ').replace('\r', ' ').strip()
        # Appliquer la limite de longueur si spécifiée
        if max_length and len(cleaned) > max_length:
            cleaned = cleaned[:max_length]
        return cleaned

    return str(value)

def validate_field(field_name: str, value: Any) -> Any:
    """
    Valide un champ selon le schéma ODS défini.
    Conforme aux standards BigQuery.
    """
    if field_name not in SCHEMA_ODS:
        logger.warning(f"Champ non reconnu dans le schéma ODS: {field_name}")
        return value

    schema = SCHEMA_ODS[field_name]
    field_type = schema.get('type')

    try:
        # Validation selon le type BigQuery
        if field_type == 'INT64':
            int_val = int(value)
            if 'min_val' in schema and int_val < schema['min_val']:
                int_val = schema['min_val']
            if 'max_val' in schema and int_val > schema['max_val']:
                int_val = schema['max_val']
            return int_val

        elif field_type == 'FLOAT64':
            float_val = float(value)
            if 'min_val' in schema and float_val < schema['min_val']:
                float_val = schema['min_val']
            if 'max_val' in schema and float_val > schema['max_val']:
                float_val = schema['max_val']
            return round(float_val, 2)

        elif field_type == 'STRING':
            max_length = schema.get('max_length')
            return clean_field(str(value), max_length)

        elif field_type in ['DATE', 'TIMESTAMP']:
            return str(value)

        else:
            return clean_field(str(value))

    except (ValueError, TypeError) as e:
        logger.error(f"Erreur de validation pour {field_name}: {e}")
        return None

def generate_row(row_id: int) -> List[Any]:
    """
    Génère une ligne de données CSV conforme au schéma ODS contract.
    Respecte exactement l'ordre des colonnes du schéma.
    """
    try:
        # Dates cohérentes pour le contrat
        date_signature = fake.date_between(start_date='-4y', end_date='today')
        date_debut = date_signature + timedelta(days=random.randint(1, 30))
        duree_mois = random.randint(1, 48)
        date_fin = date_debut + timedelta(days=duree_mois * 30)

        # Montants cohérents
        montant_total = round(random.uniform(5000, 2000000), 2)
        montant_mensuel = round(montant_total / duree_mois, 2)

        # Génération des données dans l'ordre exact du schéma ODS
        raw_data = {
            'contract_id': row_id,
            'numero_contrat': f"CTR-{date_signature.year}-{row_id:06d}",
            'nom_client': fake.name(),
            'entreprise': fake.company(),
            'email_contact': fake.email(),
            'type_contrat': random.choice(TYPES_CONTRAT),
            'departement': random.choice(DEPARTEMENTS),
            'montant_total': montant_total,
            'devise': random.choice(DEVISES),
            'date_signature': date_signature.strftime('%Y-%m-%d'),
            'date_debut': date_debut.strftime('%Y-%m-%d'),
            'date_fin': date_fin.strftime('%Y-%m-%d'),
            'duree_mois': duree_mois,
            'statut': random.choice(STATUTS_CONTRAT),
            'priorite': random.choice(PRIORITES),
            'description': fake.text(max_nb_chars=400),
            'referent_interne': fake.name(),
            'montant_mensuel': montant_mensuel,
            'pourcentage_completion': round(random.uniform(0, 100), 1),
            'timestamp': datetime.now().isoformat()
        }

        # Validation et nettoyage de chaque champ
        validated_row = []
        for field_name in SCHEMA_ODS.keys():
            validated_value = validate_field(field_name, raw_data[field_name])
            if validated_value is None:
                logger.error(f"Validation échouée pour {field_name} à la ligne {row_id}")
                validated_value = ''
            validated_row.append(validated_value)

        return validated_row

    except Exception as e:
        logger.error(f"Erreur lors de la génération de la ligne {row_id}: {e}")
        # Ligne de fallback avec valeurs par défaut
        return [row_id, f'CTR-2023-{row_id:06d}', '', '', '', 'CDI', 'IT',
                50000.0, 'EUR', '2023-01-01', '2023-02-01', '2024-02-01', 12,
                'actif', 'moyenne', '', '', 4166.67, 50.0, datetime.now().isoformat()]

def estimate_rows_needed(target_size_mb):
    """Estime le nombre de lignes nécessaires pour atteindre la taille cible"""
    sample_row = generate_row(1)
    sample_line = ';'.join(map(str, sample_row)) + '\n'
    avg_row_size = len(sample_line.encode('utf-8'))
    target_size_bytes = target_size_mb * 1024 * 1024
    estimated_rows = int(target_size_bytes / avg_row_size)
    logger.info(f"Taille moyenne d'une ligne: {avg_row_size} bytes")
    logger.info(f"Nombre estimé de lignes nécessaires: {estimated_rows:,}")
    return estimated_rows

def generate_csv_file(filename: str, target_size_mb: float, unit: str = 'MB') -> bool:
    """
    Génère un fichier CSV de la taille spécifiée.
    Conforme au framework GCP Data Lakehouse avec gestion d'erreurs robuste.

    Args:
        filename: Nom du fichier à générer
        target_size_mb: Taille cible (en MB ou GB selon unit)
        unit: 'MB' ou 'GB'

    Returns:
        bool: True si succès, False sinon
    """
    try:
        logger.info(f"🚀 Génération de {filename} ({target_size_mb}{unit}) - Framework GCP Data Lakehouse")

        if unit == 'GB':
            target_size_bytes = target_size_mb * 1024 * 1024 * 1024
            estimated_rows = estimate_rows_needed(target_size_mb * 1024)
        else:
            target_size_bytes = target_size_mb * 1024 * 1024
            estimated_rows = estimate_rows_needed(target_size_mb)

        # En-têtes conformes au schéma ODS (ordre exact)
        headers = list(SCHEMA_ODS.keys())

        # Validation des headers
        logger.info(f"📋 Schéma ODS: {len(headers)} colonnes conformes au framework médaillon")

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=';', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(headers)

            current_size = os.path.getsize(filename)
            row_id = 1
            error_count = 0

            while current_size < target_size_bytes:
                batch_size = min(10000, estimated_rows - row_id + 1)
                rows_batch = []

                for _ in range(batch_size):
                    try:
                        row_data = generate_row(row_id)
                        if row_data and len(row_data) == len(headers):
                            rows_batch.append(row_data)
                        else:
                            error_count += 1
                            logger.warning(f"⚠️ Ligne {row_id} invalide, ignorée")
                    except Exception as e:
                        error_count += 1
                        logger.error(f"❌ Erreur génération ligne {row_id}: {e}")

                    row_id += 1

                if rows_batch:
                    writer.writerows(rows_batch)
                    current_size = os.path.getsize(filename)

                # Progress reporting
                if row_id % 50000 == 0:
                    progress = (current_size / target_size_bytes) * 100
                    size_display = current_size / (1024*1024*1024) if unit == 'GB' else current_size / (1024*1024)
                    unit_display = 'GB' if unit == 'GB' else 'MB'

                    logger.info(f"⏳ Progression: {progress:.1f}% - {size_display:.2f}{unit_display} - {row_id:,} lignes - {error_count} erreurs")

        # Validation finale
        final_size = os.path.getsize(filename)
        final_size_display = final_size / (1024 * 1024 * 1024) if unit == 'GB' else final_size / (1024 * 1024)
        unit_display = 'GB' if unit == 'GB' else 'MB'

        logger.info(f"✅ Fichier {filename} généré avec succès:")
        logger.info(f"   📊 Taille: {final_size_display:.2f}{unit_display}")
        logger.info(f"   📈 Lignes: {row_id:,}")
        logger.info(f"   🔍 Erreurs: {error_count}")
        logger.info(f"   📋 Conforme au schéma ODS contract")

        return True

    except Exception as e:
        logger.error(f"❌ Erreur critique lors de la génération de {filename}: {e}")
        return False

if __name__ == "__main__":
    logger.info("🏗️ Générateur CSV Contract - Framework GCP Data Lakehouse")
    logger.info("📋 Conforme à l'architecture médaillon Bronze → Silver → Gold")

    if len(sys.argv) != 2:
        print("Usage: python generate_contract_csv.py <1|5|5MB>")
        print("  1    = génère contract_1gb.csv (1GB)")
        print("  5    = génère contract_5gb.csv (5GB)")
        print("  5MB  = génère contract_5mb.csv (5MB)")
        print("\n🔍 Conformité Framework GCP Data Lakehouse:")
        print(f"  • Schéma: {len(SCHEMA_ODS)} colonnes ODS")
        print("  • Validation: Types BigQuery respectés")
        print("  • Nettoyage: Délimiteurs CSV sécurisés")
        print("  • Logging: Suivi des erreurs détaillé")
        sys.exit(1)

    # Créer le dossier data s'il n'existe pas
    data_dir = 'data'
    os.makedirs(data_dir, exist_ok=True)
    logger.info(f"📁 Répertoire de sortie: {os.path.abspath(data_dir)}")

    arg = sys.argv[1]
    success = False

    if arg == "1":
        success = generate_csv_file('data/contract_1gb.csv', 1, 'GB')
    elif arg == "5":
        success = generate_csv_file('data/contract_5gb.csv', 5, 'GB')
    elif arg == "5MB":
        success = generate_csv_file('data/contract_5mb.csv', 5, 'MB')
    else:
        logger.error(f"❌ Taille non supportée: {arg}")
        logger.info("✅ Tailles supportées: 1, 5, 5MB")
        sys.exit(1)

    if success:
        logger.info("🎉 Génération terminée avec succès!")
        logger.info("📋 Fichier prêt pour ingestion BigQuery (Pattern médaillon)")
        sys.exit(0)
    else:
        logger.error("💥 Échec de la génération")
        sys.exit(1)