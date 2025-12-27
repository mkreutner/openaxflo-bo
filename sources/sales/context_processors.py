from sales.models import Order
from inventory.models import Product
from django.db.models import Sum, F
from django.utils import timezone

def dashboard_stats(request):
    if not request.user.is_staff:
        return {}

    # 1. Chiffre d'affaires du mois en cours
    current_month = timezone.now().month
    ca_month = Order.objects.filter(
        status__in=['PAID', 'SHIPPED'],
        created_at__month=current_month
    ).aggregate(total=Sum('lines__unit_price_incl_tax'))['total'] or 0

    # 2. Alertes Stock (Produits sous le seuil)
    low_stock_count = Product.objects.filter(
        stock_quantity__lte=F('low_stock_threshold')
    ).count()

    # 3. Commandes en attente de traitement
    pending_orders = Order.objects.filter(status='DRAFT').count()

    return {
        'stat_ca_month': ca_month,
        'stat_low_stock': low_stock_count,
        'stat_pending_orders': pending_orders,
    }
