from urllib.parse import urlencode, urlsplit

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Q
from django.db.models.functions import Lower
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import Resolver404, resolve, reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import CollectionFieldForm, CollectionForm, CollectionItemForm
from .models import Collection, CollectionField, CollectionItem

# Isolamento entre usuários (RN06, RN31): toda consulta parte do usuário autenticado.
# Coleção, item ou campo de outra pessoa → 404, sem revelar se o registro existe.

SEARCH_MAX_LENGTH = 100
LIVE_SEARCH_LIMIT = 5

# Ordenações aceitas na lista de itens (lista fechada: o parâmetro da URL nunca vira consulta direta)
ITEM_ORDERINGS = {
    'recentes': ('Mais recentes', ('-updated_at',)),
    'nome': ('Nome (A–Z)', (Lower('name'),)),
    'ano': ('Ano', (F('year').asc(nulls_last=True), Lower('name'))),
}


def _user_collections(user):
    return user.collections.annotate(item_count=Count('items'))


def _get_own_collection(request, pk):
    return get_object_or_404(Collection, pk=pk, user=request.user)


def _get_own_item(request, pk):
    return get_object_or_404(
        CollectionItem.objects.select_related('collection'),
        pk=pk,
        collection__user=request.user,
    )


def _get_own_field(request, pk):
    return get_object_or_404(
        CollectionField.objects.select_related('collection'),
        pk=pk,
        collection__user=request.user,
    )


def _item_form_return(request, collection):
    """Endereço do formulário de item de onde a pessoa veio (?voltar=), para o botão "Voltar ao item".

    Só aceita o cadastro ou a edição de item DESTA coleção (do dono): qualquer outro valor é ignorado,
    o que impede usar o parâmetro para mandar alguém a um site externo (open redirect).
    """
    url = request.GET.get('voltar', '')
    if not url.startswith('/') or url.startswith('//'):
        return ''
    path = urlsplit(url).path
    try:
        match = resolve(path)
    except Resolver404:
        return ''
    if match.url_name == 'item_create' and match.kwargs.get('collection_pk') == collection.pk:
        return path
    if match.url_name == 'item_update' and collection.items.filter(pk=match.kwargs.get('pk')).exists():
        return path
    return ''


def _fields_url(collection, return_url):
    url = reverse('collection_fields', args=[collection.pk])
    return f'{url}?{urlencode({"voltar": return_url})}' if return_url else url


def _touch(collection):
    # Mudanças nos itens contam como atividade da coleção (recentes e "última atualização")
    collection.save(update_fields=['updated_at'])


@login_required
def home(request):
    collections = _user_collections(request.user)
    items = CollectionItem.objects.filter(collection__user=request.user)
    month_start = timezone.localtime().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    context = {
        'total_collections': collections.count(),
        'total_items': items.count(),
        'total_categories': request.user.collections.values('category').distinct().count(),
        'items_this_month': items.filter(created_at__gte=month_start).count(),
        'last_collection': request.user.collections.order_by('-updated_at').first(),
        'recent_collections': collections[:4],
    }
    return render(request, 'colecoes/home.html', context)


@login_required
def collection_list(request):
    return render(request, 'colecoes/collection_list.html', {
        'collections': _user_collections(request.user),
    })


@login_required
@require_http_methods(['GET', 'POST'])
def collection_create(request):
    form = CollectionForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        collection = form.save(commit=False)
        collection.user = request.user  # RN09: dono sempre do back-end
        collection.save()
        messages.success(request, f'Coleção “{collection.name}” criada.')
        return redirect('collection_detail', pk=collection.pk)
    return render(request, 'colecoes/collection_form.html', {'form': form})


