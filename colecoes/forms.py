import re

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .images import process_cover
from .models import Collection, CollectionField, CollectionItem, ItemFieldValue

# Nunca incluir `user` ou `collection` nos campos: o dono e a coleção vêm sempre do back-end (RN09, RN18)

TAG_PATTERN = re.compile(r'^[\w-]{1,30}$')
MAX_TAGS = 8


def normalize_tags(raw):
    """'#Rara, anos 2000, rara' -> 'rara,anos-2000' (minúsculas, sem '#', sem repetição)."""
    tags = []
    for part in (raw or '').split(','):
        tag = '-'.join(part.strip().lstrip('#').lower().split())
        if not tag:
            continue
        if not TAG_PATTERN.match(tag):
            raise ValidationError(
                f'Tag inválida: “{tag[:30]}”. Use letras, números e hífen (até 30 caracteres).'
            )
        if tag not in tags:
            tags.append(tag)
    if len(tags) > MAX_TAGS:
        raise ValidationError(f'Use no máximo {MAX_TAGS} tags.')
    return ','.join(tags)


class CollectionForm(forms.ModelForm):
    # Campo próprio (e não o do modelo) para passar sempre pelo process_cover e não exibir o
    # caminho do arquivo, como o widget padrão do Django faria
    cover = forms.FileField(
        label='Enviar imagem',
        required=False,
        help_text='JPG, PNG ou WEBP, até 2 MB. Opcional.',
        widget=forms.FileInput(attrs={'accept': 'image/jpeg,image/png,image/webp', 'class': 'cover-input'}),
    )
    remove_cover = forms.BooleanField(label='Remover a capa atual', required=False)

    class Meta:
        model = Collection
        fields = ('name', 'category', 'start_year', 'tags', 'description')
        help_texts = {
            'name': 'Escolha um título representativo e fácil de reconhecer.',
            'tags': 'Separe por vírgula. Até 8 tags.',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Ex.: Monster High — Primeiras edições',
                'autofocus': True,
            }),
            'start_year': forms.NumberInput(attrs={'placeholder': 'Ex.: 2019'}),
            'tags': forms.TextInput(attrs={'placeholder': 'Ex.: anos-2000, rara, importados'}),
            'description': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Conte a história por trás desta coleção, critérios de aquisição, '
                               'edições de interesse ou memórias de valor afetivo (opcional)',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._old_cover = self.instance.cover.name if self.instance.pk else ''
        if self.instance.pk:
            self.initial['tags'] = ', '.join(self.instance.tag_list)

    def clean_start_year(self):
        year = self.cleaned_data.get('start_year')
        if year and year > timezone.localdate().year:
            raise ValidationError('O ano de início não pode estar no futuro.')
        return year

    def clean_tags(self):
        return normalize_tags(self.cleaned_data.get('tags'))

    def clean_cover(self):
        uploaded = self.cleaned_data.get('cover')
        return process_cover(uploaded) if uploaded else None

    def save(self, commit=True):
        collection = super().save(commit=False)
        new_cover = self.cleaned_data.get('cover')
        if new_cover:
            collection.cover = new_cover
        elif self.cleaned_data.get('remove_cover'):
            collection.cover = ''
        if commit:
            collection.save()
            # Apaga do disco a capa substituída ou removida
            if self._old_cover and self._old_cover != collection.cover.name:
                collection.cover.storage.delete(self._old_cover)
        return collection


class CollectionItemForm(forms.ModelForm):
    """Formulário do item com os campos fixos + os campos personalizados da coleção."""

    class Meta:
        model = CollectionItem
        fields = ('name', 'edition', 'year', 'condition', 'location', 'description')
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Ex.: Draculaura — Edição 13 Wishes (2013)',
                'autofocus': True,
            }),
            'edition': forms.TextInput(attrs={'placeholder': 'Ex.: 13 Wishes, 1ª prensagem'}),
            'year': forms.NumberInput(attrs={'placeholder': 'Ex.: 2013'}),
            'location': forms.TextInput(attrs={'placeholder': 'Ex.: Estante 02 — Prateleira 3'}),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Histórico, estado da caixa, acessórios, como foi adquirido... (opcional)',
            }),
        }

    def __init__(self, *args, collection, **kwargs):
        super().__init__(*args, **kwargs)
        # A coleção vem da view (já validada pelo dono), nunca do formulário
        self.collection = collection
        self.fields['condition'].choices = [('', 'Não informado')] + list(CollectionItem.Condition.choices)

        # Só os campos da coleção do item: um ID de campo de outra coleção enviado no POST é ignorado
        self.custom_fields = list(collection.custom_fields.all())
        current = {}
        if self.instance.pk:
            current = {v.field_id: v.value for v in self.instance.field_values.all()}
        for field in self.custom_fields:
            if field.field_type == CollectionField.FieldType.NUMBER:
                form_field = forms.DecimalField(
                    label=field.name, required=False, max_digits=18, decimal_places=4, localize=True,
                    widget=forms.TextInput(attrs={'inputmode': 'decimal', 'placeholder': 'Número'}),
                )
            else:
                form_field = forms.CharField(
                    label=field.name, required=False, max_length=200,
                    widget=forms.TextInput(attrs={'placeholder': 'Opcional'}),
                )
            form_field.initial = current.get(field.pk)
            self.fields[self._key(field)] = form_field

    @staticmethod
    def _key(field):
        return f'custom_{field.pk}'

    @property
    def custom_bound_fields(self):
        return [self[self._key(field)] for field in self.custom_fields]

    def clean_year(self):
        year = self.cleaned_data.get('year')
        if year and year > timezone.localdate().year + 1:
            raise ValidationError('Informe um ano válido.')
        return year

    def save(self, commit=True):
        item = super().save(commit=False)
        item.collection = self.collection
        if commit:
            item.save()
            self._save_custom_values(item)
        return item

    def _save_custom_values(self, item):
        for field in self.custom_fields:
            value = self.cleaned_data.get(self._key(field))
            if value in (None, ''):
                ItemFieldValue.objects.filter(item=item, field=field).delete()
                continue
            if field.field_type == CollectionField.FieldType.NUMBER:
                # Guarda no formato brasileiro, sem notação científica: Decimal('1000') -> '1000'
                value = format(value.normalize(), 'f').replace('.', ',')
            ItemFieldValue.objects.update_or_create(item=item, field=field, defaults={'value': value})


class CollectionFieldForm(forms.ModelForm):
    class Meta:
        model = CollectionField
        fields = ('name', 'field_type')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ex.: Gravadora, Nº de série, Tiragem'}),
        }

    def __init__(self, *args, collection, **kwargs):
        super().__init__(*args, **kwargs)
        self.collection = collection
        if self.instance.pk:
            # Mudar o tipo invalidaria os valores já preenchidos nos itens
            self.fields['field_type'].disabled = True

    def clean_name(self):
        name = self.cleaned_data['name']
        others = self.collection.custom_fields.exclude(pk=self.instance.pk)
        if others.filter(name__iexact=name).exists():
            raise ValidationError('Esta coleção já tem um campo com esse nome.')
        return name

    def clean(self):
        cleaned = super().clean()
        if not self.instance.pk and self.collection.custom_fields.count() >= CollectionField.MAX_PER_COLLECTION:
            raise ValidationError(
                f'Cada coleção pode ter no máximo {CollectionField.MAX_PER_COLLECTION} campos personalizados.'
            )
        return cleaned

    def save(self, commit=True):
        field = super().save(commit=False)
        field.collection = self.collection
        if commit:
            field.save()
        return field
