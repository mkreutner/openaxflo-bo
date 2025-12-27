from django.db import models

class TaxRate(models.Model):
    """Gère les différents taux de taxe (TVA) applicables."""
    name = models.CharField("Nom de la taxe", max_length=50, help_text="Ex: TVA Standard")
    rate = models.DecimalField("Taux (%)", max_digits=5, decimal_places=2)
    is_default = models.BooleanField("Taux par défaut", default=False)

    class Meta:
        verbose_name = "Taux de TVA"
        verbose_name_plural = "Taux de TVA"

    def __str__(self):
        return f"{self.name} ({self.rate}%)"

class CompanySettings(models.Model):
    """Configuration globale de l'entreprise (Marque blanche)."""
    name = models.CharField("Nom de l'entreprise", max_length=200)
    logo = models.ImageField(upload_to='company/', blank=True, null=True)
    email = models.EmailField("Email de contact")
    phone = models.CharField("Téléphone", max_length=20, blank=True)
    
    # Identifiants Légaux (Universel)
    tax_number = models.CharField("Numéro de TVA Intracom.", max_length=50, null=True, blank=True)
    registration_number = models.CharField("SIRET / Registration ID", max_length=100, blank=True)
    legal_mention = models.TextField("Mentions légales (Pied de facture)", blank=True, help_text="Ex: SARL au capital de...")

    # Adresse du siège
    address = models.TextField("Adresse")
    zip_code = models.CharField("Code Postal", max_length=20)
    city = models.CharField("Ville", max_length=100)
    country = models.CharField("Pays", max_length=100, default="France")

    # Paramètres Financiers
    currency_symbol = models.CharField("Symbole Monétaire", max_length=5, default="€")
    default_tax = models.ForeignKey(
        TaxRate, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Taxe par défaut"
    )

    class Meta:
        verbose_name = "Paramètres Entreprise"
        verbose_name_plural = "Paramètres Entreprise"

    def __str__(self):
        return self.name