from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Collection, CollectionField, CollectionItem, ItemFieldValue

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
            'category': 'musica',
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
            self.client.post(reverse('collection_create'), {'name': 'Câmeras', 'category': 'fotografia'})
        self.assertEqual(Collection.objects.filter(name='Câmeras').count(), 2)

    def test_edita_colecao(self):
        collection = Collection.objects.create(user=self.ana, name='Antigo')
        self.client.post(reverse('collection_update', args=[collection.pk]), {'name': 'Novo', 'category': 'outros'})
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
            'edition': 'Jazz',
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
        self.client.post(reverse('item_update', args=[item.pk]), {'name': 'Novo', 'edition': 'Raro'})
        item.refresh_from_db()
        self.assertEqual((item.name, item.edition), ('Novo', 'Raro'))

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

    def test_detalhes_dos_totais(self):
        Collection.objects.create(user=self.ana, name='Câmeras', category='fotografia')
        Collection.objects.create(user=self.ana, name='Discos antigos', category='musica')
        vinis = Collection.objects.create(user=self.ana, name='Vinis', category='musica')
        for i in range(4):
            CollectionItem.objects.create(collection=vinis, name=f'Disco {i}')
        da_bia = Collection.objects.create(user=self.bia, name='Da Bia', category='arte')
        CollectionItem.objects.create(collection=da_bia, name='Item')

        response = self.client.get(reverse('home'))
        self.assertEqual(response.context['total_categories'], 2)  # música conta uma vez; a da Bia não entra
        self.assertEqual(response.context['items_this_month'], 4)
        self.assertEqual(response.context['last_collection'], vinis)

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

    def test_404_usa_pagina_propria_sem_detalhes_tecnicos(self):
        response = self.client.get(reverse('collection_detail', args=[self.collection.pk]))
        self.assertTemplateUsed(response, '404.html')
        self.assertContains(response, 'Página não encontrada', status_code=404)
        self.assertNotContains(response, 'Collection', status_code=404)

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


def _image_file(name='capa.png', fmt='PNG', size=(800, 600), exif=None):
    from io import BytesIO

    from django.core.files.uploadedfile import SimpleUploadedFile
    from PIL import Image

    buffer = BytesIO()
    image = Image.new('RGB', size, (118, 85, 200))
    kwargs = {'exif': exif} if exif is not None else {}
    image.save(buffer, format=fmt, **kwargs)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=f'image/{fmt.lower()}')


