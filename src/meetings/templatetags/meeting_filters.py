"""
Custom template filters for time-manager
"""
from django import template
from datetime import datetime

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter to get an item from a dictionary
    Usage: {{ mydict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def format_date_header(date_str):
    """
    Format date string for heatmap header
    Usage: {{ date_str|format_date_header }}
    Converts '2024-01-15' to 'Mon 15/1'
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        # Vietnamese day names
        day_names = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']
        day_name = day_names[date_obj.weekday()]
        return f"{day_name} {date_obj.day}/{date_obj.month}"
    except:
        return date_str
