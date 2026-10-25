from datetime import timedelta

from django import template
from django.utils import timezone
from django.utils.timesince import timesince

register = template.Library()


@register.filter
def ha_quanto_tempo(value):
    """'agora mesmo' para menos de 1 minuto; senão 'há 2 horas', 'há 3 dias'..."""
    if not value:
        return ''
    if timezone.now() - value < timedelta(minutes=1):
        return 'agora mesmo'
    return f'há {timesince(value)}'
