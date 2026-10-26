"""Popula o banco de desenvolvimento com um acervo de demonstração.

Uso:  .venv/bin/python manage.py seed_demo [--reset]

- Só roda com DEBUG=True: nunca cria contas de demonstração em produção.
- As senhas são aleatórias, geradas a cada execução e mostradas só no terminal (nada fixo no código).
- Cria a Ana (acervo completo) e a Bia (uma coleção), útil para demonstrar o isolamento (404).
"""
import secrets
from datetime import timedelta
from io import BytesIO
from math import cos, radians, sin

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw

from colecoes.images import process_cover
from colecoes.models import Collection, CollectionField, CollectionItem, ItemFieldValue

DEMO_DOMAIN = 'demo.coletta.local'

# Cada coleção: dados, cores da capa (None = sem capa), campos personalizados e itens.
# Itens: (nome, edição, ano, estado, local, notas, {campo: valor}, dias atrás)
ACERVO = [
    {
        'name': 'Monster High — Primeiras edições',
        'category': 'brinquedos', 'start_year': 2011, 'tags': 'anos-2010,bonecas,mattel',
        'description': 'Bonecas da primeira leva da linha, com foco nas edições de 2010 a 2013. '
                       'Prioridade para peças com caixa e acessórios completos.',
        'cover': ((236, 72, 153), (91, 33, 182), 'estrela'), 'days': 1,
        'fields': [('Personagem', 'texto'), ('Acessórios inclusos', 'numero')],
        'items': [
            ('Draculaura — 13 Wishes', '13 Wishes', 2013, 'lacrado', 'Estante 02 — Prateleira 3',
             'Caixa sem amassados. Comprada em pré-venda.', {'Personagem': 'Draculaura', 'Acessórios inclusos': '6'}, 1),
            ('Frankie Stein — Original', 'Primeira onda', 2010, 'excelente', 'Estante 02 — Prateleira 1',
             'Acompanha o diário e o suporte.', {'Personagem': 'Frankie Stein', 'Acessórios inclusos': '4'}, 3),
            ('Clawdeen Wolf — Sweet 1600', 'Sweet 1600', 2012, 'bom', 'Estante 02 — Prateleira 2',
             'Faltam os brincos.', {'Personagem': 'Clawdeen Wolf', 'Acessórios inclusos': '3'}, 9),
            ('Lagoona Blue — Dead Tired', 'Dead Tired', 2011, 'excelente', 'Estante 02 — Prateleira 2',
             '', {'Personagem': 'Lagoona Blue'}, 15),
            ('Cleo de Nile — Dawn of the Dance', 'Dawn of the Dance', 2011, 'regular', 'Caixa organizadora A',
             'Cabelo precisa de tratamento. Vestido em ótimo estado.', {'Personagem': 'Cleo de Nile', 'Acessórios inclusos': '2'}, 22),
            ('Ghoulia Yelps — Original', 'Primeira onda', 2010, 'danificado', 'Caixa organizadora A',
             'Articulação do braço esquerdo solta. Peça para restauro.', {'Personagem': 'Ghoulia Yelps'}, 40),
        ],
    },
    {
        'name': 'Discos de Vinil — MPB e Jazz',
        'category': 'musica', 'start_year': 2016, 'tags': 'vinil,mpb,jazz,rara',
        'description': 'LPs garimpados em sebos e feiras. Preferência por primeiras prensagens nacionais.',
        'cover': ((249, 115, 22), (127, 29, 29), 'disco'), 'days': 0,
        'fields': [('Gravadora', 'texto'), ('Rotação (RPM)', 'numero')],
        'items': [
            ('Clube da Esquina', '1ª prensagem', 1972, 'excelente', 'Rack da sala — Nicho 1',
             'Encarte original completo.', {'Gravadora': 'EMI-Odeon', 'Rotação (RPM)': '33'}, 0),
            ('Elis & Tom', '1ª prensagem', 1974, 'bom', 'Rack da sala — Nicho 1',
             'Leves chiados no lado B.', {'Gravadora': 'Philips', 'Rotação (RPM)': '33'}, 2),
            ('Kind of Blue', 'Reedição 2015', 1959, 'lacrado', 'Rack da sala — Nicho 2',
             'Edição em vinil 180 g.', {'Gravadora': 'Columbia', 'Rotação (RPM)': '33'}, 4),
            ('Tropicália ou Panis et Circencis', 'Reedição', 1968, 'excelente', 'Rack da sala — Nicho 1',
             '', {'Gravadora': 'Philips', 'Rotação (RPM)': '33'}, 6),
            ('Acabou Chorare', '1ª prensagem', 1972, 'regular', 'Rack da sala — Nicho 3',
             'Capa com desgaste nas bordas.', {'Gravadora': 'Som Livre', 'Rotação (RPM)': '33'}, 11),
            ('Construção', 'Reedição', 1971, 'bom', 'Rack da sala — Nicho 3',
             '', {'Gravadora': 'Philips', 'Rotação (RPM)': '33'}, 18),
            ('A Love Supreme', 'Importado', 1965, 'excelente', 'Rack da sala — Nicho 2',
             'Comprado em viagem. Capa gatefold.', {'Gravadora': 'Impulse!', 'Rotação (RPM)': '33'}, 30),
        ],
    },
    {
        'name': 'Câmeras Analógicas',
        'category': 'fotografia', 'start_year': 2019, 'tags': 'filme-35mm,vintage',
        'description': 'Câmeras de filme funcionando, usadas de verdade nos passeios de fim de semana.',
        'cover': ((120, 113, 108), (41, 37, 36), 'lente'), 'days': 5,
        'fields': [('Formato do filme', 'texto'), ('Lente', 'texto')],
        'items': [
            ('Canon AE-1 Program', 'SLR', 1981, 'excelente', 'Armário do escritório',
             'Fotômetro funcionando. Revisada em 2024.', {'Formato do filme': '35 mm', 'Lente': 'FD 50 mm f/1.8'}, 5),
            ('Pentax K1000', 'SLR', 1976, 'bom', 'Armário do escritório',
             '', {'Formato do filme': '35 mm', 'Lente': 'SMC Pentax-M 50 mm f/2'}, 12),
            ('Olympus Trip 35', 'Compacta', 1968, 'excelente', 'Mochila de viagem',
             'A favorita para viagens.', {'Formato do filme': '35 mm', 'Lente': 'Zuiko 40 mm f/2.8'}, 20),
            ('Zenit 12XP', 'SLR', 1984, 'regular', 'Armário do escritório',
             'Obturador às vezes trava em 1/500.', {'Formato do filme': '35 mm', 'Lente': 'Helios-44M 58 mm f/2'}, 35),
            ('Polaroid SX-70', 'Instantânea', 1972, 'bom', 'Estante 01',
             '', {'Formato do filme': 'Instantâneo SX-70'}, 50),
        ],
    },
    {
        'name': 'Quadrinhos que mudaram tudo',
        'category': 'livros', 'start_year': 2008, 'tags': 'hq,graphic-novel',
        'description': 'Graphic novels e séries marcantes, em edições nacionais.',
        'cover': ((14, 116, 144), (30, 41, 59), 'quadros'), 'days': 14,
        'fields': [('Editora', 'texto'), ('Páginas', 'numero')],
        'items': [
            ('Watchmen', 'Edição definitiva', 1986, 'excelente', 'Estante 01 — Prateleira 2',
             '', {'Editora': 'Panini', 'Páginas': '464'}, 14),
            ('Maus', 'Edição completa', 1991, 'bom', 'Estante 01 — Prateleira 2',
             'Presente de aniversário.', {'Editora': 'Companhia das Letras', 'Páginas': '296'}, 25),
            ('Persépolis', 'Edição completa', 2000, 'excelente', 'Estante 01 — Prateleira 2',
             '', {'Editora': 'Quadrinhos na Cia.', 'Páginas': '352'}, 32),
            ('Sandman — Volume 1', 'Edição de luxo', 1989, 'lacrado', 'Estante 01 — Prateleira 3',
             'Ainda no plástico.', {'Editora': 'Panini', 'Páginas': '616'}, 45),
        ],
    },
    {
        'name': 'Cartuchos de Super Nintendo',
        'category': 'jogos', 'start_year': 2014, 'tags': 'retro,16-bits,anos-90',
        'description': 'Cartuchos originais testados. Os com caixa ficam guardados à parte.',
        'cover': None, 'days': 21,
        'fields': [('Região', 'texto')],
        'items': [
            ('Super Mario World', 'Cartucho solto', 1990, 'bom', 'Gaveta do rack', '', {'Região': 'NTSC-US'}, 21),
            ('Donkey Kong Country', 'Com caixa', 1994, 'excelente', 'Caixa organizadora B',
             'Manual incluso.', {'Região': 'NTSC-US'}, 28),
            ('Chrono Trigger', 'Cartucho solto', 1995, 'regular', 'Gaveta do rack',
             'Bateria do save trocada.', {'Região': 'NTSC-US'}, 60),
            ('Top Gear', 'Cartucho solto', 1992, 'bom', 'Gaveta do rack', '', {'Região': 'NTSC-US'}, 75),
        ],
    },
    {
        'name': 'Moedas comemorativas',
        'category': 'moedas', 'start_year': 2016, 'tags': 'numismatica,brasil',
        'description': 'Moedas de 1 real comemorativas e algumas estrangeiras de viagens.',
        'cover': ((202, 138, 4), (120, 53, 15), 'moeda'), 'days': 33,
        'fields': [('País', 'texto'), ('Valor de face', 'numero')],
        'items': [
            ('1 real — Jogos Olímpicos Rio 2016 (Natação)', 'Série olímpica', 2014, 'excelente', 'Álbum de moedas 1',
             '', {'País': 'Brasil', 'Valor de face': '1'}, 33),
            ('1 real — 50 anos do Banco Central', '', 2015, 'bom', 'Álbum de moedas 1',
             '', {'País': 'Brasil', 'Valor de face': '1'}, 40),
            ('2 euros — Portugal', 'Circulação', 2011, 'regular', 'Pote de viagem',
             'Trazida de Lisboa.', {'País': 'Portugal', 'Valor de face': '2'}, 90),
        ],
    },
    {
        # Coleção vazia, para mostrar o estado "ainda não tem itens"
        'name': 'Xilogravuras de cordel',
        'category': 'arte', 'start_year': None, 'tags': 'nordeste',
        'description': 'Começando agora: gravuras compradas em feiras do Nordeste.',
        'cover': ((101, 163, 13), (20, 83, 45), 'estrela'), 'days': 2,
        'fields': [], 'items': [],
    },
]

