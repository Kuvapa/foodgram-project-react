"""Models for Users app."""
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    """Модель пользователя."""

    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
    ]
    USERNAME_FIELD = 'email'

    email = models.EmailField(
        unique=True,
        max_length=254,
        verbose_name='Электронная почта',
    )
    username = models.CharField(
        validators=(
            RegexValidator(regex=r'^[\w.@+-]+$',),
            RegexValidator(
                regex=r'^\b(m|M)(e|E)\b',
                inverse_match=True,
                message="""Данное имя пользователя использовать нельзя."""
            ),
        ),
        unique=True,
        max_length=150,
        verbose_name='Имя пользователя',
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия',
    )
    password = models.CharField(max_length=150)

    class Meta:
        """Meta for User."""

        ordering = ('id',)

    def __str__(self):
        """__str__ for User."""
        return self.username


class Follow(models.Model):
    """Модель фоллова."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Автор',
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписчик',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["author", "following"],
                                    name="user_following"),
            models.CheckConstraint(
                check=~models.Q(author=models.F('following')),
                name='not_self_following_author'
            )
        ]
