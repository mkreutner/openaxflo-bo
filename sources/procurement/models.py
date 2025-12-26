from django.db import models
from inventory.models import Product

# Procurement models.
class Supplier(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()

    def __str__(self):
        return self.name

class PurchasePrice(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='purchase_prices')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    lead_time_days = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('product', 'supplier')
