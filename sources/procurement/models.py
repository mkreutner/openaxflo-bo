from django.db import models
from inventory.models import Product

class Supplier(models.Model):
    """Fournisseur de marchandises"""
    name = models.CharField("Nom du fournisseur", max_length=100)
    email = models.EmailField()
    phone = models.CharField("Téléphone", max_length=20, blank=True)
    
    # Infos Légales (pour les factures d'achat)
    tax_number = models.CharField("N° TVA Intracom.", max_length=50, blank=True)
    registration_number = models.CharField("SIRET / ID Légal", max_length=100, blank=True)
    
    # Paramètres de paiement
    payment_terms = models.CharField("Conditions de paiement", max_length=100, blank=True, help_text="Ex: 30 jours fin de mois")
    currency = models.CharField("Devise d'achat", max_length=5, default="€")

    def __str__(self):
        return self.name

class SupplierPrice(models.Model):
    """Lien entre un produit et un fournisseur avec son prix d'achat"""
    product = models.ForeignKey(
        'inventory.Product', 
        on_delete=models.CASCADE, 
        related_name='purchase_prices'
    )
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='products_supplied')
    price = models.DecimalField("Prix d'achat HT", max_digits=10, decimal_places=2)
    
    # Logistique
    lead_time_days = models.PositiveIntegerField("Délai de livraison (jours)", default=0)
    is_preferred = models.BooleanField("Fournisseur principal ?", default=False)
    
    # Historique
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Prix Fournisseur"
        verbose_name_plural = "Prix Fournisseurs"
        unique_together = ('product', 'supplier')

    def __str__(self):
        return f"{self.supplier.name} : {self.price}{self.supplier.currency} (Délai: {self.lead_time_days}j)"

class SupplierOffer(models.Model):
    """Remises spéciales accordées par le fournisseur"""
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='offers')
    description = models.CharField(max_length=200)
    discount_percent = models.DecimalField("Remise (%)", max_digits=5, decimal_places=2)
    valid_from = models.DateField("Valide du")
    valid_until = models.DateField("Valide au")
    minimum_order_quantity = models.PositiveIntegerField("Quantité mini d'achat", default=1)

    def __str__(self):
        return f"Offre {self.supplier.name} : -{self.discount_percent}%"