ACERVO_BIA = [
    {
        'name': 'Selos do Brasil',
        'category': 'moedas', 'start_year': 2020, 'tags': 'filatelia',
        'description': 'Coleção da Bia: usada para demonstrar que a Ana não consegue abrir esta página (404).',
        'cover': None, 'days': 3, 'fields': [],
        'items': [('Olho-de-boi', 'Réplica', 1843, 'bom', 'Classificador azul', '', {}, 3)],
    },
]


def make_cover(top, bottom, shape):
    """Capa ilustrativa (gradiente + figura simples), passando pelo mesmo process_cover do upload."""
    width, height = 1200, 675
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)
    for y in range(height):
        t = y / (height - 1)
        draw.line([(0, y), (width, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)))

    white = (255, 255, 255)
    cx, cy = width // 2, height // 2
    if shape == 'disco':
        for r in (230, 170, 110):
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=white, width=6)
        draw.ellipse([cx - 40, cy - 40, cx + 40, cy + 40], fill=white)
    elif shape == 'lente':
        draw.rounded_rectangle([cx - 300, cy - 170, cx + 300, cy + 190], radius=40, outline=white, width=12)
        draw.ellipse([cx - 130, cy - 120, cx + 130, cy + 140], outline=white, width=12)
        draw.ellipse([cx - 60, cy - 50, cx + 60, cy + 70], outline=white, width=8)
    elif shape == 'quadros':
        for x, y in [(-280, -170), (20, -170), (-280, 20), (20, 20)]:
            draw.rounded_rectangle([cx + x, cy + y, cx + x + 260, cy + y + 160], radius=18, outline=white, width=10)
    elif shape == 'moeda':
        draw.ellipse([cx - 200, cy - 200, cx + 200, cy + 200], outline=white, width=14)
        draw.ellipse([cx - 150, cy - 150, cx + 150, cy + 150], outline=white, width=5)
    else:  # estrela do Brand Guide
        points = []
        for i in range(10):
            radius = 210 if i % 2 == 0 else 90
            angle = radians(-90 + i * 36)
            points.append((cx + radius * cos(angle), cy + radius * sin(angle)))
        draw.polygon(points, outline=white, width=12)

    buffer = BytesIO()
    image.save(buffer, format='PNG')
    return process_cover(SimpleUploadedFile('capa.png', buffer.getvalue(), content_type='image/png'))


