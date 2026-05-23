from django import template

register = template.Library()

@register.filter
def split(value, delimiter=','):
    """Split a string by delimiter. Usage: "a,b,c"|split:"," """
    return value.split(delimiter)

@register.filter
def get_item(dictionary, key):
    """Get dict item by key in template. Usage: mydict|get_item:key """
    return dictionary.get(key, 0)
