from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Collection, CollectionItem

User = get_user_model()


class BaseTestCase(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user('ana@exemplo.com', 'Ana', 'Colecao-Segura-2026')
        self.bia = User.objects.create_user('bia@exemplo.com', 'Bia', 'Colecao-Segura-2026')
        self.client.force_login(self.ana)


class CollectionCrudTests(BaseTestCase):
    def test_cria_colecao_vinculada_ao_usuario_logado(self):
        response = self.client.post(reverse('collection_create'), {
            'name': '  Discos de vinil  ',
            'description': 'MPB e jazz',
            'user': self.bia.pk,  # tentativa de forjar o dono: deve ser ignorada (RN09)
        })
        collection = Collection.objects.get()
        self.assertRedirects(response, reverse('collection_detail', args=[collection.pk]))
        self.assertEqual(collection.user, self.ana)
        self.assertEqual(collection.name, 'Discos de vinil')

    def test_recusa_nome_vazio_ou_so_espacos(self):
        for name in ['', '    ']:
            response = self.client.post(reverse('collection_create'), {'name': name})
            self.assertEqual(response.status_code, 200)
            self.assertFormError(response.context['form'], 'name', 'Este campo é obrigatório.')
        self.assertFalse(Collection.objects.exists())

    def test_recusa_textos_longos_demais(self):
        response = self.client.post(reverse('collection_create'), {
            'name': 'x' * 101,
            'description': 'y' * 1001,
        })
        form = response.context['form']
        self.assertTrue(form.has_error('name'))
        self.assertTrue(form.has_error('description'))
        self.assertFalse(Collection.objects.exists())

    def test_permite_nomes_repetidos(self):
        for _ in range(2):
            self.client.post(reverse('collection_create'), {'name': 'Câmeras'})
        self.assertEqual(Collection.objects.filter(name='Câmeras').count(), 2)

    def test_edita_colecao(self):
        collection = Collection.objects.create(user=self.ana, name='Antigo')
        self.client.post(reverse('collection_update', args=[collection.pk]), {'name': 'Novo'})
        collection.refresh_from_db()
        self.assertEqual(collection.name, 'Novo')

    def test_confirmacao_avisa_quantos_itens_serao_excluidos(self):
        collection = Collection.objects.create(user=self.ana, name='Vinis')
        CollectionItem.objects.create(collection=collection, name='Disco 1')
        CollectionItem.objects.create(collection=collection, name='Disco 2')
        response = self.client.get(reverse('collection_delete', args=[collection.pk]))
        self.assertContains(response, '2 itens serão excluídos')
        self.assertTrue(Collection.objects.filter(pk=collection.pk).exists())

    def test_excluir_colecao_remove_os_itens(self):
        collection = Collection.objects.create(user=self.ana, name='Vinis')
        CollectionItem.objects.create(collection=collection, name='Disco')
        response = self.client.post(reverse('collection_delete', args=[collection.pk]))
        self.assertRedirects(response, reverse('collection_list'))
        self.assertFalse(Collection.objects.exists())
        self.assertFalse(CollectionItem.objects.exists())


class ItemCrudTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.collection = Collection.objects.create(user=self.ana, name='Vinis')

    def test_cria_item_na_colecao(self):
        response = self.client.post(reverse('item_create', args=[self.collection.pk]), {
            'name': 'Kind of Blue',
            'category': 'Jazz',
        })
        self.assertRedirects(response, reverse('collection_detail', args=[self.collection.pk]))
        item = CollectionItem.objects.get()
        self.assertEqual(item.collection, self.collection)

    def test_recusa_item_com_nome_so_de_espacos(self):
        response = self.client.post(reverse('item_create', args=[self.collection.pk]), {'name': '   '})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CollectionItem.objects.exists())

    def test_edita_e_exclui_item(self):
        item = CollectionItem.objects.create(collection=self.collection, name='Antigo')
        self.client.post(reverse('item_update', args=[item.pk]), {'name': 'Novo', 'category': 'Raro'})
        item.refresh_from_db()
        self.assertEqual((item.name, item.category), ('Novo', 'Raro'))

        self.client.post(reverse('item_delete', args=[item.pk]))
        self.assertFalse(CollectionItem.objects.exists())

    def test_get_na_exclusao_nao_exclui(self):
        item = CollectionItem.objects.create(collection=self.collection, name='Disco')
        self.client.get(reverse('item_delete', args=[item.pk]))
        self.assertTrue(CollectionItem.objects.filter(pk=item.pk).exists())

    def test_mudanca_em_item_atualiza_a_colecao(self):
        before = self.collection.updated_at
        self.client.post(reverse('item_create', args=[self.collection.pk]), {'name': 'Disco'})
        self.collection.refresh_from_db()
        self.assertGreater(self.collection.updated_at, before)


