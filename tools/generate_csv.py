import csv
import random
import uuid
from datetime import datetime, timedelta
from faker import Faker
import os
import sys

fake = Faker('fr_FR')

VILLES = ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nice', 'Nantes', 'Strasbourg', 'Montpellier', 'Bordeaux', 'Lille']
DEPARTEMENTS = ['IT', 'RH', 'Marketing', 'Finance', 'Commercial', 'Production', 'Logistique', 'R&D']
STATUTS = ['actif', 'inactif']
NIVEAUX = ['junior', 'senior', 'expert']
CATEGORIES = ['A', 'B', 'C']

def clean_field(value):
    """Nettoie un champ pour éviter les problèmes avec le délimiteur CSV"""
    if isinstance(value, str):
        return value.replace(';', ',').replace('\n', ' ').replace('\r', ' ')
    return value

def generate_row(row_id):
    """Génère une ligne de données CSV"""
    base_date = datetime(2020, 1, 1)
    random_days = random.randint(0, 1460)
    date_embauche = base_date + timedelta(days=random_days)
    
    return [
        row_id,
        clean_field(fake.last_name()),
        clean_field(fake.first_name()),
        clean_field(fake.email()),
        random.randint(18, 65),
        clean_field(random.choice(VILLES)),
        clean_field(fake.postcode()),
        clean_field(fake.phone_number()),
        round(random.uniform(25000, 80000), 2),
        clean_field(random.choice(DEPARTEMENTS)),
        date_embauche.strftime('%Y-%m-%d'),
        clean_field(random.choice(STATUTS)),
        round(random.uniform(0, 100), 2),
        round(random.uniform(42.0, 51.0), 6),
        round(random.uniform(-5.0, 8.0), 6),
        clean_field(fake.text(max_nb_chars=100)),
        clean_field(str(uuid.uuid4())),
        clean_field(random.choice(NIVEAUX)),
        clean_field(random.choice(CATEGORIES)),
        clean_field(datetime.now().isoformat())
    ]

def estimate_rows_needed(target_size_mb):
    """Estime le nombre de lignes nécessaires pour atteindre la taille cible"""
    sample_row = generate_row(1)
    sample_line = ';'.join(map(str, sample_row)) + '\n'
    avg_row_size = len(sample_line.encode('utf-8'))
    target_size_bytes = target_size_mb * 1024 * 1024
    estimated_rows = int(target_size_bytes / avg_row_size)
    print(f"Taille moyenne d'une ligne: {avg_row_size} bytes")
    print(f"Nombre estimé de lignes nécessaires: {estimated_rows:,}")
    return estimated_rows

def generate_csv_file(filename, target_size_mb, unit='MB'):
    """Génère un fichier CSV de la taille spécifiée"""
    if unit == 'GB':
        print(f"Génération de {filename} ({target_size_mb}GB)...")
        target_size_bytes = target_size_mb * 1024 * 1024 * 1024
        estimated_rows = estimate_rows_needed(target_size_mb * 1024)
    else:
        print(f"Génération de {filename} ({target_size_mb}MB)...")
        target_size_bytes = target_size_mb * 1024 * 1024
        estimated_rows = estimate_rows_needed(target_size_mb)
    
    # En-têtes
    headers = ['id', 'nom', 'prenom', 'email', 'age', 'ville', 'code_postal', 
               'telephone', 'salaire', 'departement', 'date_embauche', 'statut',
               'score', 'latitude', 'longitude', 'commentaire', 'reference',
               'niveau', 'categorie', 'timestamp']
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(headers)
        
        current_size = os.path.getsize(filename)
        row_id = 1
        
        while current_size < target_size_bytes:
            batch_size = min(10000, estimated_rows - row_id + 1)
            rows_batch = []
            
            for _ in range(batch_size):
                rows_batch.append(generate_row(row_id))
                row_id += 1
            
            writer.writerows(rows_batch)
            current_size = os.path.getsize(filename)
            
            if row_id % 50000 == 0:
                progress = (current_size / target_size_bytes) * 100
                if unit == 'GB':
                    print(f"Progression: {progress:.1f}% - {current_size / (1024*1024*1024):.2f}GB - {row_id:,} lignes")
                else:
                    print(f"Progression: {progress:.1f}% - {current_size / (1024*1024):.2f}MB - {row_id:,} lignes")
    
    final_size = os.path.getsize(filename)
    if unit == 'GB':
        final_size_display = final_size / (1024 * 1024 * 1024)
        print(f"Fichier {filename} généré: {final_size_display:.2f}GB avec {row_id:,} lignes")
    else:
        final_size_display = final_size / (1024 * 1024)
        print(f"Fichier {filename} généré: {final_size_display:.2f}MB avec {row_id:,} lignes")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_csv.py <1|5|5MB>")
        print("1 = génère un fichier de 1GB")
        print("5 = génère un fichier de 5GB")
        print("5MB = génère un fichier de 5MB")
        sys.exit(1)
    
    # Créer le dossier data s'il n'existe pas
    os.makedirs('data', exist_ok=True)
    
    arg = sys.argv[1]
    if arg == "1":
        generate_csv_file('data/employees_1gb.csv', 1, 'GB')
    elif arg == "5":
        generate_csv_file('data/employees_5gb.csv', 5, 'GB')
    elif arg == "5MB":
        generate_csv_file('data/employees_5mb.csv', 5, 'MB')
    else:
        print("Taille non supportée. Utilisez 1, 5 ou 5MB.")