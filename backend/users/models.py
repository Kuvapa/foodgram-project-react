"""Models for Users app."""
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    """Модель пользователя."""

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

    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
        'email',
        'password'
    ]
    USERNAME_FIELD = 'email'

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
        verbose_name='Папищек',
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "following"],
                                    name="user_following"),
            models.CheckConstraint(
                check=~models.Q(user=models.F('following')),
                name='not_self_following_author'
            )
        ]
