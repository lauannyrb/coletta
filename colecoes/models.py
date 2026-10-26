from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.functions import Lower
from django.db.models.signals import post_delete
from django.dispatch import receiver


class Collection(models.Model):
    class Category(models.TextChoices):
        TOYS = 'brinquedos', 'Bonecas & Brinquedos'
        MUSIC = 'musica', 'Música'
        PHOTOGRAPHY = 'fotografia', 'Fotografia'
        BOOKS = 'livros', 'Livros & HQs'
        GAMES = 'jogos', 'Jogos'
        ART = 'arte', 'Arte'
        COINS = 'moedas', 'Moedas & Selos'
        OTHER = 'outros', 'Outros'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='collections',
        verbose_name='usuário',
    )
    name = models.CharField('nome', max_length=100)
    category = models.CharField(
        'categoria principal', max_length=20, choices=Category, default=Category.OTHER,
    )
    start_year = models.PositiveSmallIntegerField(
        'ano de início', null=True, blank=True,
        validators=[MinValueValidator(1900), MaxValueValidator(9999)],
    )
    # Tags normalizadas pelo CollectionForm: minúsculas, sem "#", separadas por vírgula
    tags = models.CharField('tags', max_length=300, blank=True)
    description = models.TextField('descrição', max_length=1000, blank=True)
    # Arquivo fora da pasta pública (MEDIA_ROOT), servido só ao dono por colecoes.views.collection_cover
    cover = models.ImageField('capa', upload_to='capas/', blank=True)
    created_at = models.DateTimeField('criada em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizada em', auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'coleção'
        verbose_name_plural = 'coleções'

    def __str__(self):
        return self.name

    @property
    def tag_list(self):
        return [tag for tag in self.tags.split(',') if tag]


class CollectionItem(models.Model):
    class Condition(models.TextChoices):
        SEALED = 'lacrado', 'Lacrado'
        EXCELLENT = 'excelente', 'Excelente'
        GOOD = 'bom', 'Bom'
        FAIR = 'regular', 'Regular'
        DAMAGED = 'danificado', 'Danificado'

    # Sem campo user: o item pertence ao usuário por meio da coleção (RN19)
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='coleção',
    )
    name = models.CharField('nome', max_length=100)
    edition = models.CharField('subcategoria / edição', max_length=60, blank=True)
    year = models.PositiveSmallIntegerField(
        'ano de lançamento ou aquisição', null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(9999)],
    )
    condition = models.CharField('estado de conservação', max_length=20, choices=Condition, blank=True)
    location = models.CharField('local de guarda', max_length=100, blank=True)
    description = models.TextField('notas do colecionador', max_length=1000, blank=True)
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'item'
        verbose_name_plural = 'itens'

    def __str__(self):
        return self.name


class CollectionField(models.Model):
    """Campo personalizado de uma coleção (ex.: "Gravadora"), preenchido em cada item dela."""

    MAX_PER_COLLECTION = 10

    class FieldType(models.TextChoices):
        TEXT = 'texto', 'Texto'
        NUMBER = 'numero', 'Número'

    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name='custom_fields',
        verbose_name='coleção',
    )
    name = models.CharField('nome do campo', max_length=40)
    field_type = models.CharField('tipo', max_length=10, choices=FieldType, default=FieldType.TEXT)
    created_at = models.DateTimeField('criado em', auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'pk']
        verbose_name = 'campo personalizado'
        verbose_name_plural = 'campos personalizados'
        constraints = [
            # "Gravadora" e "gravadora" seriam o mesmo campo
            models.UniqueConstraint(Lower('name'), 'collection', name='campo_unico_por_colecao'),
        ]

    def __str__(self):
        return self.name


class ItemFieldValue(models.Model):
    """Valor de um campo personalizado em um item. O campo é sempre da coleção do próprio item."""

    item = models.ForeignKey(
        CollectionItem,
        on_delete=models.CASCADE,
        related_name='field_values',
        verbose_name='item',
    )
    field = models.ForeignKey(
        CollectionField,
        on_delete=models.CASCADE,
        related_name='values',
        verbose_name='campo',
    )
    value = models.CharField('valor', max_length=200)

    class Meta:
        ordering = ['field__created_at', 'field__pk']
        verbose_name = 'valor de campo personalizado'
        verbose_name_plural = 'valores de campos personalizados'
        constraints = [
            models.UniqueConstraint(fields=['item', 'field'], name='um_valor_por_campo'),
        ]


@receiver(post_delete, sender=Collection)
def delete_cover_file(sender, instance, **kwargs):
    # Também cobre exclusões em cascata (ex.: usuário removido)
    if instance.cover:
        instance.cover.delete(save=False)
