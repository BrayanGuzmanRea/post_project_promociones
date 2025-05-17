from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Usuario, Rol

# Formulario para crear usuarios (incluye campo rol)
class UsuarioCreationForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ('username', 'email', 'nombre', 'rol', 'empresa', 'sucursal')

# Formulario para editar usuarios
class UsuarioChangeForm(UserChangeForm):
    class Meta:
        model = Usuario
        fields = ('username', 'email', 'nombre', 'rol', 'empresa', 'sucursal', 'is_active', 'is_staff', 'is_superuser')

# Admin personalizado
class UsuarioAdmin(BaseUserAdmin):
    add_form = UsuarioCreationForm
    form = UsuarioChangeForm
    model = Usuario
    list_display = ('username', 'email', 'nombre', 'rol', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser', 'rol')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Información Personal', {'fields': ('nombre', 'rol', 'empresa', 'sucursal', 'estado')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'nombre', 'rol', 'empresa', 'sucursal', 'password1', 'password2', 'is_staff', 'is_superuser')}
        ),
    )
    search_fields = ('username', 'email', 'nombre')
    ordering = ('username',)

admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Rol)  # también registra los roles para administrarlos
