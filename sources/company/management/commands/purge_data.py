from django.core.management.base import BaseCommand
from company.models import CompanySettings, TaxRate
from inventory.models import Product, Category, Brand
from sales.models import Customer, Address, Order, OrderLine, Carrier, Promotion, CreditNote
from procurement.models import Supplier, SupplierPrice

class Command(BaseCommand):
    help = "Purge toutes les données de l'ERP"

    def handle(self, *args, **options):
        self.stdout.write("Purge en cours...")
        
        # Ordre inverse des dépendances
        OrderLine.objects.all().delete()
        Order.objects.all().delete()
        CreditNote.objects.all().delete()
        Promotion.objects.all().delete()
        Address.objects.all().delete()
        Customer.objects.all().delete()
        SupplierPrice.objects.all().delete()
        Supplier.objects.all().delete()
        Product.objects.all().delete()
        Brand.objects.all().delete()
        Category.objects.all().delete()
        TaxRate.objects.all().delete()
        CompanySettings.objects.all().delete()
        Carrier.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("Base de données nettoyée avec succès !"))