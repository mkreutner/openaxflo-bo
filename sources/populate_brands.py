import os
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from inventory.models import Brand

def populate_brands():
    brands_list = [
        "Canon", "Nikon", "Sony", "Fujifilm", "Panasonic", "OM System",
        "Sigma", "Tamron", "Samyang", "Laowa", "Voigtländer",
        "Manfrotto", "Gitzo", "Benro", "Peak Design", "Lowepro", "Vanguard",
        "Godox", "Profoto", "Elinchrom", "Nanlite", "Aputure",
        "SanDisk", "Lexar", "Epson", "Ilford", "Kodak", "Leica", "Hasselblad"
    ]

    print("Importation des marques en cours...")
    for brand_name in brands_list:
        obj, created = Brand.objects.get_or_create(name=brand_name)
        if created:
            print(f"✔️ Marque ajoutée : {brand_name}")
        else:
            print(f"🟡 Marque déjà existante : {brand_name}")

if __name__ == "__main__":
    populate_brands()
    print("Terminé !")