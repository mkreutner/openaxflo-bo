import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from company.models import CompanySettings, TaxRate
from inventory.models import Product, Category, Brand
from sales.models import Customer, Address, Order, OrderLine, Carrier, CreditNote, Promotion
from procurement.models import Supplier, SupplierPrice

class Command(BaseCommand):
    help = "Génère des données de test réalistes"

    def handle(self, *args, **options):
        self.stdout.write("Génération des données...")

        # 1. Company & Taxes
        comp = CompanySettings.objects.create(
            name="Mon ERP Universel", email="contact@erp.com", 
            address="10 Rue de la Paix", zip_code="75000", city="Paris"
        )
        tva20 = TaxRate.objects.create(name="TVA 20%", rate=Decimal("20.00"), is_default=True)
        tva5 = TaxRate.objects.create(name="TVA 5.5%", rate=Decimal("5.50"))

        # 2. Inventaire Base
        brand = Brand.objects.create(name="EcoCorp")
        cat = Category.objects.create(name="Électronique")
        sub_cat = Category.objects.create(name="Gadgets", parent=cat)

        # 3. Fournisseur
        supp = Supplier.objects.create(name="Global Supplier", email="sales@global.com")

        # 4. Produits (On en crée 10)
        for i in range(1, 11):
            # 1. On crée le produit SANS le prix final pour l'instant
            p = Product.objects.create(
                name=f"Produit High-Tech {i}",
                category=sub_cat,
                brand=brand,
                tax_rate=tva20,
                retail_price=Decimal("0.00"),
                retail_price_incl_tax=Decimal("0.00"),
                margin_coefficient=Decimal("1.80"),
                stock_quantity=random.randint(10, 100)
            )

            # 2. Maintenant que 'p' a un ID, on peut créer le SupplierPrice
            SupplierPrice.objects.create(
                product=p, 
                supplier=supp, 
                price=Decimal(random.uniform(10.0, 50.0)).quantize(Decimal("0.01")),
                is_preferred=True
            )

            # 3. On appelle save() à nouveau : la PK existe, le purchase_price existe -> le calcul se fait !
            p.save()

        # 5. Clients & Transport
        carrier = Carrier.objects.create(name="DHL Express", base_cost=Decimal("12.50"))
        cust = Customer.objects.create(
            first_name="Jean", last_name="Dupont", 
            email="jean@mail.com", is_professional=True, company_name="Dupont & Co"
        )
        addr_b = Address.objects.create(customer=cust, address_type='BILLING', label="Bureau", street_address="1 av des Champs", city="Paris", postal_code="75008")
        addr_s = Address.objects.create(customer=cust, address_type='SHIPPING', label="Entrepôt", street_address="5 rue du Port", city="Lyon", postal_code="69000")

        # 6. Une Commande de test
        order = Order.objects.create(
            customer=cust, billing_address=addr_b, shipping_address=addr_s,
            carrier=carrier, shipping_tax_rate=tva20, shipping_cost=carrier.base_cost
        )
        
        # Ajout de 3 lignes de produits au hasard
        products = Product.objects.all()[:3]
        for prod in products:
            OrderLine.objects.create(order=order, product=prod, quantity=random.randint(1, 5))

        self.stdout.write(self.style.SUCCESS(f"Seed terminé ! {Product.objects.count()} produits et 1 commande créés."))

        # À ajouter à la fin de ton script seed_data.py
        # 7. Test d'une Promotion
        promo = Promotion.objects.create(
            name="Soldes d'Hiver",
            promo_type='CODE',
            code="WINTER20",
            discount_type='PERCENT',
            value=Decimal("20.00"),
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30)
        )
        promo.target_categories.add(sub_cat)

        # 8. Test d'un Avoir
        CreditNote.objects.create(
            customer=cust,
            amount=Decimal("50.00"),
            code="AVOIR-2025-001",
            expiry_date=timezone.now().date() + timezone.timedelta(days=365)
        )