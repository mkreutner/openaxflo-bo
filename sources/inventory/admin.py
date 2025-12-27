from django.contrib import admin

# Register your models here.
from .models import Category, Brand, Product
# On importe l'Inline depuis l'autre application
from procurement.admin import SupplierPriceInline

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'slug')
    list_filter = ('parent',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)} # Génère le slug automatiquement

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'retail_price')
    list_filter = ('category', 'brand')
    search_fields = ('name',)
    # On insère l'Inline ici
    inlines = [SupplierPriceInline]