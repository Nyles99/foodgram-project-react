from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        max_length=200,
        unique=True,
        blank=False,
        verbose_name="Почта",
        null=False
    )
    username = models.CharField(
        max_length=200,
        unique=True,
        blank=False,
        verbose_name='Логин',
        null=False
    )
    first_name = models.CharField(
        max_length=200,
        blank=False,
        verbose_name='Имя',
        null=False
    )
    last_name = models.CharField(
        max_length=200,
        blank=False,
        verbose_name='Фамилия',
        null=False
    )
    password = models.CharField(
        'Пароль',
        max_length=150,
        blank=False,
        null=False,
    )

    class Meta:
        ordering = ['id']
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="followers",
        verbose_name='Пользователь'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
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
