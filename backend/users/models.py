from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ("username",)

    email = models.EmailField(
        max_length=200,
        unique=True,
        verbose_name="Почта"
    )
    username = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='Логин'
    )
    first_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Фамилия'
    )


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="follower"
    )
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="following"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following']
            )
        ]
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
