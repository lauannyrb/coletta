from django.conf import settings
from django.db import models


class Collection(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='collections',
        verbose_name='usuário',
    )
    name = models.CharField('nome', max_length=100)
    description = models.TextField('descrição', max_length=1000, blank=True)
    created_at = models.DateTimeField('criada em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizada em', auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'coleção'
        verbose_name_plural = 'coleções'

    def __str__(self):
        return self.name


class CollectionItem(models.Model):
    # Sem campo user: o item pertence ao usuário por meio da coleção (RN19)
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='coleção',
    )
    name = models.CharField('nome', max_length=100)
    description = models.TextField('descrição', max_length=1000, blank=True)
    category = models.CharField('categoria', max_length=60, blank=True)
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'item'
        verbose_name_plural = 'itens'

    def __str__(self):
        return self.name