class HomeTests(BaseTestCase):
    def test_estado_vazio(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.context['total_collections'], 0)
        self.assertEqual(response.context['total_items'], 0)
        self.assertContains(response, 'Criar minha primeira coleção')

    def test_totais_consideram_apenas_o_usuario_atual(self):
        vinis = Collection.objects.create(user=self.ana, name='Vinis')
        Collection.objects.create(user=self.ana, name='Câmeras')
        CollectionItem.objects.create(collection=vinis, name='Disco 1')
        CollectionItem.objects.create(collection=vinis, name='Disco 2')
        da_bia = Collection.objects.create(user=self.bia, name='Da Bia')
        CollectionItem.objects.create(collection=da_bia, name='Item da Bia')

        response = self.client.get(reverse('home'))
        self.assertEqual(response.context['total_collections'], 2)
        self.assertEqual(response.context['total_items'], 2)
        self.assertNotContains(response, 'Da Bia')

    def test_totais_atualizam_depois_de_excluir(self):
        collection = Collection.objects.create(user=self.ana, name='Vinis')
        CollectionItem.objects.create(collection=collection, name='Disco')
        self.client.post(reverse('collection_delete', args=[collection.pk]))
        response = self.client.get(reverse('home'))
        self.assertEqual(response.context['total_collections'], 0)
        self.assertEqual(response.context['total_items'], 0)

    def test_recentes_ordenadas_por_atualizacao(self):
        primeira = Collection.objects.create(user=self.ana, name='Primeira')
        Collection.objects.create(user=self.ana, name='Segunda')
        primeira.save()  # vira a mais recente
        response = self.client.get(reverse('home'))
        names = [c.name for c in response.context['recent_collections']]
        self.assertEqual(names, ['Primeira', 'Segunda'])


class SearchTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        vinis = Collection.objects.create(user=self.ana, name='Discos de Vinil')
        CollectionItem.objects.create(collection=vinis, name='Vinil azul raro')
        da_bia = Collection.objects.create(user=self.bia, name='Vinil da Bia')
        CollectionItem.objects.create(collection=da_bia, name='Vinil secreto da Bia')

    def test_busca_sem_diferenciar_maiusculas_e_com_espacos_extras(self):
        response = self.client.get(reverse('search'), {'q': '   VINIL  '})
        self.assertEqual(response.context['query'], 'VINIL')
        self.assertEqual([c.name for c in response.context['collections']], ['Discos de Vinil'])
        self.assertEqual([i.name for i in response.context['items']], ['Vinil azul raro'])

    def test_busca_nao_retorna_dados_de_outro_usuario(self):
        response = self.client.get(reverse('search'), {'q': 'Bia'})
        self.assertFalse(response.context['collections'])
        self.assertFalse(response.context['items'])
        self.assertContains(response, 'Nenhum resultado encontrado')

    def test_busca_vazia_nao_lista_nada(self):
        response = self.client.get(reverse('search'), {'q': '   '})
        self.assertEqual(response.context['query'], '')
        self.assertIsNone(response.context['collections'])


class AccessControlTests(BaseTestCase):
    """Usuária B (Bia) tentando acessar dados da usuária A (Ana): sempre 404 (RN06, RN31)."""

    def setUp(self):
        super().setUp()
        self.collection = Collection.objects.create(user=self.ana, name='Da Ana')
        self.item = CollectionItem.objects.create(collection=self.collection, name='Item da Ana')
        self.client.force_login(self.bia)

    def test_nao_acessa_edita_nem_exclui_colecao_de_outro_usuario(self):
        pk = self.collection.pk
        self.assertEqual(self.client.get(reverse('collection_detail', args=[pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('collection_update', args=[pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('collection_update', args=[pk]), {'name': 'Hack'}).status_code, 404)
        self.assertEqual(self.client.post(reverse('collection_delete', args=[pk])).status_code, 404)
        self.collection.refresh_from_db()
        self.assertEqual(self.collection.name, 'Da Ana')

    def test_nao_acessa_nem_modifica_item_de_outro_usuario(self):
        pk = self.item.pk
        self.assertEqual(self.client.get(reverse('item_update', args=[pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('item_update', args=[pk]), {'name': 'Hack'}).status_code, 404)
        self.assertEqual(self.client.post(reverse('item_delete', args=[pk])).status_code, 404)
        self.item.refresh_from_db()
        self.assertEqual(self.item.name, 'Item da Ana')

    def test_nao_cria_item_em_colecao_de_outro_usuario(self):
        response = self.client.post(reverse('item_create', args=[self.collection.pk]), {'name': 'Intruso'})
        self.assertEqual(response.status_code, 404)
        self.assertFalse(CollectionItem.objects.filter(name='Intruso').exists())

    def test_404_igual_para_id_inexistente_e_de_outro_usuario(self):
        de_outro = self.client.get(reverse('collection_detail', args=[self.collection.pk]))
        inexistente = self.client.get(reverse('collection_detail', args=[99999]))
        self.assertEqual(de_outro.status_code, inexistente.status_code)
        self.assertEqual(de_outro.content, inexistente.content)

    def test_listagem_nao_mostra_colecoes_de_outro_usuario(self):
        response = self.client.get(reverse('collection_list'))
        self.assertNotContains(response, 'Da Ana')

    def test_paginas_privadas_exigem_login(self):
        self.client.logout()
        urls = [
            reverse('home'),
            reverse('collection_list'),
            reverse('collection_create'),
            reverse('collection_detail', args=[self.collection.pk]),
            reverse('item_create', args=[self.collection.pk]),
            reverse('item_update', args=[self.item.pk]),
            reverse('search'),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, url)
            self.assertTrue(response.url.startswith(reverse('login')), url)
