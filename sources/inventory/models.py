from django.db import models
from decimal import Decimal
from django.utils.translation import gettext_lazy as _

class Category(models.Model):
    name = models.CharField(_("Name"), max_length=100)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='children'
    )
    slug = models.SlugField(unique=True, null=True, blank=True, help_text="URL friendly name")

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        full_path = [self.name]
        k = self.parent
        while k is not None:
            full_path.append(k.name)
            k = k.parent
        return ' > '.join(reversed(full_path))

class Brand(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True)
    
    # --- Liaison avec l'application Company ---
    tax_rate = models.ForeignKey(
        'company.TaxRate', 
        on_delete=models.PROTECT, 
        verbose_name="Taux de taxe applicable",
        help_text="Sélectionnez le taux de TVA pour ce produit"
    )
    
    retail_price = models.DecimalField("Prix HT", max_digits=10, decimal_places=2)
    retail_price_incl_tax = models.DecimalField("Prix TTC", max_digits=10, decimal_places=2, default=0.00)
    
    margin_coefficient = models.DecimalField("Coeff. Marge", max_digits=4, decimal_places=2, default=1.50)
    stock_quantity = models.PositiveIntegerField("Stock disponible", default=0)
    low_stock_threshold = models.PositiveIntegerField("Seuil d'alerte", default=5)

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0

    @property
    def needs_reorder(self):
        return self.stock_quantity <= self.low_stock_threshold
    
    def save(self, *args, **kwargs):
        # On définit le multiplicateur de taxe dès le début (toujours dispo via FK tax_rate)
        tax_multiplier = 1 + (self.tax_rate.rate / 100)

        # 1. LOGIQUE DE CALCUL VIA MARGE (Seulement si l'objet existe déjà en base)
        if self.pk and self.retail_price_incl_tax == Decimal('0.00'):
            # Utilisation de getattr pour la sécurité de la relation inversée
            purchase_prices = getattr(self, 'purchase_prices', None)
            if purchase_prices and purchase_prices.exists():
                purchase_price_ht = purchase_prices.first().price
                # Calcul : HT Achat * Marge * TVA
                calculated_ttc = purchase_price_ht * self.margin_coefficient * tax_multiplier
                self.retail_price_incl_tax = calculated_ttc.quantize(Decimal('0.01'))

        # 2. SYNCHRONISATION HT / TTC
        # Cas A : On a le TTC mais pas le HT
        if self.retail_price_incl_tax and not self.retail_price:
            self.retail_price = (self.retail_price_incl_tax / tax_multiplier).quantize(Decimal('0.01'))
        
        # Cas B : On a le HT mais pas encore le TTC (ou TTC à zéro)
        elif self.retail_price and (not self.retail_price_incl_tax or self.retail_price_incl_tax == Decimal('0.00')):
            self.retail_price_incl_tax = (self.retail_price * tax_multiplier).quantize(Decimal('0.01'))
            
        # Cas C : RE-CALCUL DE SÉCURITÉ (Les deux sont là, on synchronise sur le HT)
        # Indispensable si on change la TVA ou le HT manuellement
        elif self.retail_price and self.retail_price_incl_tax:
            self.retail_price_incl_tax = (self.retail_price * tax_multiplier).quantize(Decimal('0.01'))

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.retail_price_incl_tax}€ TTC)"