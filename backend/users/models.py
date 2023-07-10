from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ("username",)

    email = models.EmailField(
        max_length=200,
        unique=True,
        blank=False,
        verbose_name="Почта"
    )
    username = models.CharField(
        max_length=200,
        unique=True,
        blank=False,
        verbose_name='Логин'
    )
    first_name = models.CharField(
        max_length=200,
        blank=False,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=200,
        blank=False,
        verbose_name='Фамилия'
    )
    password = models.CharField(
        'Пароль',
        max_length=150,
        blank=False,
        null=False,
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='Subscribeers',
        verbose_name='Пользователь',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='Subscribeing',
        verbose_name='Автор',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'
