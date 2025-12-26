from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from inventory.models import Product

class Customer(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Address(models.Model):
    ADDRESS_TYPES = [('BILLING', 'Billing'), ('SHIPPING', 'Shipping')]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPES)
    label = models.CharField(max_length=100, help_text="Ex: Home, Office, My Studio")
    full_address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default="France")
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.label} ({self.city})"

class Carrier(models.Model):
    name = models.CharField(max_length=100)
    base_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Coût de livraison standard par défaut"
    )
    free_shipping_threshold = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Montant de commande à partir duquel la livraison est gratuite"
    )
    is_relay_point_compatible = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.base_cost}€)"

class Order(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'), ('PAID', 'Paid'), ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'), ('CANCELLED', 'Cancelled')
    ]
    
    reference = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    
    # Adresses
    billing_address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='billed_orders')
    shipping_address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='shipped_orders', null=True, blank=True)
    
    # Transport
    carrier = models.ForeignKey(Carrier, on_delete=models.PROTECT, null=True)
    is_relay_point = models.BooleanField(default=False)
    relay_point_id = models.CharField(max_length=50, blank=True, help_text="ID of the selected relay point")
    tracking_number = models.CharField(max_length=100, blank=True)
    
    shipping_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    shipping_cost_incl_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)
    
    # Nouveau champ calculé en Django 5 pour le total des produits
    # (Note : Nécessite une logique de calcul via une méthode ou un signal car les lignes sont liées)
    
    def calculate_shipping(self):
        """Logique de calcul du coût de transport"""
        if not self.carrier:
            return Decimal('0.00')
        
        # Calcul du total des produits (HT ou TTC selon ton choix)
        order_total = sum(line.total_line_price for line in self.lines.all())
        
        # Vérification du seuil de gratuité
        if self.carrier.free_shipping_threshold and order_total >= self.carrier.free_shipping_threshold:
            return Decimal('0.00')
        
        return self.carrier.base_cost

    def clean(self):
        """
        Validation personnalisée de la commande.
        """
        super().clean()

        # 1. Vérification de l'adresse de livraison
        if self.shipping_address:
            if self.shipping_address.address_type != 'SHIPPING':
                raise ValidationError({
                    'shipping_address': "L'adresse sélectionnée pour la livraison doit être de type 'SHIPPING'."
                })
            
            # Optionnel : Vérifier que l'adresse appartient bien au client de la commande
            if self.shipping_address.customer != self.customer:
                raise ValidationError({
                    'shipping_address': "Cette adresse de livraison n'appartient pas au client sélectionné."
                })

        # 2. Vérification de l'adresse de facturation
        if self.billing_address:
            if self.billing_address.address_type != 'BILLING':
                raise ValidationError({
                    'billing_address': "L'adresse sélectionnée pour la facturation doit être de type 'BILLING'."
                })
            
            if self.billing_address.customer != self.customer:
                raise ValidationError({
                    'billing_address': "Cette adresse de facturation n'appartient pas au client sélectionné."
                })

    def get_totals(self):
        lines = self.lines.all()
        total_ht = sum(line.total_line_excl_tax for line in lines)
        total_ttc_products = sum(line.total_line_incl_tax for line in lines)
        
        # On considère que les frais de port ont aussi une TVA à 20%
        shipping_ht = self.shipping_cost_incl_tax / Decimal('1.20')
        
        grand_total_ttc = total_ttc_products + self.shipping_cost_incl_tax
        total_vat = grand_total_ttc - (total_ht + shipping_ht)
        
        return {
            'total_ht': total_ht + shipping_ht,
            'total_vat': total_vat,
            'grand_total_ttc': grand_total_ttc
        }

    def save(self, *args, **kwargs):
        # On force l'exécution de clean() car save() ne l'appelle pas automatiquement 
        # en dehors de l'interface Admin ou des ModelForms.
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference

class OrderLine(models.Model):
    order = models.ForeignKey('Order', related_name='lines', on_delete=models.CASCADE)
    product = models.ForeignKey('inventory.Product', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    
    # On stocke les valeurs au moment de la transaction
    unit_price_incl_tax = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=20.00)

    @property
    def total_line_excl_tax(self):
        price_ht = self.unit_price_incl_tax / (1 + self.vat_rate / 100)
        return (price_ht * self.quantity).quantize(Decimal('0.01'))

    @property
    def total_line_incl_tax(self):
        return self.unit_price_incl_tax * self.quantity

    @property
    def vat_amount(self):
        return self.total_line_incl_tax - self.total_line_excl_tax
    
    def clean(self):
        super().clean()
        # On vérifie si le stock est suffisant
        if self.product and self.quantity > self.product.stock_quantity:
            raise ValidationError({
                'quantity': f"Stock insuffisant pour {self.product.name}. "
                            f"Disponible : {self.product.stock_quantity}."
            })

    def save(self, *args, **kwargs):
        if not self.unit_price_incl_tax:
            self.unit_price_incl_tax = self.product.retail_price_incl_tax
        if not self.vat_rate:
            self.vat_rate = self.product.vat_rate
        self.full_clean() # Force la vérification du stock
        super().save(*args, **kwargs)
