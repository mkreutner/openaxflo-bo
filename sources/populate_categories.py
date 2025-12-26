import os
import django
from django.utils.text import slugify

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from inventory.models import Category

def populate():
    # Structure complète basée sur l'arborescence Digit-Photo
    catalog_structure = {
    "PHOTO & VIDEO": {
        "Cameras": ["Mirrorless", "DSLR", "Compact & Bridge", "Film Cameras", "Instant"],
        "Lenses": ["Prime Lenses", "Zoom Lenses", "Macro Lenses", "Lens Adapters"],
        "Video & Cinema": ["Camcorders", "Gimbals", "Recorders", "Monitors"],
    },
    "ACCESSORIES": {
        "Tripods & Supports": ["Photo Tripods", "Monopods", "Ball Heads", "Accessories"],
        "Bags & Transport": ["Backpacks", "Shoulder Bags", "Hard Cases", "Pouches"],
        "Filters & Optics": ["Polarizing", "ND Filters", "Filter Holders", "Cleaning Kits"],
    },
    "LIGHTING & STUDIO": {
        "Flashes & Light": ["Speedlights", "LED Lights", "Studio Strobes", "Transmitters"],
        "Modifiers": ["Softboxes", "Umbrellas", "Reflectors", "Barn Doors"],
        "Studio Gear": ["Backgrounds", "Background Supports", "Light Stands"],
    },
    "LAB & PRINTING": {
        "Printing": ["Photo Printers", "Photo Paper", "Ink Cartridges"],
        "Analog Lab": ["Film Rolls", "Chemicals", "Darkroom Gear", "Scanners"],
    },
    "OBSERVATION": {
        "Binoculars": ["Nature Binoculars", "Astronomy Binoculars"],
        "Spotting Scopes": ["Observation", "Digiscoping"],
    }
}

    for lvl1, lvl2_content in catalog_structure.items():
        # Création Niveau 1 (Univers)
        parent_l1, _ = Category.objects.get_or_create(
            name=lvl1, 
            parent=None,
            defaults={'slug': slugify(lvl1)}
        )
        print(f"✔️ Univers : {lvl1}")

        for lvl2, lvl3_list in lvl2_content.items():
            # Création Niveau 2 (Rayon)
            parent_l2, _ = Category.objects.get_or_create(
                name=lvl2, 
                parent=parent_l1,
                defaults={'slug': slugify(f"{lvl1}-{lvl2}")}
            )
            print(f"  > Rayon : {lvl2}")

            for lvl3 in lvl3_list:
                # Création Niveau 3 (Famille)
                Category.objects.get_or_create(
                    name=lvl3, 
                    parent=parent_l2,
                    defaults={'slug': slugify(f"{lvl2}-{lvl3}")}
                )
                print(f"    - Famille : {lvl3}")

if __name__ == "__main__":
    populate()