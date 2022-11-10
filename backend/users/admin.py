from django.contrib import admin

from .models import User, Follow


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'email',
        'id',
        'username',
        'first_name',
        'last_name')
    search_fields = ('email', 'username',)
    list_filter = ('email', 'username',)


class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'following',)


admin.site.register(User, UserAdmin)
admin.site.register(Follow, FollowAdmin)

