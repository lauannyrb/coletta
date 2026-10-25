from django.contrib.auth import authenticate, get_user_model
from django.core.cache import cache
from django.db import IntegrityError
from django.test import RequestFactory, TestCase
from django.urls import reverse

User = get_user_model()

PASSWORD = 'Colecao-Segura-2026'


class UserModelTests(TestCase):
    def test_email_salvo_em_minusculas(self):
        user = User.objects.create_user('Ana.Silva@Exemplo.COM', 'Ana', PASSWORD)
        self.assertEqual(user.email, 'ana.silva@exemplo.com')

    def test_email_unico_sem_diferenciar_caixa(self):
        User.objects.create_user('ana@exemplo.com', 'Ana', PASSWORD)
        with self.assertRaises(IntegrityError):
            User.objects.create_user('ANA@exemplo.com', 'Outra Ana', PASSWORD)

    def test_login_sem_diferenciar_caixa(self):
        User.objects.create_user('ana@exemplo.com', 'Ana', PASSWORD)
        # O backend do django-axes exige o request
        request = RequestFactory().post(reverse('login'))
        user = authenticate(request, username='ANA@Exemplo.com', password=PASSWORD)
        self.assertIsNotNone(user)


class SignUpTests(TestCase):
    def setUp(self):
        cache.clear()

    def signup(self, **overrides):
        data = {
            'name': 'Ana Silva',
            'email': 'ana@exemplo.com',
            'password1': PASSWORD,
            'password2': PASSWORD,
            **overrides,
        }
        return self.client.post(reverse('signup'), data)

    def test_cadastro_valido_cria_usuario_e_faz_login(self):
        response = self.signup()
        self.assertRedirects(response, reverse('home'))
        user = User.objects.get(email='ana@exemplo.com')
        self.assertEqual(user.name, 'Ana Silva')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_recusa_email_duplicado_com_caixa_diferente(self):
        User.objects.create_user('ana@exemplo.com', 'Ana', PASSWORD)
        response = self.signup(email='ANA@Exemplo.com')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Já existe uma conta com este e-mail.')
        self.assertEqual(User.objects.count(), 1)

    def test_recusa_campos_obrigatorios_vazios_ou_so_espacos(self):
        response = self.signup(name='   ', email='')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.exists())
        self.assertFormError(response.context['form'], 'name', 'Este campo é obrigatório.')
        self.assertFormError(response.context['form'], 'email', 'Este campo é obrigatório.')

    def test_recusa_email_invalido(self):
        response = self.signup(email='nao-e-email')
        self.assertFalse(User.objects.exists())
        self.assertTrue(response.context['form'].has_error('email'))

    def test_recusa_senha_fraca(self):
        response = self.signup(password1='12345678', password2='12345678')
        self.assertFalse(User.objects.exists())
        self.assertTrue(response.context['form'].has_error('password2'))

    def test_recusa_senhas_diferentes(self):
        response = self.signup(password2='Outra-Senha-2026')
        self.assertFalse(User.objects.exists())
        self.assertTrue(response.context['form'].has_error('password2'))

    def test_rate_limit_do_cadastro(self):
        for i in range(10):
            self.signup(email=f'pessoa{i}@exemplo.com', password2='diferente')
        response = self.signup(email='mais-uma@exemplo.com')
        self.assertEqual(response.status_code, 429)
        self.assertFalse(User.objects.filter(email='mais-uma@exemplo.com').exists())


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ana@exemplo.com', 'Ana', PASSWORD)

    def login(self, email='ana@exemplo.com', password=PASSWORD):
        return self.client.post(reverse('login'), {'username': email, 'password': password})

    def test_login_correto(self):
        response = self.login(email='Ana@Exemplo.com')
        self.assertRedirects(response, reverse('home'))

    def test_login_incorreto_mostra_mensagem_generica(self):
        senha_errada = self.login(password='senha-errada')
        email_inexistente = self.login(email='ninguem@exemplo.com')
        for response in (senha_errada, email_inexistente):
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'E-mail ou senha inválidos.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_home_exige_login(self):
        response = self.client.get(reverse('home'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('home')}")

    def test_logout_por_get_nao_e_permitido(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)

    def test_logout_encerra_sessao_e_bloqueia_paginas_privadas(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 302)

    def test_bloqueio_apos_5_tentativas_erradas(self):
        for _ in range(5):
            self.login(password='senha-errada')
        # Mesmo com a senha certa, o IP continua bloqueado
        response = self.login()
        self.assertEqual(response.status_code, 429)
        self.assertNotIn('_auth_user_id', self.client.session)
