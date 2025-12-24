from django import template
from decimal import Decimal
from django import template
from django.templatetags.static import static

register = template.Library()






@register.filter
def notification_image(image, default_image=None):
    if image:
        return image.url
    return default_image or static('images/bitcoin.png')
    
register = template.Library()

@register.filter
def multiply(value, arg):
    return Decimal(value) * Decimal(arg)