@login_required
def collection_detail(request, pk):
    collection = _get_own_collection(request, pk)
    all_items = collection.items.all()

    # Filtros e ordenação vindos da URL: só valores conhecidos são aceitos
    condition = request.GET.get('estado', '')
    if condition not in CollectionItem.Condition.values:
        condition = ''
    edition = request.GET.get('edicao', '')[:60]
    ordering = request.GET.get('ordem', 'recentes')
    if ordering not in ITEM_ORDERINGS:
        ordering = 'recentes'

    items = all_items
    if condition:
        items = items.filter(condition=condition)
    if edition:
        items = items.filter(edition__iexact=edition)
    items = items.order_by(*ITEM_ORDERINGS[ordering][1]).prefetch_related('field_values__field')

    # Chips dos filtros ativos, cada um com o link que remove só aquele filtro
    params = {'estado': condition, 'edicao': edition, 'ordem': '' if ordering == 'recentes' else ordering}

    def url_without(key):
        rest = {k: v for k, v in params.items() if v and k != key}
        return f'?{urlencode(rest)}' if rest else request.path

    active_filters = []
    if condition:
        active_filters.append(('Estado', CollectionItem.Condition(condition).label, url_without('estado')))
    if edition:
        active_filters.append(('Edição', edition, url_without('edicao')))

    counts = dict(all_items.exclude(condition='').values_list('condition').annotate(total=Count('pk')))
    condition_summary = [
        (value, label, counts[value]) for value, label in CollectionItem.Condition.choices if value in counts
    ]

    return render(request, 'colecoes/collection_detail.html', {
        'collection': collection,
        'items': items,
        'total_items': all_items.count(),
        'condition_summary': condition_summary,
        'conditions': CollectionItem.Condition.choices,
        'editions': (
            all_items.exclude(edition='').order_by(Lower('edition'))
            .values_list('edition', flat=True).distinct()
        ),
        'orderings': [(key, label) for key, (label, _) in ITEM_ORDERINGS.items()],
        'selected': {'estado': condition, 'edicao': edition, 'ordem': ordering},
        'filters_active': bool(condition or edition),
        'active_filters': active_filters,
        'custom_fields': collection.custom_fields.all(),
    })


@login_required
@require_http_methods(['GET', 'POST'])
def collection_update(request, pk):
    collection = _get_own_collection(request, pk)
    form = CollectionForm(request.POST or None, request.FILES or None, instance=collection)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Coleção atualizada.')
        return redirect('collection_detail', pk=collection.pk)
    return render(request, 'colecoes/collection_form.html', {'form': form, 'collection': collection})


@login_required
def collection_cover(request, pk):
    # A capa nunca é servida pelo Nginx: só o dono da coleção recebe o arquivo (RN24)
    collection = _get_own_collection(request, pk)
    if not collection.cover:
        raise Http404
    response = FileResponse(collection.cover.open('rb'), content_type='image/webp')
    # A URL leva ?v=<nome do arquivo>, então uma capa nova nunca vem do cache antigo
    response['Cache-Control'] = 'private, max-age=86400'
    return response


@login_required
@require_http_methods(['GET', 'POST'])
def collection_delete(request, pk):
    collection = _get_own_collection(request, pk)
    if request.method == 'POST':
        name = collection.name
        collection.delete()  # CASCADE remove os itens (RN13)
        messages.success(request, f'Coleção “{name}” e seus itens foram excluídos.')
        return redirect('collection_list')
    return render(request, 'colecoes/collection_confirm_delete.html', {
        'collection': collection,
        'item_count': collection.items.count(),
    })


@login_required
@require_http_methods(['GET', 'POST'])
def collection_fields(request, pk):
    collection = _get_own_collection(request, pk)
    return_url = _item_form_return(request, collection)
    form = CollectionFieldForm(request.POST or None, collection=collection)
    if request.method == 'POST' and form.is_valid():
        field = form.save()
        messages.success(request, f'Campo “{field.name}” adicionado aos itens desta coleção.')
        return redirect(_fields_url(collection, return_url))
    return render(request, 'colecoes/collection_fields.html', {
        'collection': collection,
        'fields': collection.custom_fields.annotate(filled=Count('values')),
        'form': form,
        'max_fields': CollectionField.MAX_PER_COLLECTION,
        'return_url': return_url,
        'return_query': f'?{urlencode({"voltar": return_url})}' if return_url else '',
    })


@login_required
@require_http_methods(['GET', 'POST'])
def field_update(request, pk):
    field = _get_own_field(request, pk)
    fields_url = _fields_url(field.collection, _item_form_return(request, field.collection))
    form = CollectionFieldForm(request.POST or None, instance=field, collection=field.collection)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Campo renomeado.')
        return redirect(fields_url)
    return render(request, 'colecoes/field_form.html', {
        'form': form,
        'field': field,
        'collection': field.collection,
        'fields_url': fields_url,
    })