class CoverTests(BaseTestCase):
    """Capa da coleção: validação pelo conteúdo, regravação e acesso só pelo dono (RN24)."""

    def setUp(self):
        import shutil
        import tempfile

        from django.test import override_settings

        super().setUp()
        media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media, ignore_errors=True)
        override = override_settings(MEDIA_ROOT=media)
        override.enable()
        self.addCleanup(override.disable)

    def create(self, cover):
        return self.client.post(reverse('collection_create'), {'name': 'Vinis', 'category': 'musica', 'cover': cover})

    def test_capa_valida_e_regravada_em_webp_com_nome_aleatorio(self):
        self.create(_image_file('minha foto.png'))
        collection = Collection.objects.get()
        self.assertRegex(collection.cover.name, r'^capas/[0-9a-f]{32}\.webp$')

        response = self.client.get(reverse('collection_cover', args=[collection.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/webp')
        self.assertTrue(b''.join(response.streaming_content).startswith(b'RIFF'))

    def test_metadados_exif_sao_removidos(self):
        from io import BytesIO

        from PIL import Image

        exif = Image.Exif()
        exif[0x010F] = 'CameraSecreta'  # Make (fabricante da câmera)
        self.create(_image_file('foto.jpg', fmt='JPEG', exif=exif))
        collection = Collection.objects.get()
        with collection.cover.open('rb') as f, Image.open(BytesIO(f.read())) as saved:
            self.assertEqual(len(saved.getexif()), 0)

    def test_imagem_grande_e_reduzida(self):
        from PIL import Image

        self.create(_image_file(size=(3000, 1500)))
        with Image.open(Collection.objects.get().cover.path) as saved:
            self.assertEqual(max(saved.size), 1600)

    def test_recusa_arquivo_que_nao_e_imagem_mesmo_com_extensao_png(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        fake = SimpleUploadedFile('capa.png', b'<script>alert(1)</script>', content_type='image/png')
        response = self.create(fake)
        self.assertTrue(response.context['form'].has_error('cover'))
        self.assertFalse(Collection.objects.exists())

    def test_recusa_formato_nao_permitido(self):
        response = self.create(_image_file('anim.gif', fmt='GIF'))
        self.assertTrue(response.context['form'].has_error('cover'))

    def test_recusa_arquivo_maior_que_2mb(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        big = SimpleUploadedFile('grande.png', b'0' * (2 * 1024 * 1024 + 1), content_type='image/png')
        response = self.create(big)
        self.assertFormError(response.context['form'], 'cover', 'A imagem deve ter no máximo 2 MB.')

    def test_recusa_dimensoes_gigantes(self):
        # PNG pequeno em bytes, mas com 6000 x 6000 pixels ao ser aberto
        response = self.create(_image_file(size=(6000, 6000)))
        self.assertFormError(response.context['form'], 'cover', 'A imagem tem dimensões grandes demais.')

    def test_trocar_remover_e_excluir_apagam_o_arquivo_antigo(self):
        self.create(_image_file())
        collection = Collection.objects.get()
        storage, first = collection.cover.storage, collection.cover.name

        self.client.post(reverse('collection_update', args=[collection.pk]),
                         {'name': 'Vinis', 'category': 'musica', 'cover': _image_file()})
        collection.refresh_from_db()
        second = collection.cover.name
        self.assertNotEqual(first, second)
        self.assertFalse(storage.exists(first))

        self.client.post(reverse('collection_update', args=[collection.pk]),
                         {'name': 'Vinis', 'category': 'musica', 'remove_cover': 'on'})
        collection.refresh_from_db()
        self.assertFalse(collection.cover)
        self.assertFalse(storage.exists(second))

        self.client.post(reverse('collection_update', args=[collection.pk]),
                         {'name': 'Vinis', 'category': 'musica', 'cover': _image_file()})
        collection.refresh_from_db()
        third = collection.cover.name
        self.client.post(reverse('collection_delete', args=[collection.pk]))
        self.assertFalse(storage.exists(third))

    def test_capa_de_outro_usuario_retorna_404(self):
        self.create(_image_file())
        collection = Collection.objects.get()
        self.client.force_login(self.bia)
        response = self.client.get(reverse('collection_cover', args=[collection.pk]))
        self.assertEqual(response.status_code, 404)

    def test_capa_exige_login(self):
        self.create(_image_file())
        collection = Collection.objects.get()
        self.client.logout()
        response = self.client.get(reverse('collection_cover', args=[collection.pk]))
        self.assertEqual(response.status_code, 302)

    def test_colecao_sem_capa_retorna_404(self):
        collection = Collection.objects.create(user=self.ana, name='Sem capa')
        response = self.client.get(reverse('collection_cover', args=[collection.pk]))
        self.assertEqual(response.status_code, 404)


class CollectionExtraFieldsTests(BaseTestCase):
    def post(self, **data):
        return self.client.post(reverse('collection_create'), {'name': 'Vinis', 'category': 'musica', **data})

    def test_salva_categoria_ano_e_tags_normalizadas(self):
        self.post(start_year='2019', tags=' #Rara, anos 2000, rara,, Importados ')
        collection = Collection.objects.get()
        self.assertEqual(collection.category, 'musica')
        self.assertEqual(collection.start_year, 2019)
        self.assertEqual(collection.tags, 'rara,anos-2000,importados')
        self.assertEqual(collection.tag_list, ['rara', 'anos-2000', 'importados'])

    def test_categoria_obrigatoria_e_restrita_a_lista(self):
        for category in ['', 'nao-existe']:
            response = self.client.post(reverse('collection_create'), {'name': 'X', 'category': category})
            self.assertTrue(response.context['form'].has_error('category'))
        self.assertFalse(Collection.objects.exists())

    def test_recusa_ano_no_futuro(self):
        from django.utils import timezone

        response = self.post(start_year=str(timezone.localdate().year + 1))
        self.assertTrue(response.context['form'].has_error('start_year'))

    def test_recusa_tag_invalida_e_tags_demais(self):
        response = self.post(tags='ok, <script>')
        self.assertTrue(response.context['form'].has_error('tags'))
        response = self.post(tags=','.join(f't{i}' for i in range(9)))
        self.assertFormError(response.context['form'], 'tags', 'Use no máximo 8 tags.')
        self.assertFalse(Collection.objects.exists())


class ItemExtraFieldsTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.collection = Collection.objects.create(user=self.ana, name='Bonecas', category='brinquedos')

    def test_salva_campos_fixos_e_abre_a_ficha(self):
        self.client.post(reverse('item_create', args=[self.collection.pk]), {
            'name': 'Draculaura', 'edition': '13 Wishes', 'year': '2013',
            'condition': 'excelente', 'location': 'Estante 02', 'description': 'Lacrada',
        })
        item = CollectionItem.objects.get()
        self.assertEqual(
            (item.edition, item.year, item.condition, item.location),
            ('13 Wishes', 2013, 'excelente', 'Estante 02'),
        )
        response = self.client.get(reverse('item_detail', args=[item.pk]))
        self.assertContains(response, 'Excelente')
        self.assertContains(response, 'Estante 02')

    def test_recusa_estado_fora_da_lista_e_ano_invalido(self):
        response = self.client.post(reverse('item_create', args=[self.collection.pk]), {
            'name': 'X', 'condition': 'novinho', 'year': '99999',
        })
        form = response.context['form']
        self.assertTrue(form.has_error('condition'))
        self.assertTrue(form.has_error('year'))
        self.assertFalse(CollectionItem.objects.exists())

    def test_continuar_adicionando_volta_para_o_formulario(self):
        url = reverse('item_create', args=[self.collection.pk])
        response = self.client.post(url, {'name': 'Primeira', 'add_another': '1'})
        self.assertRedirects(response, url + '?continuar=1')
        response = self.client.post(url, {'name': 'Segunda'})
        self.assertRedirects(response, reverse('collection_detail', args=[self.collection.pk]))


class CustomFieldTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.collection = Collection.objects.create(user=self.ana, name='Vinis', category='musica')
        self.fields_url = reverse('collection_fields', args=[self.collection.pk])

    def add_field(self, name, field_type='texto'):
        return self.client.post(self.fields_url, {'name': name, 'field_type': field_type})

    def test_cria_campo_e_recusa_nome_repetido_sem_diferenciar_caixa(self):
        self.add_field('Gravadora')
        response = self.add_field('  GRAVADORA ')
        self.assertFormError(response.context['form'], 'name', 'Esta coleção já tem um campo com esse nome.')
        self.assertEqual(self.collection.custom_fields.count(), 1)

    def test_limite_de_campos_por_colecao(self):
        for i in range(CollectionField.MAX_PER_COLLECTION):
            self.add_field(f'Campo {i}')
        response = self.add_field('Um a mais')
        self.assertTrue(response.context['form'].non_field_errors())
        self.assertEqual(self.collection.custom_fields.count(), CollectionField.MAX_PER_COLLECTION)

    def test_valores_texto_e_numero_no_item(self):
        self.add_field('Gravadora')
        self.add_field('Tiragem', 'numero')
        gravadora, tiragem = self.collection.custom_fields.all()
        url = reverse('item_create', args=[self.collection.pk])

        response = self.client.post(url, {'name': 'X', f'custom_{tiragem.pk}': 'mil'})
        self.assertTrue(response.context['form'].has_error(f'custom_{tiragem.pk}'))

        self.client.post(url, {
            'name': 'Kind of Blue', f'custom_{gravadora.pk}': 'Columbia', f'custom_{tiragem.pk}': '1500,50',
        })
        item = CollectionItem.objects.get()
        values = {v.field.name: v.value for v in item.field_values.all()}
        self.assertEqual(values, {'Gravadora': 'Columbia', 'Tiragem': '1500,5'})

        # Apagar o valor no formulário remove o registro
        self.client.post(reverse('item_update', args=[item.pk]), {
            'name': 'Kind of Blue', f'custom_{gravadora.pk}': '', f'custom_{tiragem.pk}': '1500,5',
        })
        self.assertEqual([v.field.name for v in item.field_values.all()], ['Tiragem'])

    def test_renomear_mantem_valores_e_tipo_nao_muda(self):
        self.add_field('Tiragem', 'numero')
        field = self.collection.custom_fields.get()
        item = CollectionItem.objects.create(collection=self.collection, name='Disco')
        ItemFieldValue.objects.create(item=item, field=field, value='300')

        self.client.post(reverse('field_update', args=[field.pk]), {'name': 'Nº de cópias', 'field_type': 'texto'})
        field.refresh_from_db()
        self.assertEqual((field.name, field.field_type), ('Nº de cópias', 'numero'))
        self.assertEqual(item.field_values.get().value, '300')

    def test_excluir_campo_apaga_os_valores(self):
        self.add_field('Gravadora')
        field = self.collection.custom_fields.get()
        item = CollectionItem.objects.create(collection=self.collection, name='Disco')
        ItemFieldValue.objects.create(item=item, field=field, value='Blue Note')
        self.assertContains(self.client.get(reverse('field_delete', args=[field.pk])), '1 item tem este campo')
        self.client.post(reverse('field_delete', args=[field.pk]))
        self.assertFalse(ItemFieldValue.objects.exists())


class CustomFieldAccessTests(BaseTestCase):
    """Campos personalizados seguem o mesmo isolamento: dados da Ana são invisíveis para a Bia."""

    def setUp(self):
        super().setUp()
        self.collection = Collection.objects.create(user=self.ana, name='Da Ana', category='musica')
        self.field = CollectionField.objects.create(collection=self.collection, name='Gravadora')
        self.item = CollectionItem.objects.create(collection=self.collection, name='Item da Ana')
        self.client.force_login(self.bia)

    def test_bia_nao_gerencia_campos_da_ana(self):
        fields_url = reverse('collection_fields', args=[self.collection.pk])
        self.assertEqual(self.client.get(fields_url).status_code, 404)
        self.assertEqual(self.client.post(fields_url, {'name': 'Intruso', 'field_type': 'texto'}).status_code, 404)
        self.assertEqual(self.client.post(reverse('field_update', args=[self.field.pk]), {'name': 'Hack'}).status_code, 404)
        self.assertEqual(self.client.post(reverse('field_delete', args=[self.field.pk])).status_code, 404)
        self.field.refresh_from_db()
        self.assertEqual(self.field.name, 'Gravadora')
        self.assertEqual(CollectionField.objects.count(), 1)

    def test_bia_nao_ve_a_ficha_do_item_da_ana(self):
        self.assertEqual(self.client.get(reverse('item_detail', args=[self.item.pk])).status_code, 404)

    def test_campo_de_outra_colecao_enviado_no_post_e_ignorado(self):
        da_bia = Collection.objects.create(user=self.bia, name='Da Bia', category='arte')
        self.client.post(reverse('item_create', args=[da_bia.pk]), {
            'name': 'Item da Bia', f'custom_{self.field.pk}': 'valor injetado',
        })
        self.assertTrue(CollectionItem.objects.filter(name='Item da Bia').exists())
        self.assertFalse(ItemFieldValue.objects.exists())


class CollectionDetailFilterTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.collection = Collection.objects.create(user=self.ana, name='Bonecas', category='brinquedos')
        make = CollectionItem.objects.create
        make(collection=self.collection, name='Clawdeen', condition='bom', edition='Basic', year=2010)
        make(collection=self.collection, name='Abbey', condition='excelente', edition='13 Wishes', year=2013)
        make(collection=self.collection, name='Draculaura', condition='excelente', edition='Basic')
        self.url = reverse('collection_detail', args=[self.collection.pk])

    def names(self, **params):
        return [i.name for i in self.client.get(self.url, params).context['items']]

    def test_filtros_e_ordenacao(self):
        self.assertEqual(self.names(estado='excelente', ordem='nome'), ['Abbey', 'Draculaura'])
        self.assertEqual(self.names(edicao='basic', ordem='nome'), ['Clawdeen', 'Draculaura'])
        self.assertEqual(self.names(ordem='ano'), ['Clawdeen', 'Abbey', 'Draculaura'])  # sem ano vai por último

    def test_parametros_invalidos_sao_ignorados(self):
        response = self.client.get(self.url, {'estado': "x' OR 1=1", 'ordem': 'password'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['items']), 3)

    def test_resumo_por_estado(self):
        response = self.client.get(self.url)
        self.assertEqual(
            [(value, total) for value, _, total in response.context['condition_summary']],
            [('excelente', 2), ('bom', 1)],
        )


class SearchExtraTests(BaseTestCase):
    def test_busca_por_tag_e_por_edicao(self):
        vinis = Collection.objects.create(user=self.ana, name='Vinis', category='musica', tags='rara,jazz')
        CollectionItem.objects.create(collection=vinis, name='Disco', edition='Primeira prensagem')
        Collection.objects.create(user=self.bia, name='Da Bia', category='musica', tags='rara')

        response = self.client.get(reverse('search'), {'q': '#rara'})
        self.assertEqual([c.name for c in response.context['collections']], ['Vinis'])

        response = self.client.get(reverse('search'), {'q': 'prensagem'})
        self.assertEqual([i.name for i in response.context['items']], ['Disco'])


class LiveSearchTests(BaseTestCase):
    """Busca em tempo real (?parcial=1): mesmo isolamento da busca completa, só um trecho de HTML."""

    def test_trecho_so_com_dados_do_usuario_e_limitado(self):
        vinis = Collection.objects.create(user=self.ana, name='Vinis', category='musica')
        for n in range(7):
            CollectionItem.objects.create(collection=vinis, name=f'Disco {n}')
        bia = Collection.objects.create(user=self.bia, name='Discos da Bia', category='musica')
        CollectionItem.objects.create(collection=bia, name='Disco secreto da Bia')

        response = self.client.get(reverse('search'), {'q': 'disco', 'parcial': '1'})
        self.assertTemplateUsed(response, 'partials/search_live.html')
        self.assertTemplateNotUsed(response, 'app_base.html')
        self.assertEqual(len(response.context['items']), 5)
        self.assertEqual(response.context['total'], 7)
        self.assertNotContains(response, 'Bia')
        self.assertContains(response, 'Ver todos os 7 resultados')

    def test_trecho_escapa_o_termo_e_mostra_estado_vazio(self):
        response = self.client.get(reverse('search'), {'q': '<script>x</script>', 'parcial': '1'})
        self.assertContains(response, 'Nada encontrado')
        self.assertNotContains(response, '<script>x</script>')
        self.assertContains(response, '&lt;script&gt;')

    def test_trecho_exige_login(self):
        self.client.logout()
        response = self.client.get(reverse('search'), {'q': 'disco', 'parcial': '1'})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response['Location'])


class DeleteModalTests(BaseTestCase):
    def test_link_de_exclusao_tem_modal_e_mantem_pagina_de_confirmacao(self):
        vinis = Collection.objects.create(user=self.ana, name='Vinis <b>raros</b>', category='musica')
        CollectionItem.objects.create(collection=vinis, name='Disco')
        response = self.client.get(reverse('collection_detail', args=[vinis.pk]))
        # Sem JS o link continua levando à página de confirmação (GET não exclui nada)
        self.assertContains(response, f'href="{reverse("collection_delete", args=[vinis.pk])}" data-confirm=')
        self.assertContains(response, 'data-confirm-name="Vinis &lt;b&gt;raros&lt;/b&gt;" data-confirm-text="1 item será excluído junto com ela."')
        # Nome escapado dentro do atributo; o modal envia POST com token CSRF
        self.assertContains(response, 'Vinis &lt;b&gt;raros&lt;/b&gt;')
        self.assertContains(response, '<dialog class="modal" id="modal-excluir"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')


class CollectionFormRequiredTests(BaseTestCase):
    def test_categoria_comeca_vazia_e_e_obrigatoria(self):
        response = self.client.get(reverse('collection_create'))
        self.assertContains(response, '<option value="" selected>Selecione uma categoria</option>', html=True)

        response = self.client.post(reverse('collection_create'), {'name': 'Só o nome'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('category', response.context['form'].errors)
        self.assertFalse(Collection.objects.exists())

    def test_avisa_que_a_imagem_precisa_ser_escolhida_de_novo(self):
        response = self.client.post(reverse('collection_create'), {
            'name': 'Vinis', 'category': 'musica', 'tags': 'tag inválida!', 'cover': _image_file('capa.png'),
        })
        self.assertContains(response, 'A imagem não foi salva porque o formulário tinha erros')


class SeedDemoTests(TestCase):
    def run_seed(self, *args):
        import shutil
        import tempfile
        from io import StringIO

        from django.core.management import call_command
        from django.test import override_settings

        media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media, ignore_errors=True)
        out = StringIO()
        with override_settings(DEBUG=True, MEDIA_ROOT=media):
            call_command('seed_demo', *args, stdout=out)
        return out.getvalue()

    def test_recusa_rodar_fora_do_modo_de_desenvolvimento(self):
        from django.core.management import CommandError, call_command

        with self.assertRaises(CommandError):
            call_command('seed_demo')  # o executor de testes roda com DEBUG=False
        self.assertFalse(get_user_model().objects.exists())

    def test_cria_acervo_com_senhas_aleatorias_e_reset_nao_duplica(self):
        output = self.run_seed()
        ana = get_user_model().objects.get(email='ana@demo.coletta.local')
        self.assertEqual(ana.collections.count(), 7)
        self.assertTrue(CollectionItem.objects.filter(collection__user=ana).count() > 20)
        self.assertTrue(ItemFieldValue.objects.exists())
        # Senha aleatória, mostrada só no terminal, e funcionando
        password = output.split('senha: ')[1].split()[0]
        self.assertTrue(ana.check_password(password))

        self.run_seed('--reset')
        self.assertEqual(get_user_model().objects.count(), 2)
        self.assertEqual(Collection.objects.filter(user__email='ana@demo.coletta.local').count(), 7)


class FirstNamesFilterTests(TestCase):
    def test_primeiros_nomes(self):
        from colecoes.templatetags.colecoes_extras import primeiros_nomes

        self.assertEqual(primeiros_nomes('Lauanny Rodrigues Barreto'), 'Lauanny Rodrigues')
        self.assertEqual(primeiros_nomes('Maria da Silva Lima'), 'Maria da Silva')
        self.assertEqual(primeiros_nomes('Ana'), 'Ana')
        self.assertEqual(primeiros_nomes(''), '')


class ReturnToItemFormTests(BaseTestCase):
    """?voltar= na página de campos: só aceita o formulário de item da própria coleção (sem open redirect)."""

    def setUp(self):
        super().setUp()
        self.vinis = Collection.objects.create(user=self.ana, name='Vinis', category='musica')
        self.outra = Collection.objects.create(user=self.ana, name='Outra', category='outros')
        self.item = CollectionItem.objects.create(collection=self.vinis, name='Disco')
        self.fields_url = reverse('collection_fields', args=[self.vinis.pk])

    def return_url(self, voltar):
        return self.client.get(self.fields_url, {'voltar': voltar}).context['return_url']

    def test_aceita_cadastro_e_edicao_de_item_desta_colecao(self):
        create = reverse('item_create', args=[self.vinis.pk])
        update = reverse('item_update', args=[self.item.pk])
        self.assertEqual(self.return_url(create), create)
        self.assertEqual(self.return_url(update + '?x=1'), update)

    def test_ignora_enderecos_externos_e_de_outras_colecoes_ou_contas(self):
        bia_collection = Collection.objects.create(user=self.bia, name='Da Bia', category='outros')
        bia_item = CollectionItem.objects.create(collection=bia_collection, name='Item da Bia')
        for voltar in [
            'https://site-malicioso.com/', '//site-malicioso.com/', 'javascript:alert(1)',
            reverse('item_create', args=[self.outra.pk]),
            reverse('item_update', args=[bia_item.pk]),
            reverse('collection_list'), '/nao-existe/',
        ]:
            self.assertEqual(self.return_url(voltar), '', voltar)

    def test_criar_campo_mantem_o_caminho_de_volta(self):
        create = reverse('item_create', args=[self.vinis.pk])
        response = self.client.post(f'{self.fields_url}?voltar={create}', {'name': 'Gravadora', 'field_type': 'texto'})
        self.assertRedirects(response, f'{self.fields_url}?voltar={create.replace("/", "%2F")}')
        response = self.client.get(response['Location'])
        self.assertContains(response, 'Voltar ao item')
        self.assertContains(response, f'href="{create}"')

    def test_formulario_de_item_aponta_para_campos_com_volta_e_rascunho(self):
        create = reverse('item_create', args=[self.vinis.pk])
        response = self.client.get(create)
        self.assertContains(response, f'{self.fields_url}?voltar={create}')
        self.assertContains(response, f'data-draft="item-{self.vinis.pk}-novo"')
        # Formulário que voltou do servidor com erro não usa rascunho (os dados já estão nele)
        response = self.client.post(create, {'name': ''})
        self.assertNotContains(response, 'data-draft=')
