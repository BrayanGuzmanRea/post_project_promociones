// static/js/jvPromos.js - REEMPLAZAR TODO EL CONTENIDO
document.addEventListener('DOMContentLoaded', function () {
    console.log('🚀 jvPromos.js cargado correctamente'); // Para debug
    
    // Variables globales
    let articulosDisponibles = [];
    
    // Elementos del formulario
    const empresaSelect = document.getElementById('id_empresa');
    const sucursalSelect = document.getElementById('id_sucursal');
    const marcaSelect = document.getElementById('id_grupo_proveedor');
    const lineaSelect = document.getElementById('id_linea_articulo');
    const tipoCondicionSelect = document.getElementById('id_tipo_condicion');
    const tipoBeneficioSelect = document.getElementById('id_tipo_beneficio');
    const fechaInicioInput = document.getElementById('id_fecha_inicio');
    const fechaFinInput = document.getElementById('id_fecha_fin');

    console.log('📋 Elementos encontrados:', {
        empresa: !!empresaSelect,
        sucursal: !!sucursalSelect,
        marca: !!marcaSelect,
        linea: !!lineaSelect
    }); // Para debug

    // Inicialización
    init();

    function init() {
        console.log('⚡ Inicializando formulario...');
        configurarFechas();
        deshabilitarElementosDependientes();
        configurarEventListeners();
        configurarFiltrosPorDefecto();
    }

    function configurarFechas() {
        const hoy = new Date().toISOString().split('T')[0];
        if (fechaInicioInput) fechaInicioInput.setAttribute('min', hoy);

        if (fechaInicioInput && fechaFinInput) {
            fechaInicioInput.addEventListener('change', function() {
                const fechaSeleccionada = this.value;
                fechaFinInput.value = '';
                fechaFinInput.setAttribute('min', fechaSeleccionada);
            });
        }
    }

    function deshabilitarElementosDependientes() {
        if (sucursalSelect) sucursalSelect.disabled = true;
        if (marcaSelect) marcaSelect.disabled = true;
        if (lineaSelect) lineaSelect.disabled = true;
    }

    function configurarEventListeners() {
        console.log('🔗 Configurando event listeners...');
        
        // Cambios en empresa
        if (empresaSelect) {
            empresaSelect.addEventListener('change', function() {
                console.log('🏢 Empresa seleccionada:', this.value);
                cargarSucursales(this.value);
                cargarMarcas(this.value);
                resetSelect(lineaSelect, 'Seleccione una línea');
            });
        }

        // Cambios en marca
        if (marcaSelect) {
            marcaSelect.addEventListener('change', function() {
                console.log('🏷️ Marca seleccionada:', this.value);
                cargarLineasPorMarca(this.value);
            });
        }

        // Cambios en sucursal
        if (sucursalSelect) {
            sucursalSelect.addEventListener('change', function() {
                console.log('🏪 Sucursal seleccionada:', this.value);
                cargarArticulos(this.value);
            });
        }

        // Cambios en tipo de filtro
        document.querySelectorAll('input[name="tipo_filtro"]').forEach(radio => {
            radio.addEventListener('change', manejarCambioTipoFiltro);
        });

        // Cambios en tipo de condición
        if (tipoCondicionSelect) {
            tipoCondicionSelect.addEventListener('change', manejarCambioTipoCondicion);
        }

        // Cambios en tipo de beneficio
        if (tipoBeneficioSelect) {
            tipoBeneficioSelect.addEventListener('change', manejarCambioTipoBeneficio);
        }

        // Configurar manejo de productos
        configurarProductosCondicion();
        
        // Configurar rangos
        configurarRangos();
        
        // Configurar bonificaciones
        configurarBonificaciones();
    }

    function configurarFiltrosPorDefecto() {
        // Seleccionar "productos específicos" por defecto
        const radioProductos = document.getElementById('filtro_productos');
        if (radioProductos) {
            radioProductos.checked = true;
            manejarCambioTipoFiltro();
        }
    }

    // === CARGA DE DATOS ===

    async function cargarSucursales(empresaId) {
        console.log('📡 Cargando sucursales para empresa:', empresaId);
        
        if (!empresaId) {
            resetSelect(sucursalSelect, 'Seleccione una sucursal');
            return;
        }

        try {
            const response = await fetch(`/core/api/sucursales/?empresa_id=${empresaId}`);
            const sucursales = await response.json();
            
            console.log('✅ Sucursales cargadas:', sucursales.length);
            
            sucursalSelect.innerHTML = '<option value="">Todas las sucursales</option>';
            sucursales.forEach(sucursal => {
                const option = document.createElement('option');
                option.value = sucursal.sucursal_id;
                option.textContent = sucursal.nombre;
                sucursalSelect.appendChild(option);
            });
            sucursalSelect.disabled = false;
        } catch (error) {
            console.error('❌ Error cargando sucursales:', error);
        }
    }

    async function cargarMarcas(empresaId) {
        console.log('📡 Cargando marcas para empresa:', empresaId);
        
        if (!empresaId) {
            resetSelect(marcaSelect, 'Seleccione una marca');
            return;
        }

        try {
            const response = await fetch(`/core/api/marcas_por_empresa/?empresa_id=${empresaId}`);
            const marcas = await response.json();
            
            console.log('✅ Marcas cargadas:', marcas.length);
            
            marcaSelect.innerHTML = '<option value="">Seleccione una marca</option>';
            marcas.forEach(marca => {
                const option = document.createElement('option');
                option.value = marca.grupo_proveedor_id;
                option.textContent = marca.nombre;
                marcaSelect.appendChild(option);
            });
            marcaSelect.disabled = false;
        } catch (error) {
            console.error('❌ Error cargando marcas:', error);
        }
    }

    async function cargarLineasPorMarca(marcaId) {
        console.log('📡 Cargando líneas para marca:', marcaId);
        
        if (!marcaId) {
            resetSelect(lineaSelect, 'Seleccione una línea');
            return;
        }

        try {
            const response = await fetch(`/core/api/lineas_por_marca/?marca_id=${marcaId}`);
            const lineas = await response.json();
            
            console.log('✅ Líneas cargadas:', lineas.length);
            
            lineaSelect.innerHTML = '<option value="">Seleccione una línea</option>';
            lineas.forEach(linea => {
                const option = document.createElement('option');
                option.value = linea.linea_articulo_id;
                option.textContent = linea.nombre;
                lineaSelect.appendChild(option);
            });
            lineaSelect.disabled = false;
        } catch (error) {
            console.error('❌ Error cargando líneas:', error);
        }
    }

    async function cargarArticulos(sucursalId) {
        console.log('📡 Cargando artículos para sucursal:', sucursalId);
        
        if (!sucursalId) {
            articulosDisponibles = [];
            actualizarSelectsProductos();
            return;
        }

        try {
            const response = await fetch(`/core/api/articulos_por_sucursal/?sucursal_id=${sucursalId}`);
            articulosDisponibles = await response.json();
            
            console.log('✅ Artículos cargados:', articulosDisponibles.length);
            
            actualizarSelectsProductos();
            actualizarSelectsBonificacion();
        } catch (error) {
            console.error('❌ Error cargando artículos:', error);
            articulosDisponibles = [];
        }
    }

    // === MANEJO DE FILTROS ===

    function manejarCambioTipoFiltro() {
        console.log('🔄 Cambiando tipo de filtro...');
        
        const tipoSeleccionado = document.querySelector('input[name="tipo_filtro"]:checked')?.value;
        
        // Ocultar todas las configuraciones
        document.querySelectorAll('.configuracion-filtro').forEach(config => {
            config.classList.add('d-none');
        });

        if (tipoSeleccionado === 'linea_marca') {
            const configLinea = document.getElementById('config-linea-marca');
            if (configLinea) configLinea.classList.remove('d-none');
        } else if (tipoSeleccionado === 'productos_especificos') {
            const configProductos = document.getElementById('config-productos-especificos');
            if (configProductos) configProductos.classList.remove('d-none');
        }
    }

    // === MANEJO DE CONDICIONES ===

    function manejarCambioTipoCondicion() {
        console.log('🔄 Cambiando tipo de condición...');
        
        const tipoCondicion = tipoCondicionSelect.value;
        
        // Ocultar todas las condiciones
        document.querySelectorAll('.condiciones-container').forEach(container => {
            container.classList.add('d-none');
        });

        if (tipoCondicion === 'cantidad') {
            const condicionesCantidad = document.getElementById('condiciones-cantidad');
            if (condicionesCantidad) {
                condicionesCantidad.classList.remove('d-none');
                verificarConfiguracionCantidad();
            }
        } else if (tipoCondicion === 'monto') {
            const condicionesMonto = document.getElementById('condiciones-monto');
            if (condicionesMonto) condicionesMonto.classList.remove('d-none');
        }
    }

    function verificarConfiguracionCantidad() {
        const productosCondicion = document.querySelectorAll('.productos-condicion-select');
        const productosSeleccionados = Array.from(productosCondicion)
            .map(select => select.value)
            .filter(val => val !== '');

        const configSimple = document.getElementById('config-cantidad-simple');
        const configMultiple = document.getElementById('config-cantidad-multiple');

        if (productosSeleccionados.length === 1) {
            if (configSimple) configSimple.classList.remove('d-none');
            if (configMultiple) configMultiple.classList.add('d-none');
            actualizarSelectProductoCantidad();
        } else if (productosSeleccionados.length > 1) {
            if (configSimple) configSimple.classList.add('d-none');
            if (configMultiple) configMultiple.classList.remove('d-none');
        } else {
            if (configSimple) configSimple.classList.add('d-none');
            if (configMultiple) configMultiple.classList.add('d-none');
        }
    }

    function actualizarSelectProductoCantidad() {
        const selectProductoCantidad = document.getElementById('select-producto-cantidad');
        if (!selectProductoCantidad) return;

        selectProductoCantidad.innerHTML = '<option value="">Seleccione el producto</option>';

        const productosCondicion = document.querySelectorAll('.productos-condicion-select');
        productosCondicion.forEach(select => {
            const valor = select.value;
            const texto = select.options[select.selectedIndex]?.textContent;
            if (valor) {
                const option = document.createElement('option');
                option.value = valor;
                option.textContent = texto;
                selectProductoCantidad.appendChild(option);
            }
        });

        // Event listener para mostrar configuración
        selectProductoCantidad.addEventListener('change', function() {
            const rangosConfig = document.getElementById('rangos-cantidad-config');
            if (this.value && rangosConfig) {
                rangosConfig.classList.remove('d-none');
            } else if (rangosConfig) {
                rangosConfig.classList.add('d-none');
            }
        });
    }

    // === MANEJO DE BENEFICIOS ===

    function manejarCambioTipoBeneficio() {
        console.log('🔄 Cambiando tipo de beneficio...');
        
        const tipoBeneficio = tipoBeneficioSelect.options[tipoBeneficioSelect.selectedIndex]?.textContent.toLowerCase();
        
        // Ocultar todos los beneficios
        document.querySelectorAll('.beneficios-container').forEach(container => {
            container.classList.add('d-none');
        });

        if (tipoBeneficio.includes('bonificación') && !tipoBeneficio.includes('ambos')) {
            const beneficioBonif = document.getElementById('beneficios-bonificacion');
            if (beneficioBonif) {
                beneficioBonif.classList.remove('d-none');
                actualizarSelectsBonificacion();
            }
        } else if (tipoBeneficio.includes('descuento') && !tipoBeneficio.includes('ambos')) {
            const beneficioDesc = document.getElementById('beneficios-descuento');
            if (beneficioDesc) beneficioDesc.classList.remove('d-none');
        } else if (tipoBeneficio.includes('ambos')) {
            const beneficioAmbos = document.getElementById('beneficios-ambos');
            if (beneficioAmbos) {
                beneficioAmbos.classList.remove('d-none');
                actualizarSelectsBonificacion();
            }
        }
    }

    // === PRODUCTOS CONDICIÓN ===

    function configurarProductosCondicion() {
        const container = document.getElementById('productos-condicion-container');
        if (!container) return;

        container.addEventListener('click', function(e) {
            if (e.target.classList.contains('btn-agregar-producto')) {
                agregarProductoCondicion();
            } else if (e.target.classList.contains('btn-eliminar-producto')) {
                eliminarProductoCondicion(e.target);
            }
        });

        container.addEventListener('change', function(e) {
            if (e.target.classList.contains('productos-condicion-select')) {
                actualizarSelectsProductos();
                if (tipoCondicionSelect && tipoCondicionSelect.value === 'cantidad') {
                    verificarConfiguracionCantidad();
                }
            }
        });
    }

    function agregarProductoCondicion() {
        const container = document.getElementById('productos-condicion-container');
        const template = container.querySelector('.producto-condicion');
        const nuevo = template.cloneNode(true);
        
        nuevo.querySelector('.productos-condicion-select').value = '';
        container.appendChild(nuevo);
        actualizarSelectsProductos();
    }

    function eliminarProductoCondicion(boton) {
        const container = document.getElementById('productos-condicion-container');
        const filas = container.querySelectorAll('.producto-condicion');
        
        if (filas.length > 1) {
            boton.closest('.producto-condicion').remove();
            actualizarSelectsProductos();
            if (tipoCondicionSelect && tipoCondicionSelect.value === 'cantidad') {
                verificarConfiguracionCantidad();
            }
        }
    }

    function actualizarSelectsProductos() {
        const selects = document.querySelectorAll('.productos-condicion-select');
        const seleccionados = Array.from(selects).map(s => s.value).filter(val => val !== '');

        selects.forEach(select => {
            const valorActual = select.value;
            select.innerHTML = '<option value="">Seleccione un producto</option>';
            
            articulosDisponibles.forEach(articulo => {
                if (!seleccionados.includes(articulo.articulo_id) || articulo.articulo_id === valorActual) {
                    const option = document.createElement('option');
                    option.value = articulo.articulo_id;
                    option.textContent = `${articulo.codigo} - ${articulo.descripcion}`;
                    if (articulo.articulo_id === valorActual) {
                        option.selected = true;
                    }
                    select.appendChild(option);
                }
            });
        });

        actualizarBotonesProductos();
    }

    function actualizarBotonesProductos() {
        const container = document.getElementById('productos-condicion-container');
        if (!container) return;
        
        const filas = container.querySelectorAll('.producto-condicion');
        const usados = Array.from(container.querySelectorAll('.productos-condicion-select'))
            .map(s => s.value).filter(val => val !== '').length;

        // Botones de agregar
        const botonesAgregar = container.querySelectorAll('.btn-agregar-producto');
        const desactivarAgregar = usados >= articulosDisponibles.length;
        botonesAgregar.forEach(btn => {
            btn.disabled = desactivarAgregar;
        });

        // Botones de eliminar
        filas.forEach(fila => {
            const btnEliminar = fila.querySelector('.btn-eliminar-producto');
            if (btnEliminar) {
                btnEliminar.disabled = filas.length === 1;
            }
        });
    }

    // === RANGOS ===

    function configurarRangos() {
        // Tipo de beneficio en cantidad
        const tipoBeneficioSelect = document.querySelector('.tipo-beneficio-cantidad');
        if (tipoBeneficioSelect) {
            tipoBeneficioSelect.addEventListener('change', function() {
                actualizarEtiquetasBeneficio(this.value);
            });
        }

        // Rangos de cantidad
        const tablaCantidad = document.getElementById('tabla-rangos-cantidad');
        if (tablaCantidad) {
            tablaCantidad.addEventListener('click', function(e) {
                if (e.target.classList.contains('btn-agregar-rango-cantidad')) {
                    agregarRangoCantidad();
                } else if (e.target.classList.contains('btn-eliminar-rango-cantidad')) {
                    eliminarRangoCantidad(e.target);
                }
            });
        }

        // Rangos de monto
        const tablaMonto = document.getElementById('tabla-rangos-monto');
        if (tablaMonto) {
            tablaMonto.addEventListener('click', function(e) {
                if (e.target.classList.contains('btn-agregar-rango-monto')) {
                    agregarRangoMonto();
                } else if (e.target.classList.contains('btn-eliminar-rango-monto')) {
                    eliminarRangoMonto(e.target);
                }
            });
        }
    }

    function agregarRangoCantidad() {
        const tabla = document.getElementById('tabla-rangos-cantidad');
        if (!tabla) return;
        
        const template = tabla.querySelector('.rango-cantidad-item');
        const nuevo = template.cloneNode(true);
        
        nuevo.querySelectorAll('input').forEach(input => input.value = '');
        tabla.appendChild(nuevo);
        actualizarBotonesRangoCantidad();
    }

    function eliminarRangoCantidad(boton) {
        const tabla = document.getElementById('tabla-rangos-cantidad');
        if (!tabla) return;
        
        const filas = tabla.querySelectorAll('.rango-cantidad-item');
        
        if (filas.length > 1) {
            boton.closest('.rango-cantidad-item').remove();
            actualizarBotonesRangoCantidad();
        }
    }

    function actualizarBotonesRangoCantidad() {
        const tabla = document.getElementById('tabla-rangos-cantidad');
        if (!tabla) return;
        
        const filas = tabla.querySelectorAll('.rango-cantidad-item');
        
        filas.forEach(fila => {
            const btnEliminar = fila.querySelector('.btn-eliminar-rango-cantidad');
            if (btnEliminar) {
                btnEliminar.disabled = filas.length === 1;
            }
        });
    }

    function agregarRangoMonto() {
        const tabla = document.getElementById('tabla-rangos-monto');
        if (!tabla) return;
        
        const template = tabla.querySelector('.rango-monto-item');
        const nuevo = template.cloneNode(true);
        
        nuevo.querySelectorAll('input').forEach(input => input.value = '');
        tabla.appendChild(nuevo);
        actualizarBotonesRangoMonto();
    }

    function eliminarRangoMonto(boton) {
        const tabla = document.getElementById('tabla-rangos-monto');
        if (!tabla) return;
        
        const filas = tabla.querySelectorAll('.rango-monto-item');
        
        if (filas.length > 1) {
            boton.closest('.rango-monto-item').remove();
            actualizarBotonesRangoMonto();
        }
    }

    function actualizarBotonesRangoMonto() {
        const tabla = document.getElementById('tabla-rangos-monto');
        if (!tabla) return;
        
        const filas = tabla.querySelectorAll('.rango-monto-item');
        
        filas.forEach(fila => {
            const btnEliminar = fila.querySelector('.btn-eliminar-rango-monto');
            if (btnEliminar) {
                btnEliminar.disabled = filas.length === 1;
            }
        });
    }

    function actualizarEtiquetasBeneficio(tipo) {
        const headers = document.querySelectorAll('.beneficio-header');
        const hints = document.querySelectorAll('.beneficio-hint');
        
        if (tipo === 'producto_gratis') {
            headers.forEach(header => header.textContent = 'Cantidad Gratis');
            hints.forEach(hint => hint.textContent = 'Cantidad de productos gratis');
        } else if (tipo === 'porcentaje_descuento') {
            headers.forEach(header => header.textContent = 'Porcentaje (%)');
            hints.forEach(hint => hint.textContent = 'Porcentaje de descuento');
        }
    }

    // === BONIFICACIONES ===

    function configurarBonificaciones() {
        // Bonificaciones simples
        const tablaBonif = document.getElementById('tabla-bonificaciones');
        if (tablaBonif) {
            tablaBonif.addEventListener('click', function(e) {
                if (e.target.classList.contains('btn-agregar-bonificacion')) {
                    agregarBonificacion();
                } else if (e.target.classList.contains('btn-eliminar-bonificacion')) {
                    eliminarBonificacion(e.target);
                }
            });
        }

        // Bonificaciones ambos
        const tablaBonifAmbos = document.getElementById('tabla-bonificaciones-ambos');
        if (tablaBonifAmbos) {
            tablaBonifAmbos.addEventListener('click', function(e) {
                if (e.target.classList.contains('btn-agregar-bonificacion-ambos')) {
                    agregarBonificacionAmbos();
                } else if (e.target.classList.contains('btn-eliminar-bonificacion-ambos')) {
                    eliminarBonificacionAmbos(e.target);
                }
            });
        }
    }

    function agregarBonificacion() {
        const tabla = document.getElementById('tabla-bonificaciones');
        if (!tabla) return;
        
        const template = tabla.querySelector('.bonificacion-item');
        const nuevo = template.cloneNode(true);
        
        nuevo.querySelector('.select-bonificacion').value = '';
        nuevo.querySelector('input[name="cantidad_bonificada[]"]').value = '';
        
        tabla.appendChild(nuevo);
        actualizarSelectsBonificacion();
    }

    function eliminarBonificacion(boton) {
        const tabla = document.getElementById('tabla-bonificaciones');
        if (!tabla) return;
        
        const filas = tabla.querySelectorAll('.bonificacion-item');
        
        if (filas.length > 1) {
            boton.closest('.bonificacion-item').remove();
        }
    }

    function agregarBonificacionAmbos() {
        const tabla = document.getElementById('tabla-bonificaciones-ambos');
        if (!tabla) return;
        
        const template = tabla.querySelector('.bonificacion-ambos-item');
        const nuevo = template.cloneNode(true);
        
        nuevo.querySelector('.select-bonificacion-ambos').value = '';
        nuevo.querySelector('input[name="cantidad_bonificada_ambos[]"]').value = '';
        
        tabla.appendChild(nuevo);
        actualizarSelectsBonificacion();
    }

    function eliminarBonificacionAmbos(boton) {
        const tabla = document.getElementById('tabla-bonificaciones-ambos');
        if (!tabla) return;
        
        const filas = tabla.querySelectorAll('.bonificacion-ambos-item');
        
        if (filas.length > 1) {
            boton.closest('.bonificacion-ambos-item').remove();
        }
    }

    function actualizarSelectsBonificacion() {
        const selects = document.querySelectorAll('.select-bonificacion, .select-bonificacion-ambos');
        
        selects.forEach(select => {
            const valorActual = select.value;
            select.innerHTML = '<option value="">Seleccione un producto</option>';
            
            articulosDisponibles.forEach(articulo => {
                const option = document.createElement('option');
                option.value = articulo.articulo_id;
                option.textContent = `${articulo.codigo} - ${articulo.descripcion}`;
                if (articulo.articulo_id === valorActual) {
                    option.selected = true;
                }
                select.appendChild(option);
            });
        });
    }

    // === VALIDACIONES ===

    const formulario = document.getElementById('form-promocion');
    if (formulario) {
        formulario.addEventListener('submit', function(e) {
            console.log('📝 Enviando formulario...');
            if (!validarFormulario()) {
                
                return false;
            }
        });
    }

    function validarFormulario() {
        // Validaciones básicas
        const nombre = document.getElementById('id_nombre')?.value.trim();
        const empresa = empresaSelect?.value;
        const fechaInicio = fechaInicioInput?.value;
        const fechaFin = fechaFinInput?.value;
        const canalCliente = document.getElementById('id_canal_cliente')?.value;

        if (!nombre) {
            alert('Por favor ingrese la descripción de la promoción');
            document.getElementById('id_nombre')?.focus();
            return false;
        }
        if (!empresa) {
            alert('Por favor seleccione una empresa');
            empresaSelect?.focus();
            return false;
        }
        if (!fechaInicio) {
            alert('Por favor seleccione la fecha de inicio');
            fechaInicioInput?.focus();
            return false;
        }
        if (!fechaFin) {
            alert('Por favor seleccione la fecha de fin');
            fechaFinInput?.focus();
            return false;
        }
        if (!canalCliente) {
            alert('Por favor seleccione el canal de cliente');
            document.getElementById('id_canal_cliente')?.focus();
            return false;
        }

        // Validar filtros
        const tipoFiltro = document.querySelector('input[name="tipo_filtro"]:checked')?.value;
        if (tipoFiltro === 'productos_especificos') {
            const productosSeleccionados = Array.from(document.querySelectorAll('.productos-condicion-select'))
                .map(s => s.value).filter(val => val !== '');
            
            if (productosSeleccionados.length === 0) {
                alert('Por favor seleccione al menos un producto');
                return false;
            }
        }

        // Validar condiciones
        const tipoCondicion = tipoCondicionSelect?.value;
        if (!tipoCondicion) {
            alert('Por favor seleccione el tipo de condición');
            tipoCondicionSelect?.focus();
            return false;
        }

        // Validar beneficios
        const tipoBeneficio = tipoBeneficioSelect?.value;
        if (!tipoBeneficio) {
            alert('Por favor seleccione el tipo de beneficio');
            tipoBeneficioSelect?.focus();
            return false;
        }

        console.log('✅ Formulario validado correctamente');
        return true;
    }

    // === UTILIDADES ===

    function resetSelect(select, placeholder) {
        if (select) {
            select.innerHTML = `<option value="">${placeholder}</option>`;
            select.disabled = true;
        }
    }

    console.log('✅ jvPromos.js inicializado completamente');
});

// AGREGAR AL FINAL DE jvPromos.js TEMPORALMENTE
document.addEventListener('DOMContentLoaded', function() {
    const botonCrear = document.querySelector('button[type="submit"]');
    if (botonCrear) {
        botonCrear.addEventListener('click', function(e) {
            console.log('🔥 BOTÓN CLICKEADO!');
            console.log('📝 Formulario:', document.getElementById('form-promocion'));
        });
    } else {
        console.log('❌ NO SE ENCONTRÓ EL BOTÓN DE SUBMIT');
    }
});