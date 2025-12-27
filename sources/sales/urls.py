from django.urls import path
from . import views

urlpatterns = [
    # ... tes autres urls ...
    path('order/<int:order_id>/pdf/', views.generate_invoice_pdf, name='generate_invoice_pdf'),
]