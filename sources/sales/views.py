from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa  # Assure-toi que xhtml2pdf est installé : pip install xhtml2pdf
from .models import Order

def generate_invoice_pdf(request, order_id):
    # Utilisation de get_object_or_404 pour éviter un crash si l'ID n'existe pas
    order = get_object_or_404(Order, id=order_id)
    
    # On récupère tes nouveaux calculs dynamiques
    totals = order.get_totals() 
    
    template = get_template('sales/invoice_pdf.html')
    
    # On passe l'ordre et les totaux au template
    context = {
        'order': order, 
        'totals': totals,
        'pagesize': 'A4',
    }
    
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    # On utilise la référence (ex: ORD-2025-0001) plutôt que l'ID pour le nom du fichier
    response['Content-Disposition'] = f'filename="facture_{order.reference}.pdf"'
    
    # Création du PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Erreur lors de la génération du PDF', status=500)
    
    return response