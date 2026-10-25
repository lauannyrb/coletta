from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, name, password, **extra_fields):
        if not email:
            raise ValueError('O e-mail é obrigatório.')
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, name, password, **extra_fields)

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields['is_staff'] = True
        extra_fields['is_superuser'] = True
        return self._create_user(email, name, password, **extra_fields)

    def get_by_natural_key(self, email):
        # Login sem diferenciar maiúsculas/minúsculas (RN01)
        return self.get(email__iexact=email)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField('e-mail', unique=True)
    name = models.CharField('nome', max_length=150)
    is_active = models.BooleanField('ativo', default=True)
    is_staff = models.BooleanField('equipe', default=False)
    date_joined = models.DateTimeField('data de cadastro', default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        verbose_name = 'usuário'
        verbose_name_plural = 'usuários'

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        # E-mail sempre em minúsculas: o unique do banco passa a valer sem diferenciar caixa (RN01)
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)
