from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError
from django.test import TestCase

User = get_user_model()


class UserModelTests(TestCase):
    def test_email_salvo_em_minusculas(self):
        user = User.objects.create_user('Ana.Silva@Exemplo.COM', 'Ana', 'senha-forte-123')
        self.assertEqual(user.email, 'ana.silva@exemplo.com')

    def test_email_unico_sem_diferenciar_caixa(self):
        User.objects.create_user('ana@exemplo.com', 'Ana', 'senha-forte-123')
        with self.assertRaises(IntegrityError):
            User.objects.create_user('ANA@exemplo.com', 'Outra Ana', 'senha-forte-123')

    def test_login_sem_diferenciar_caixa(self):
        User.objects.create_user('ana@exemplo.com', 'Ana', 'senha-forte-123')
        self.assertIsNotNone(authenticate(username='ANA@Exemplo.com', password='senha-forte-123'))
