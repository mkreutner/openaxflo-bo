from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order

@receiver(post_save, sender=Order)
def update_stock_on_shipping(sender, instance, **kwargs):
    # Si la commande vient de passer en 'SHIPPED'
    if instance.status == 'SHIPPED':
        for line in instance.lines.all():
            product = line.product
            # On déduit la quantité vendue du stock
            product.stock_quantity -= line.quantity
            product.save()
        pass