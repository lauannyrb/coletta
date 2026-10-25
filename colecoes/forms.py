from django import forms

from .models import Collection, CollectionItem

# Nunca incluir `user` ou `collection` nos campos: o dono e a coleção vêm sempre do back-end (RN09, RN18)


class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ('name', 'description')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ex.: Discos de vinil', 'autofocus': True}),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Conte um pouco sobre esta coleção (opcional)',
            }),
        }


class CollectionItemForm(forms.ModelForm):
    class Meta:
        model = CollectionItem
        fields = ('name', 'category', 'description')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ex.: Kind of Blue — Miles Davis', 'autofocus': True}),
            'category': forms.TextInput(attrs={'placeholder': 'Ex.: Jazz, Edição limitada (opcional)'}),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Detalhes, estado de conservação, origem... (opcional)',
            }),
        }
