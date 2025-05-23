from django import forms
from .models import Sucursal, Usuario, Rol
from .models import Articulo, Promocion

class UsuarioForm(forms.ModelForm):
    rol = forms.ModelChoiceField(
        queryset=Rol.objects.all(),
        label="Rol",
        empty_label="Seleccione un rol",
        required=True
    )

    class Meta:
        model = Usuario
        fields = ['nombre', 'email', 'password', 'rol', 'empresa', 'sucursal', 'estado']
        widgets = {
            'password': forms.PasswordInput(),
        }


from django import forms
from .models import Articulo

class ArticuloForm(forms.ModelForm):
    class Meta:
        model = Articulo
        fields = [
            'empresa',
            'codigo',
            'codigo_barras',
            'codigo_ean',
            'descripcion',
            'grupo_proveedor',
            'linea_articulo',
            'unidad_medida',
            'unidad_compra',
            'unidad_reparto',
            'unidad_bonificacion',
            'factor_reparto',
            'factor_compra',
            'factor_bonificacion',
            'tipo_afectacion',
            'peso',
            'tipo_producto',
            'afecto_retencion',
            'afecto_detraccion',
            'precio',
            'estado',
        ]
        widgets = {
            'empresa': forms.Select(attrs={'class': 'form-select'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_barras': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_ean': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'grupo_proveedor': forms.Select(attrs={'class': 'form-select'}),
            'linea_articulo': forms.Select(attrs={'class': 'form-select'}),
            'unidad_medida': forms.TextInput(attrs={'class': 'form-control'}),
            'unidad_compra': forms.TextInput(attrs={'class': 'form-control'}),
            'unidad_reparto': forms.TextInput(attrs={'class': 'form-control'}),
            'unidad_bonificacion': forms.TextInput(attrs={'class': 'form-control'}),
            'factor_reparto': forms.NumberInput(attrs={'class': 'form-control'}),
            'factor_compra': forms.NumberInput(attrs={'class': 'form-control'}),
            'factor_bonificacion': forms.NumberInput(attrs={'class': 'form-control'}),
            'tipo_afectacion': forms.TextInput(attrs={'class': 'form-control'}),
            'peso': forms.NumberInput(attrs={'class': 'form-control'}),
            'tipo_producto': forms.TextInput(attrs={'class': 'form-control'}),
            'afecto_retencion': forms.CheckboxInput(),
            'afecto_detraccion': forms.CheckboxInput(),
            'precio': forms.NumberInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }


class PromocionForm(forms.ModelForm):
    class Meta:
        model = Promocion
        fields = [
            'nombre', 'empresa', 'sucursal', 'canal_cliente',
            'fecha_inicio', 'fecha_fin', 'tipo_condicion',
            'monto_minimo', 'cantidad_minima',
            'tipo_beneficio', 'estado'
        ]
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super(PromocionForm, self).__init__(*args, **kwargs)
        self.fields['sucursal'].queryset = Sucursal.objects.none()
        self.fields['sucursal'].widget.attrs['disabled'] = 'disabled'
