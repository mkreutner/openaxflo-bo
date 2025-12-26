from django.contrib import admin

# Register your models here.
from .models import Supplier, PurchasePrice

# On définit comment afficher les prix d'achat à l'intérieur d'un autre modèle
class PurchasePriceInline(admin.TabularInline):
    model = PurchasePrice
    extra = 1  # Nombre de lignes vides affichées par défaut
    fields = ('supplier', 'price', 'lead_time_days')

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'email')
    search_fields = ('name',)