@login_required
@require_http_methods(['GET', 'POST'])
def field_delete(request, pk):
    field = _get_own_field(request, pk)
    collection = field.collection
    fields_url = _fields_url(collection, _item_form_return(request, collection))
    if request.method == 'POST':
        name = field.name
        field.delete()  # CASCADE remove os valores preenchidos nos itens
        messages.success(request, f'Campo “{name}” excluído.')
        return redirect(fields_url)
    return render(request, 'colecoes/field_confirm_delete.html', {
        'field': field,
        'collection': collection,
        'filled': field.values.count(),
        'fields_url': fields_url,
    })


@login_required
def item_detail(request, pk):
    item = _get_own_item(request, pk)
    return render(request, 'colecoes/item_detail.html', {
        'item': item,
        'collection': item.collection,
        'field_values': item.field_values.select_related('field'),
    })


@login_required
@require_http_methods(['GET', 'POST'])
def item_create(request, collection_pk):
    # A coleção de destino também é validada pelo dono (nunca confiar no ID vindo do navegador)
    collection = _get_own_collection(request, collection_pk)
    form = CollectionItemForm(request.POST or None, collection=collection)
    if request.method == 'POST' and form.is_valid():
        item = form.save()
        _touch(collection)
        messages.success(request, f'Item “{item.name}” adicionado.')
        if request.POST.get('add_another'):
            return redirect(reverse('item_create', args=[collection.pk]) + '?continuar=1')
        return redirect('collection_detail', pk=collection.pk)
    return render(request, 'colecoes/item_form.html', {
        'form': form,
        'collection': collection,
        'item_count': collection.items.count(),
        'add_another': bool(request.POST.get('add_another') or request.GET.get('continuar')),
    })


@login_required
@require_http_methods(['GET', 'POST'])
def item_update(request, pk):
    item = _get_own_item(request, pk)
    form = CollectionItemForm(request.POST or None, instance=item, collection=item.collection)
    if request.method == 'POST' and form.is_valid():
        form.save()
        _touch(item.collection)
        messages.success(request, 'Item atualizado.')
        return redirect('item_detail', pk=item.pk)
    return render(request, 'colecoes/item_form.html', {
        'form': form,
        'collection': item.collection,
        'item': item,
        'item_count': item.collection.items.count(),
    })


@login_required
@require_http_methods(['GET', 'POST'])
def item_delete(request, pk):
    item = _get_own_item(request, pk)
    collection = item.collection
    if request.method == 'POST':
        name = item.name
        item.delete()
        _touch(collection)
        messages.success(request, f'Item “{name}” excluído.')
        return redirect('collection_detail', pk=collection.pk)
    return render(request, 'colecoes/item_confirm_delete.html', {'item': item, 'collection': collection})


@login_required
def search(request):
    # Ignora espaços extras nas pontas e no meio (RN29)
    query = ' '.join(request.GET.get('q', '').split())[:SEARCH_MAX_LENGTH]
    collections = items = None
    if query:
        tag = query.lstrip('#')
        collections = _user_collections(request.user).filter(
            Q(name__icontains=query) | Q(tags__icontains=tag)
        )
        items = (
            CollectionItem.objects
            .filter(collection__user=request.user)
            .filter(Q(name__icontains=query) | Q(edition__icontains=query))
            .select_related('collection')
        )
    if request.GET.get('parcial') == '1':
        # Busca em tempo real (static/js/busca.js): só um trecho de HTML com os primeiros resultados.
        # Mesmas consultas filtradas pelo dono e mesmo autoescape da página completa.
        context = {'query': query}
        if query:
            context.update({
                'collections': collections[:LIVE_SEARCH_LIMIT],
                'items': items[:LIVE_SEARCH_LIMIT],
                'total': collections.count() + items.count(),
            })
        return render(request, 'partials/search_live.html', context)
    return render(request, 'colecoes/search.html', {
        'query': query,
        'collections': collections,
        'items': items,
    })
