from django.conf import settings


def get_client_ip(request):
    """IP real do cliente, usado pelo django-axes e pelo rate limit do cadastro.

    Em produção o Django fica atrás do Nginx (socket Unix), então REMOTE_ADDR não traz o IP do
    cliente. O Nginx sobrescreve X-Real-IP com $remote_addr, por isso o cabeçalho só é confiável
    com BEHIND_PROXY=True; sem proxy, ele poderia ser forjado pelo próprio cliente.
    """
    if settings.BEHIND_PROXY:
        ip = request.META.get('HTTP_X_REAL_IP')
        if ip:
            return ip
    return request.META.get('REMOTE_ADDR')
