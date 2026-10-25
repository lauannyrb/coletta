from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import CollectionForm, CollectionItemForm
from .models import Collection, CollectionItem

# Isolamento entre usuários (RN06, RN31): toda consulta parte do usuário autenticado.
# Coleção ou item de outra pessoa → 404, sem revelar se o registro existe.

SEARCH_MAX_LENGTH = 100


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


def _touch(collection):
    # Mudanças nos itens contam como atividade da coleção (recentes e "última atualização")
    collection.save(update_fields=['updated_at'])


@login_required
def home(request):
    collections = _user_collections(request.user)
    context = {
        'total_collections': collections.count(),
        'total_items': CollectionItem.objects.filter(collection__user=request.user).count(),
        'last_update': request.user.collections.aggregate(last=Max('updated_at'))['last'],
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
    form = CollectionForm(request.POST or None)
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
    return render(request, 'colecoes/collection_detail.html', {
        'collection': collection,
        'items': collection.items.all(),
    })


@login_required
@require_http_methods(['GET', 'POST'])
def collection_update(request, pk):
    collection = _get_own_collection(request, pk)
    form = CollectionForm(request.POST or None, instance=collection)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Coleção atualizada.')
        return redirect('collection_detail', pk=collection.pk)
    return render(request, 'colecoes/collection_form.html', {'form': form, 'collection': collection})


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
def item_create(request, collection_pk):
    # A coleção de destino também é validada pelo dono (nunca confiar no ID vindo do navegador)
    collection = _get_own_collection(request, collection_pk)
    form = CollectionItemForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        item.collection = collection
        item.save()
        _touch(collection)
        messages.success(request, f'Item “{item.name}” adicionado.')
        return redirect('collection_detail', pk=collection.pk)
    return render(request, 'colecoes/item_form.html', {'form': form, 'collection': collection})


@login_required
@require_http_methods(['GET', 'POST'])
def item_update(request, pk):
    item = _get_own_item(request, pk)
    form = CollectionItemForm(request.POST or None, instance=item)
    if request.method == 'POST' and form.is_valid():
        form.save()
        _touch(item.collection)
        messages.success(request, 'Item atualizado.')
        return redirect('collection_detail', pk=item.collection.pk)
    return render(request, 'colecoes/item_form.html', {
        'form': form,
        'collection': item.collection,
        'item': item,
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
        collections = _user_collections(request.user).filter(name__icontains=query)
        items = (
            CollectionItem.objects
            .filter(collection__user=request.user, name__icontains=query)
            .select_related('collection')
        )
    return render(request, 'colecoes/search.html', {
        'query': query,
        'collections': collections,
        'items': items,
    })
