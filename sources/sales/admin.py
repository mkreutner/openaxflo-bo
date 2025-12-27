from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Customer, Address, Carrier, Order, OrderLine, Promotion

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
    list_display = (
        'id', 
        'reference', 
        'customer', 
        'status', 
        'carrier', 
        'shipping_cost', 
        'get_total', 
        'view_invoice_link'
    )
    readonly_fields = ('reference',)
    
    fieldsets = (
        ('General Info', {'fields': ('reference', 'customer', 'status')}),
        ('Shipping & Logistics', {
            'fields': ('carrier', 'is_relay_point', 'relay_point_id', 'shipping_cost', 'tracking_number')
        }),
        ('Addresses', {'fields': ('billing_address', 'shipping_address')}),
    )

    actions = ['generate_credit_notes']

    def get_total(self, obj):
        # Méthode pour afficher le total (Produits + Livraison) dans la liste
        product_total = sum(line.total_line_price for line in obj.lines.all())
        return product_total + obj.shipping_cost
    get_total.short_description = 'Total Order'

    @admin.action(description="Generate a credit note for the selected orders")
    def generate_credit_notes(self, request, queryset):
        created_count = 0
        
        for order in queryset:
            # Sécurité : On ne génère un avoir que pour des commandes non annulées 
            # et qui n'ont pas déjà d'avoir lié
            if order.status != 'CANCELLED' and not hasattr(order, 'applied_credit_note'):
                
                # Calcul du montant total de la commande (Produits + Port - Remises déjà appliquées)
                totals = order.get_totals()
                amount_to_refund = totals['grand_total_ttc']
                
                # Création de l'avoir
                credit = CreditNote.objects.create(
                    customer=order.customer,
                    amount=amount_to_refund,
                    code=f"AV-{uuid.uuid4().hex[:6].upper()}",
                    expiry_date=timezone.now().date() + timedelta(days=365) # Valable 1 an
                )
                
                # On marque la commande comme annulée après génération de l'avoir
                order.status = 'CANCELLED'
                order.save()
                created_count += 1
        
        self.message_user(
            request, 
            f"{created_count} have been successfully generated.",
            messages.SUCCESS
        )

    def view_invoice_link(self, obj):
        url = reverse('generate_invoice_pdf', args=[obj.id])
        return format_html('<a class="button" href="{}" target="_blank">📄 PDF</a>', url)
    
    view_invoice_link.short_description = "Facture"

admin.site.register(Carrier)

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('name', 'promo_type', 'active', 'start_date', 'end_date')
    list_filter = ('promo_type', 'active')
    search_fields = ('name', 'code')
    
    # Interface pro pour gérer les listes de produits/catégories
    filter_horizontal = (
        'target_brands', 'target_categories', 'target_products',
        'excluded_categories', 'excluded_products'
    )
    
    fieldsets = (
        ('General Information', {'fields': ('name', 'promo_type', 'code', 'active')}),
        ('Value', {'fields': ('discount_type', 'value', 'start_date', 'end_date')}),
        ('Targeting (Inclusion)', {
            'classes': ('collapse',),
            'fields': ('target_brands', 'target_categories', 'target_products')
        }),
        ('Exclusions', {
            'classes': ('collapse',),
            'fields': ('excluded_categories', 'excluded_products')
        }),
    )
