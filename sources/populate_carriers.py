import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from sales.models import Carrier

carriers = [
    {'name': 'Chronopost 24h', 'relay': False},
    {'name': 'Colissimo Domicile', 'relay': False},
    {'name': 'Mondial Relay', 'relay': True},
    {'name': 'UPS Express', 'relay': False},
]

for c in carriers:
    Carrier.objects.get_or_create(name=c['name'], is_relay_point_compatible=c['relay'])
