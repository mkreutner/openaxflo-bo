from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils.translation import gettext_lazy as _

# Inventory models.
class Category(models.Model):
    name = models.CharField(_("Name"), max_length=100)
    # 'self' permet de lier une catégorie à une autre catégorie
    # null=True permet d'avoir des catégories racines (niveau 1)
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
        # Affiche le chemin complet : "Électronique > Téléphones > Smartphones"
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
    retail_price = models.DecimalField(max_digits=10, decimal_places=2)
    retail_price_incl_tax = models.DecimalField("Prix TTC", max_digits=10, decimal_places=2, default=0.00)
    vat_rate = models.DecimalField("Taux TVA (%)", max_digits=5, decimal_places=2, default=20.00)
    # On peut ajouter un coefficient de marge par défaut par produit
    margin_coefficient = models.DecimalField("Coeff. Marge", max_digits=4, decimal_places=2, default=1.50)
    stock_quantity = models.PositiveIntegerField("Stock disponible", default=0)
    low_stock_threshold = models.PositiveIntegerField("Seuil d'alerte", default=5)

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0

    @property
    def needs_reorder(self):
        return self.stock_quantity <= self.low_stock_threshold

    @property
    def retail_price_excl_tax(self):
        """Calcule le prix HT à la volée pour l'affichage"""
        return (self.retail_price_incl_tax / (1 + self.vat_rate / 100)).quantize(Decimal('0.01'))
    
    def save(self, *args, **kwargs):
        # Si le prix de vente est à 0, on essaie de le calculer
        if self.retail_price_incl_tax == Decimal('0.00'):
            # On cherche le prix d'achat (lié via related_name='purchase_prices' dans procurement)
            # .first() récupère le premier prix d'achat enregistré
            purchase_entry = self.purchase_prices.first()
            
            if purchase_entry:
                purchase_price_ht = purchase_entry.price
                # Calcul : Prix d'achat HT * Marge * TVA
                calculated_price = purchase_price_ht * self.margin_coefficient * (1 + self.vat_rate / 100)
                self.retail_price_incl_tax = calculated_price.quantize(Decimal('0.01'))
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.retail_price_incl_tax}€ TTC)"
