from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, BaseUserCreationForm, UsernameField

User = get_user_model()


class SignUpForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ('name', 'email')
        widgets = {
            'name': forms.TextInput(attrs={'autocomplete': 'name', 'placeholder': 'Como devemos te chamar?'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'voce@exemplo.com'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # O form base coloca o foco no e-mail (USERNAME_FIELD); aqui o primeiro campo é o nome
        self.fields['email'].widget.attrs.pop('autofocus', None)
        self.fields['name'].widget.attrs['autofocus'] = True

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Já existe uma conta com este e-mail.')
        return email


class LoginForm(AuthenticationForm):
    username = UsernameField(
        label='E-mail',
        widget=forms.EmailInput(attrs={
            'autofocus': True,
            'autocomplete': 'email',
            'placeholder': 'voce@exemplo.com',
        }),
    )

    error_messages = {
        **AuthenticationForm.error_messages,
        # Mensagem genérica: não revela se o erro foi no e-mail ou na senha (RN03)
        'invalid_login': 'E-mail ou senha inválidos.',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].widget.attrs['placeholder'] = 'Sua senha'
