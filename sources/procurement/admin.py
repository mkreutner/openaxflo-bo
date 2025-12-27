from django.contrib import admin
from .models import Supplier, SupplierPrice, SupplierOffer

# On définit comment afficher les prix d'achat à l'intérieur d'un autre modèle
# Note : on utilise maintenant SupplierPrice
class SupplierPriceInline(admin.TabularInline):
    model = SupplierPrice
    extra = 1  
    fields = ('supplier', 'price', 'lead_time_days', 'is_preferred')

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'email')
    search_fields = ('name',)

@admin.register(SupplierPrice)
class SupplierPriceAdmin(admin.ModelAdmin):
    list_display = ('product', 'supplier', 'price', 'is_preferred')
    list_filter = ('supplier', 'product')

@admin.register(SupplierOffer)
class SupplierOfferAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'description', 'valid_until')