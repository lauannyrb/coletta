from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('colecoes/', views.collection_list, name='collection_list'),
    path('colecoes/nova/', views.collection_create, name='collection_create'),
    path('colecoes/<int:pk>/', views.collection_detail, name='collection_detail'),
    path('colecoes/<int:pk>/editar/', views.collection_update, name='collection_update'),
    path('colecoes/<int:pk>/excluir/', views.collection_delete, name='collection_delete'),
    path('colecoes/<int:collection_pk>/itens/novo/', views.item_create, name='item_create'),
    path('itens/<int:pk>/editar/', views.item_update, name='item_update'),
    path('itens/<int:pk>/excluir/', views.item_delete, name='item_delete'),
    path('busca/', views.search, name='search'),
]
