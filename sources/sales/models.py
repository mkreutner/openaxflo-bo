from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

# -------------------------------------------------------------------
# CLIENTS ET ADRESSES
# -------------------------------------------------------------------

class Customer(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Champs B2B pour l'universalité
    is_professional = models.BooleanField("Est une entreprise ?", default=False)
    company_name = models.CharField("Nom de la société", max_length=200, blank=True, null=True)
    vat_number = models.CharField("N° TVA Intracom.", max_length=50, blank=True, null=True)
    
    def __str__(self):
        if self.is_professional and self.company_name:
            return f"{self.company_name} ({self.last_name})"
        return f"{self.first_name} {self.last_name}"

class Address(models.Model):
    ADDRESS_TYPES = [('BILLING', 'Billing'), ('SHIPPING', 'Shipping')]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPES)
    label = models.CharField(max_length=100, help_text="Ex: Home, Office, My Studio")
    
    street_address = models.CharField("Street and Number", max_length=255)
    address_line_2 = models.CharField("Apartment, unit, etc.", max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default="France")
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.label} - {self.street_address}, {self.city}"

# -------------------------------------------------------------------
# TRANSPORT ET LOGISTIQUE
# -------------------------------------------------------------------

class Carrier(models.Model):
    name = models.CharField(max_length=100)
    base_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    free_shipping_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_relay_point_compatible = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.base_cost}€)"

# -------------------------------------------------------------------
# MARKETING ET FIDELITÉ
# -------------------------------------------------------------------

class Promotion(models.Model):
    PROMO_TYPES = [
        ('CODE', 'Promo Code (Coupon)'),
        ('BRAND_OFFER', 'Brand Promotion'),
        ('STORE_WIDE', 'Store-wide Sale'),
    ]
    DISCOUNT_TYPES = [('PERCENT', '%'), ('FIXED', '€')]

    name = models.CharField(max_length=100)
    promo_type = models.CharField(max_length=20, choices=PROMO_TYPES)
    code = models.CharField(max_length=50, blank=True, null=True, unique=True)
    
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    active = models.BooleanField(default=True)

    # Ciblage et Exclusions
    target_brands = models.ManyToManyField('inventory.Brand', blank=True)
    target_categories = models.ManyToManyField('inventory.Category', blank=True)
    target_products = models.ManyToManyField('inventory.Product', blank=True, related_name='included_in_promos')
    excluded_categories = models.ManyToManyField('inventory.Category', blank=True, related_name='excluded_from_promos')
    excluded_products = models.ManyToManyField('inventory.Product', blank=True, related_name='excluded_from_promos')

    def is_valid(self):
        now = timezone.now()
        return self.active and self.start_date <= now <= self.end_date
    
    def is_applicable_to_product(self, product):
        if not self.is_valid(): return False
        if product in self.excluded_products.all(): return False
        if product.category in self.excluded_categories.all(): return False
        
        has_targets = self.target_products.exists() or self.target_brands.exists() or self.target_categories.exists()
        if has_targets:
            return (product in self.target_products.all() or 
                    product.brand in self.target_brands.all() or 
                    product.category in self.target_categories.all())
        return True

