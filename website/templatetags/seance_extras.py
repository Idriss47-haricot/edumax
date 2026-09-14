from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Récupère une valeur d'un dictionnaire par sa clé"""
    if dictionary is None:
        return None
    try:
        return dictionary.get(key)
    except (AttributeError, TypeError):
        return None