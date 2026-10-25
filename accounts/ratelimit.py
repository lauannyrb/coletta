from functools import wraps

from django.core.cache import cache
from django.shortcuts import render

from .utils import get_client_ip


def ratelimit_post(key_prefix, limit, period):
    """Limita requisições POST por IP: no máximo `limit` a cada `period` segundos.

    Acima do limite, responde 429 sem executar a view.
    """
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if request.method == 'POST':
                key = f'ratelimit:{key_prefix}:{get_client_ip(request)}'
                # add() só cria a chave se ela não existir, preservando a janela já iniciada
                cache.add(key, 0, period)
                try:
                    count = cache.incr(key)
                except ValueError:
                    # A chave expirou entre o add() e o incr()
                    cache.set(key, 1, period)
                    count = 1
                if count > limit:
                    return render(request, 'accounts/bloqueado.html', status=429)
            return view(request, *args, **kwargs)
        return wrapped
    return decorator