class CreditNote(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    code = models.CharField(max_length=20, unique=True)
    is_used = models.BooleanField(default=False)
    expiry_date = models.DateField()

    def is_valid(self):
        return not self.is_used and self.expiry_date >= timezone.now().date()

    def __str__(self):
        return f"Avoir {self.code} ({self.amount}€)"

# -------------------------------------------------------------------
# COMMANDES ET LIGNES
# -------------------------------------------------------------------

class Order(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'), ('PAID', 'Paid'), ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'), ('CANCELLED', 'Cancelled')
    ]
    
    reference = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    
    billing_address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='billed_orders')
    shipping_address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='shipped_orders', null=True, blank=True)
    
    carrier = models.ForeignKey(Carrier, on_delete=models.PROTECT, null=True)
    is_relay_point = models.BooleanField(default=False)
    relay_point_id = models.CharField(max_length=50, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_tax_rate = models.ForeignKey('company.TaxRate', on_delete=models.PROTECT, null=True)

    applied_promotion = models.ForeignKey(Promotion, on_delete=models.SET_NULL, null=True, blank=True)
    applied_credit_note = models.OneToOneField(CreditNote, on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)
    
    def calculate_discount(self):
        discount = Decimal('0.00')
        total_products = sum(line.total_line_incl_tax for line in self.lines.all())
        if self.applied_promotion and self.applied_promotion.is_valid():
            if self.applied_promotion.discount_type == 'PERCENT':
                discount += (total_products * self.applied_promotion.value / 100)
            else:
                discount += self.applied_promotion.value
        if self.applied_credit_note and not self.applied_credit_note.is_used:
            discount += self.applied_credit_note.amount
        return discount
    
    def calculate_automatic_discounts(self):
        total_discount = Decimal('0.00')
        auto_promos = Promotion.objects.filter(active=True, code__isnull=True, 
                                             start_date__lte=timezone.now(), end_date__gte=timezone.now())
        for line in self.lines.all():
            for promo in auto_promos:
                if promo.is_applicable_to_product(line.product):
                    if promo.discount_type == 'PERCENT':
                        total_discount += (line.total_line_incl_tax * promo.value / 100)
                    else:
                        total_discount += (promo.value * line.quantity)
                    break
        return total_discount

    def calculate_shipping(self):
        """Logique de calcul du coût de transport"""
        if not self.carrier:
            return Decimal('0.00')
        
        # Correction ici : on utilise total_line_incl_tax au lieu de total_line_price
        order_total_ttc = sum(line.total_line_incl_tax for line in self.lines.all())
        
        # Vérification du seuil de gratuité
        if self.carrier.free_shipping_threshold and order_total_ttc >= self.carrier.free_shipping_threshold:
            return Decimal('0.00')
        
        return self.carrier.base_cost

    def clean(self):
        super().clean()
        if self.shipping_address and (self.shipping_address.address_type != 'SHIPPING' or self.shipping_address.customer != self.customer):
            raise ValidationError({'shipping_address': "Adresse de livraison invalide."})
        if self.billing_address and (self.billing_address.address_type != 'BILLING' or self.billing_address.customer != self.customer):
            raise ValidationError({'billing_address': "Adresse de facturation invalide."})

    def get_totals(self):
        lines = self.lines.all()
        total_ht = sum(line.total_line_excl_tax for line in lines)
        total_ttc_products = sum(line.total_line_incl_tax for line in lines)
        
        tax_rate_val = self.shipping_tax_rate.rate if self.shipping_tax_rate else Decimal('20.00')
        shipping_ttc = self.shipping_cost * (1 + tax_rate_val / 100)
        
        grand_total_ttc = total_ttc_products + shipping_ttc - self.discount_amount
        total_vat = grand_total_ttc - (total_ht + self.shipping_cost)
        
        return {
            'total_ht': (total_ht + self.shipping_cost).quantize(Decimal('0.01')),
            'total_vat': total_vat.quantize(Decimal('0.01')),
            'grand_total_ttc': grand_total_ttc.quantize(Decimal('0.01'))
        }

    def save(self, *args, **kwargs):
        if not self.reference:
            last_order = Order.objects.all().last()
            new_id = (last_order.id + 1) if last_order else 1
            self.reference = f"DP-{timezone.now().year}-{new_id:04d}"
        self.full_clean()
        super().save(*args, **kwargs)

class OrderLine(models.Model):
    order = models.ForeignKey(Order, related_name='lines', on_delete=models.CASCADE)
    product = models.ForeignKey('inventory.Product', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    
    unit_price_incl_tax = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField("Taux TVA (%)", max_digits=5, decimal_places=2)

    @property
    def total_line_excl_tax(self):
        price_ht = self.unit_price_incl_tax / (1 + self.vat_rate / 100)
        return (price_ht * self.quantity).quantize(Decimal('0.01'))

    @property
    def total_line_incl_tax(self):
        return self.unit_price_incl_tax * self.quantity

    @property
    def total_line_price(self):
        """Alias de confort pour pointer vers le TTC par défaut"""
        return self.total_line_incl_tax

    def clean(self):
        super().clean()
        if self.product and self.quantity > self.product.stock_quantity:
            raise ValidationError({'quantity': f"Stock insuffisant ({self.product.stock_quantity})."})

    def save(self, *args, **kwargs):
        if not self.unit_price_incl_tax:
            self.unit_price_incl_tax = self.product.retail_price_incl_tax
        if not self.vat_rate:
            self.vat_rate = self.product.tax_rate.rate
        self.full_clean()
        super().save(*args, **kwargs)