class Command(BaseCommand):
    help = 'Cria usuárias e um acervo de demonstração (somente com DEBUG=True).'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true',
                            help='Apaga as usuárias de demonstração existentes e cria tudo de novo.')

    def handle(self, *args, reset=False, **options):
        if not settings.DEBUG:
            raise CommandError('seed_demo só roda em desenvolvimento (DEBUG=True). Nunca em produção.')

        User = get_user_model()
        demo_users = User.objects.filter(email__endswith=f'@{DEMO_DOMAIN}')
        if demo_users.exists():
            if not reset:
                raise CommandError('O acervo de demonstração já existe. Use --reset para recriar.')
            for user in demo_users:
                # Um a um para disparar o post_delete que apaga os arquivos das capas
                for collection in user.collections.all():
                    collection.delete()
                user.delete()

        with transaction.atomic():
            ana, ana_password = self._create_user(f'ana@{DEMO_DOMAIN}', 'Ana Beatriz')
            bia, bia_password = self._create_user(f'bia@{DEMO_DOMAIN}', 'Bia Santos')
            total_items = self._create_collections(ana, ACERVO)
            self._create_collections(bia, ACERVO_BIA)

        bia_collection = bia.collections.get()
        self.stdout.write(self.style.SUCCESS(
            f'Acervo criado: {len(ACERVO)} coleções e {total_items} itens para a Ana.'
        ))
        self.stdout.write('\nContas de demonstração (senhas novas a cada execução, guarde agora):')
        self.stdout.write(f'  Ana  {ana.email}  senha: {ana_password}')
        self.stdout.write(f'  Bia  {bia.email}  senha: {bia_password}')
        self.stdout.write(
            f'\nTeste de isolamento: entre como Ana e abra /colecoes/{bia_collection.pk}/ (coleção da Bia) → 404.'
        )

    def _create_user(self, email, name):
        password = secrets.token_urlsafe(12)
        return get_user_model().objects.create_user(email, name, password), password

    def _create_collections(self, user, acervo):
        now = timezone.now()
        total_items = 0
        for data in acervo:
            collection = Collection.objects.create(
                user=user, name=data['name'], category=data['category'], start_year=data['start_year'],
                tags=data['tags'], description=data['description'],
                cover=make_cover(*data['cover']) if data['cover'] else '',
            )
            fields = {
                name: CollectionField.objects.create(collection=collection, name=name, field_type=field_type)
                for name, field_type in data['fields']
            }
            for name, edition, year, condition, location, notes, values, days in data['items']:
                item = CollectionItem.objects.create(
                    collection=collection, name=name, edition=edition, year=year, condition=condition,
                    location=location, description=notes,
                )
                for field_name, value in values.items():
                    ItemFieldValue.objects.create(item=item, field=fields[field_name], value=value)
                # Datas espalhadas para a tela mostrar "há 3 dias", "+N este mês" etc.
                moment = now - timedelta(days=days, hours=len(name) % 7)
                CollectionItem.objects.filter(pk=item.pk).update(created_at=moment, updated_at=moment)
                total_items += 1

            moment = now - timedelta(days=data['days'], minutes=len(data['name']))
            Collection.objects.filter(pk=collection.pk).update(
                created_at=moment - timedelta(days=120), updated_at=moment,
            )
        return total_items
