from django import forms
from .models import GrupoProveedor, LineaArticulo, Sucursal, Usuario, Rol
from .models import Articulo, Promocion, CanalCliente, Empresa

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
    """
    Formulario actualizado para la nueva estructura de promociones
    """
    
    # Campos adicionales que no están directamente en el modelo
    linea_articulo = forms.ModelChoiceField(
        queryset=LineaArticulo.objects.all(), 
        required=False,
        empty_label="Seleccione una línea",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_linea_articulo'
        })
    )
    
    grupo_proveedor = forms.ModelChoiceField(
        queryset=GrupoProveedor.objects.all(),
        required=False,
        empty_label="Seleccione una marca/proveedor",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_grupo_proveedor'
        })
    )
    
    # Campos adicionales para el formulario que no están en el modelo base
    tipo_condicion = forms.ChoiceField(
        choices=[
            ('', 'Seleccione el tipo de condición'),
            ('cantidad', 'Por Cantidad de Productos'),
            ('monto', 'Por Monto de Compra'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_tipo_condicion'
        })
    )
    
    tipo_beneficio = forms.ChoiceField(
        choices=[
            ('', 'Seleccione el tipo de beneficio'),
            ('1', 'Solo Bonificación'),
            ('2', 'Solo Descuento'),
            ('3', 'Ambos'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_tipo_beneficio'
        })
    )

    class Meta:
        model = Promocion
        fields = [
            'descripcion',  # ← Cambiado de 'nombre' a 'descripcion'
            'empresa', 
            'sucursal', 
            'canal_cliente',
            'fecha_inicio', 
            'fecha_fin', 
            'monto_minimo',
            'escalable',
            'estado'
        ]
        
        widgets = {
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_nombre',  # Mantengo el ID para que funcione con el JS
                'placeholder': 'Ej: 3x2 en Vinos Borgoña'
            }),
            'empresa': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_empresa'
            }),
            'sucursal': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_sucursal'
            }),
            'canal_cliente': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_canal_cliente'
            }),
            'fecha_inicio': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'id_fecha_inicio'
            }),
            'fecha_fin': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'id_fecha_fin'
            }),
            'monto_minimo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'escalable': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'promocion_escalable'
            }),
            'estado': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        
        labels = {
            'descripcion': 'Descripción de la Promoción',
            'empresa': 'Empresa',
            'sucursal': 'Sucursal',
            'canal_cliente': 'Canal de Cliente',
            'fecha_inicio': 'Fecha de Inicio',
            'fecha_fin': 'Fecha de Fin',
            'monto_minimo': 'Monto Mínimo',
            'escalable': 'Promoción Escalable',
            'estado': 'Estado',
        }
    
    def __init__(self, *args, **kwargs):
        super(PromocionForm, self).__init__(*args, **kwargs)
        
        # Hacer que algunos campos no sean requeridos para el formulario
        self.fields['sucursal'].required = False
        self.fields['monto_minimo'].required = False
        self.fields['escalable'].required = False
        
        # Configurar querysets vacíos inicialmente para campos dependientes
        self.fields['sucursal'].queryset = Sucursal.objects.none()
        self.fields['linea_articulo'].queryset = LineaArticulo.objects.none()
        self.fields['grupo_proveedor'].queryset = GrupoProveedor.objects.none()
        
        # Si hay una instancia, configurar los querysets apropiados
        if self.instance and self.instance.pk:
            if self.instance.empresa:
                self.fields['sucursal'].queryset = Sucursal.objects.filter(
                    empresa=self.instance.empresa
                )
                self.fields['grupo_proveedor'].queryset = GrupoProveedor.objects.filter(
                    empresa=self.instance.empresa
                )
                
            if self.instance.grupo_proveedor_id:
                self.fields['linea_articulo'].queryset = LineaArticulo.objects.filter(
                    grupo_proveedor_id=self.instance.grupo_proveedor_id
                )
                
    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        # Validar que fecha_fin sea mayor que fecha_inicio
        if fecha_inicio and fecha_fin and fecha_fin <= fecha_inicio:
            raise forms.ValidationError(
                'La fecha de fin debe ser posterior a la fecha de inicio.'
            )
        
        return cleaned_data