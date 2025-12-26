from django.contrib import admin
from .models import Customer, Address, Carrier, Order, OrderLine

class AddressInline(admin.TabularInline):
    model = Address
    extra = 1

class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 1

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'email')
    inlines = [AddressInline]

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('reference', 'customer', 'status', 'carrier', 'shipping_cost', 'get_total')
    
    fieldsets = (
        ('General Info', {'fields': ('reference', 'customer', 'status')}),
        ('Shipping & Logistics', {
            'fields': ('carrier', 'is_relay_point', 'relay_point_id', 'shipping_cost', 'tracking_number')
        }),
        ('Addresses', {'fields': ('billing_address', 'shipping_address')}),
    )

    def get_total(self, obj):
        # Méthode pour afficher le total (Produits + Livraison) dans la liste
        product_total = sum(line.total_line_price for line in obj.lines.all())
        return product_total + obj.shipping_cost
    get_total.short_description = 'Total Order'

admin.site.register(Carrier)