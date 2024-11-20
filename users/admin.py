from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, GPTMessageLog

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['email', 'name', 'is_staff', 'is_active', 'is_superuser']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    search_fields = ['email', 'name']
    ordering = ['email']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )


admin.site.register(User, CustomUserAdmin)
admin.site.register(GPTMessageLog)
