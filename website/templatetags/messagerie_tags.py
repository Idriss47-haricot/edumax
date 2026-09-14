from django import template
from ..models import MessagePrive

register = template.Library()

@register.simple_tag(takes_context=True)
def messages_non_lus(context):
    """Retourne le nombre de messages non lus pour l'utilisateur"""
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return 0
    
    return MessagePrive.objects.filter(
        conversation__participants=request.user,
        lu=False
    ).exclude(expediteur=request.user).count()