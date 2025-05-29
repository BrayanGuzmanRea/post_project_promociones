from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Usuario, Rol, Empresa, Sucursal, CanalCliente, Cliente, Articulo
from core.models import Cliente, Usuario, Promocion

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

# Admin personalizado para Usuario
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
admin.site.register(Rol)  # Registro de roles para administración
admin.site.register(Promocion)

# Admin personalizado para Empresa
@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('empresa_id', 'nombre')
    search_fields = ('nombre',)

# Admin personalizado para Sucursal
@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ('sucursal_id', 'nombre', 'empresa')
    list_filter = ('empresa',)
    search_fields = ('nombre',)

# Admin personalizado para CanalCliente
@admin.register(CanalCliente)
class CanalClienteAdmin(admin.ModelAdmin):
    list_display = ('canal_cliente_id', 'nombre')
    search_fields = ('nombre',)
 

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar usuarios cuyo rol sea el ID 5
        self.fields['usuario'].queryset = Usuario.objects.filter(rol_id=5)


# lo faltante para lo de brayan:
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    form = ClienteForm
    list_display = ('cliente_id', 'usuario', 'canal_cliente')
    search_fields = ('usuario__username', 'usuario__nombre')
    list_filter = ('canal_cliente',)

@admin.register(Articulo)
class ArticuloAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descripcion', 'empresa', 'sucursal', 'grupo_proveedor', 'linea_articulo', 'precio', 'estado')
    list_filter = ('empresa', 'sucursal', 'grupo_proveedor', 'linea_articulo', 'estado')
    search_fields = ('codigo', 'descripcion', 'codigo_barras', 'codigo_ean')
    ordering = ('codigo',)
