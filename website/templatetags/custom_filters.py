from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Récupère un élément d'un dictionnaire par sa clé"""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def get_attr(obj, attr):
    """Récupère un attribut d'un objet"""
    if obj is None:
        return None
    return getattr(obj, attr, None)