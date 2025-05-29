// static/js/jvPromos.js - VERSIÓN COMPLETA CON RANGOS ILIMITADOS Y CONDICIONES DE GUARDADO
document.addEventListener('DOMContentLoaded', function () {
    console.log('🚀 jvPromos.js cargado correctamente - VERSIÓN RANGOS ILIMITADOS');
    
    // Variables globales
    let articulosDisponibles = [];
    let contadorRangosCantidad = 1;
    let contadorRangosMonto = 1;
    
    // Elementos del formulario
    const empresaSelect = document.getElementById('id_empresa');
    const sucursalSelect = document.getElementById('id_sucursal');
    const marcaSelect = document.getElementById('id_grupo_proveedor');
    const lineaSelect = document.getElementById('id_linea_articulo');
    const tipoCondicionSelect = document.getElementById('id_tipo_condicion');
    const tipoBeneficioSelect = document.getElementById('id_tipo_beneficio');
    const fechaInicioInput = document.getElementById('id_fecha_inicio');
    const fechaFinInput = document.getElementById('id_fecha_fin');
    const montoMinimoProductos = document.getElementById('monto_minimo_productos');
    const promocionEscalable = document.getElementById('promocion_escalable');

    // Secciones
    const seccionCondiciones = document.getElementById('seccion-condiciones');
    const seccionBeneficios = document.getElementById('seccion-beneficios');

    // Inicialización
    init();

    function init() {
        console.log('⚡ Inicializando formulario...');
        configurarFechas();
        deshabilitarElementosDependientes();
        configurarEventListeners();
        configurarFiltrosPorDefecto();
        evaluarEstadoFormulario();
    }

    function configurarFechas() {
        const hoy = new Date().toISOString().split('T')[0];
        if (fechaInicioInput) fechaInicioInput.setAttribute('min', hoy);

        if (fechaInicioInput && fechaFinInput) {
            fechaInicioInput.addEventListener('change', function() {
                const fechaSeleccionada = this.value;
                fechaFinInput.value = '';
                fechaFinInput.setAttribute('min', fechaSeleccionada);
                evaluarEstadoFormulario();
            });
        }
    }

    function deshabilitarElementosDependientes() {
        if (sucursalSelect) sucursalSelect.disabled = true;
        if (marcaSelect) marcaSelect.disabled = true;
        if (lineaSelect) lineaSelect.disabled = true;
        if (montoMinimoProductos) montoMinimoProductos.disabled = true;
        if (tipoCondicionSelect) tipoCondicionSelect.disabled = true;
        if (tipoBeneficioSelect) tipoBeneficioSelect.disabled = true;
        if (promocionEscalable) promocionEscalable.disabled = true;
        
        agregarClaseDeshabilitada(seccionCondiciones);
        agregarClaseDeshabilitada(seccionBeneficios);
    }

    function configurarEventListeners() {
        console.log('🔗 Configurando event listeners...');
        
        // === INFORMACIÓN BÁSICA ===
        [empresaSelect, sucursalSelect, document.getElementById('id_canal_cliente'), 
         fechaInicioInput, fechaFinInput].forEach(elemento => {
            if (elemento) {
                elemento.addEventListener('change', evaluarEstadoFormulario);
            }
        });

        // Cambios en empresa
        if (empresaSelect) {
            empresaSelect.addEventListener('change', function() {
                console.log('🏢 Empresa seleccionada:', this.value);
                cargarSucursales(this.value);
                cargarMarcas(this.value);
                resetSelect(lineaSelect, 'Seleccione una línea');
                if (montoMinimoProductos) montoMinimoProductos.disabled = true;
                evaluarEstadoFormulario();
            });
        }

        // Cambios en sucursal
        if (sucursalSelect) {
            sucursalSelect.addEventListener('change', function() {
                console.log('🏪 Sucursal seleccionada:', this.value);
                cargarArticulos(this.value);
                evaluarEstadoFormulario();
            });
        }

        // Cambios en marca
        if (marcaSelect) {
            marcaSelect.addEventListener('change', function() {
                console.log('🏷️ Marca seleccionada:', this.value);
                cargarLineasPorMarca(this.value);
                if (montoMinimoProductos) montoMinimoProductos.disabled = true;
                evaluarEstadoFormulario();
            });
        }

        // Cambios en línea
        if (lineaSelect) {
            lineaSelect.addEventListener('change', function() {
                console.log('📋 Línea seleccionada:', this.value);
                const tipoFiltro = document.querySelector('input[name="tipo_filtro"]:checked')?.value;
                if (tipoFiltro === 'linea_marca' && this.value) {
                    if (montoMinimoProductos) {
                        montoMinimoProductos.disabled = false;
                        montoMinimoProductos.required = true;
                    }
                }
                evaluarEstadoFormulario();
            });
        }

        // Monto mínimo productos
        if (montoMinimoProductos) {
            montoMinimoProductos.addEventListener('input', evaluarEstadoFormulario);
        }

        // === CONFIGURACIÓN DE PRODUCTOS ===
        document.querySelectorAll('input[name="tipo_filtro"]').forEach(radio => {
            radio.addEventListener('change', manejarCambioTipoFiltro);
        });

        // === CONDICIONES DE ACTIVACIÓN ===
        if (tipoCondicionSelect) {
            tipoCondicionSelect.addEventListener('change', manejarCambioTipoCondicion);
        }

        // === BENEFICIOS ===
        if (tipoBeneficioSelect) {
            tipoBeneficioSelect.addEventListener('change', manejarCambioTipoBeneficio);
        }

        // Configurar manejo de productos
        configurarProductosCondicion();
        configurarRangos();
        configurarBonificaciones();
    }

    function configurarFiltrosPorDefecto() {
        const radioProductos = document.getElementById('filtro_productos');
        if (radioProductos) {
            radioProductos.checked = true;
            manejarCambioTipoFiltro();
        }
    }

    // === EVALUACIÓN GENERAL DEL ESTADO ===
    function evaluarEstadoFormulario() {
        console.log('🔄 Evaluando estado del formulario...');
        
        const informacionBasicaCompleta = verificarInformacionBasica();
        const configuracionProductosCompleta = verificarConfiguracionProductos();
        
        console.log('📋 Estado actual:', {
            informacionBasica: informacionBasicaCompleta,
            configuracionProductos: configuracionProductosCompleta
        });

        controlarSeccionCondiciones(informacionBasicaCompleta, configuracionProductosCompleta);
        controlarSeccionBeneficios(informacionBasicaCompleta, configuracionProductosCompleta);
        controlarPromocionEscalable();
    }

    function verificarInformacionBasica() {
        const nombre = document.getElementById('id_nombre')?.value.trim();
        const empresa = empresaSelect?.value;
        const sucursal = sucursalSelect?.value;
        const canalCliente = document.getElementById('id_canal_cliente')?.value;
        const fechaInicio = fechaInicioInput?.value;
        const fechaFin = fechaFinInput?.value;

        return !!(nombre && empresa && sucursal && canalCliente && fechaInicio && fechaFin);
    }

    function verificarConfiguracionProductos() {
        const tipoFiltro = document.querySelector('input[name="tipo_filtro"]:checked')?.value;
        
        if (tipoFiltro === 'productos_especificos') {
            const productosSeleccionados = Array.from(document.querySelectorAll('.productos-condicion-select'))
                .map(s => s.value).filter(val => val !== '');
            return productosSeleccionados.length >= 1;
        } else if (tipoFiltro === 'linea_marca') {
            const marca = marcaSelect?.value;
            const linea = lineaSelect?.value;
            const monto = montoMinimoProductos?.value;
            return !!(marca && linea && monto);
        }
        
        return false;
    }

    function controlarSeccionCondiciones(informacionBasicaCompleta, configuracionProductosCompleta) {
        const tipoFiltro = document.querySelector('input[name="tipo_filtro"]:checked')?.value;
        const productosSeleccionados = Array.from(document.querySelectorAll('.productos-condicion-select'))
            .map(s => s.value).filter(val => val !== '');

        const habilitarCondiciones = informacionBasicaCompleta && 
                                tipoFiltro === 'productos_especificos' && 
                                productosSeleccionados.length === 1;

        if (seccionCondiciones) {
            if (habilitarCondiciones) {
                quitarClaseDeshabilitada(seccionCondiciones);
            } else {
                agregarClaseDeshabilitada(seccionCondiciones);
            }
        }

        if (tipoCondicionSelect) {
            tipoCondicionSelect.disabled = !habilitarCondiciones;
            if (!habilitarCondiciones) {
                tipoCondicionSelect.value = '';
                ocultarTodasLasCondiciones();
            }
        }

        console.log(`🎯 Condiciones: ${habilitarCondiciones ? 'HABILITADAS' : 'DESHABILITADAS'}`);
    }

    function controlarSeccionBeneficios(informacionBasicaCompleta, configuracionProductosCompleta) {
        const tipoFiltro = document.querySelector('input[name="tipo_filtro"]:checked')?.value;
        const productosSeleccionados = Array.from(document.querySelectorAll('.productos-condicion-select'))
            .map(s => s.value).filter(val => val !== '');
        
        let habilitarBeneficios = false;

        if (tipoFiltro === 'linea_marca') {
            habilitarBeneficios = informacionBasicaCompleta && configuracionProductosCompleta;
        } else if (tipoFiltro === 'productos_especificos') {
            if (productosSeleccionados.length > 1) {
                habilitarBeneficios = informacionBasicaCompleta && configuracionProductosCompleta;
            }
        }

        if (seccionBeneficios) {
            if (habilitarBeneficios) {
                quitarClaseDeshabilitada(seccionBeneficios);
            } else {
                agregarClaseDeshabilitada(seccionBeneficios);
            }
        }

        if (tipoBeneficioSelect) {
            tipoBeneficioSelect.disabled = !habilitarBeneficios;
            if (!habilitarBeneficios) {
                tipoBeneficioSelect.value = '';
                ocultarTodosLosBeneficios();
            }
        }

        console.log(`🎁 Beneficios: ${habilitarBeneficios ? 'HABILITADOS' : 'DESHABILITADOS'}`);
    }

    function controlarPromocionEscalable() {
        if (!promocionEscalable) return;

        const tipoFiltro = document.querySelector('input[name="tipo_filtro"]:checked')?.value;
        const productosSeleccionados = Array.from(document.querySelectorAll('.productos-condicion-select'))
            .map(s => s.value).filter(val => val !== '');
        const tipoCondicion = tipoCondicionSelect?.value;
        const tipoBeneficioValue = tipoBeneficioSelect?.value;
        
        let habilitarEscalable = false;
        let razonDeshabilitacion = '';

        if (tipoFiltro === 'productos_especificos' && 
            productosSeleccionados.length === 1 && 
            tipoCondicion === 'cantidad') {
            
            const filasRangos = document.querySelectorAll('.rango-cantidad-item');
            const soloUnaFila = filasRangos.length === 1;
            
            if (soloUnaFila) {
                const tieneCantidadMinimaYProductos = verificarCantidadMinimaConProductosBonificados();
                
                if (tieneCantidadMinimaYProductos) {
                    habilitarEscalable = true;
                    razonDeshabilitacion = '✅ Condición 1 cumplida: 1 producto + 1 fila + cantidad mínima + producto bonificado';
                } else {
                    razonDeshabilitacion = '❌ Condición 1 incompleta: Falta cantidad mínima o producto bonificado en la fila';
                }
            } else {
                razonDeshabilitacion = `❌ Condición 1 incompleta: Debe haber exactamente 1 fila de rangos (actualmente: ${filasRangos.length})`;
            }
        }
        else if (tipoFiltro === 'linea_marca') {
            const configuracionCompleta = verificarConfiguracionLineaMarca();
            const esBonificacionOAmbos = tipoBeneficioValue === '1' || tipoBeneficioValue === '3';
            
            if (configuracionCompleta && esBonificacionOAmbos) {
                habilitarEscalable = true;
                const tipoBeneficioTexto = tipoBeneficioSelect?.options[tipoBeneficioSelect?.selectedIndex]?.textContent || '';
                razonDeshabilitacion = `✅ Condición 2 cumplida: Marca/Línea completa + ${tipoBeneficioTexto}`;
            } else if (!configuracionCompleta) {
                razonDeshabilitacion = '❌ Condición 2 incompleta: Falta completar campos de Marca/Línea/Monto';
            } else if (!esBonificacionOAmbos) {
                razonDeshabilitacion = '❌ Condición 2 incompleta: Tipo de beneficio debe ser "Solo Bonificación" o "ambos"';
            }
        }
        else {
            if (tipoFiltro === 'productos_especificos') {
                if (productosSeleccionados.length === 0) {
                    razonDeshabilitacion = '❌ Debe seleccionar exactamente 1 producto específico';
                } else if (productosSeleccionados.length > 1) {
                    razonDeshabilitacion = '❌ Debe seleccionar exactamente 1 producto (no múltiples)';
                } else if (tipoCondicion !== 'cantidad') {
                    razonDeshabilitacion = '❌ Debe seleccionar "Por cantidad de productos"';
                } else {
                    razonDeshabilitacion = '❌ Falta configurar cantidad mínima y productos bonificados';
                }
            } else {
                razonDeshabilitacion = '❌ Configuración no válida para promoción escalable';
            }
        }

        promocionEscalable.disabled = !habilitarEscalable;
        if (!habilitarEscalable) {
            promocionEscalable.checked = false;
        }

        console.log(`♾️ Promoción Escalable: ${habilitarEscalable ? 'HABILITADA' : 'DESHABILITADA'}`);
        console.log(`   📝 Razón: ${razonDeshabilitacion}`);
    }

    function verificarCantidadMinimaConProductosBonificados() {
        const primeraFila = document.querySelector('.rango-cantidad-item');
        if (!primeraFila) return false;
        
        const cantidadMinima = primeraFila.querySelector('.cantidad-min-input')?.value?.trim();
        if (!cantidadMinima || parseInt(cantidadMinima) <= 0) return false;
        
        const productosBonificados = primeraFila.querySelectorAll('.producto-bonificado-select');
        const hayProductoBonificado = Array.from(productosBonificados).some(select => select.value !== '');
        
        if (hayProductoBonificado) {
            const cantidadesBonificadas = primeraFila.querySelectorAll('.cantidad-bonificada-input');
            const hayCantidadBonificada = Array.from(cantidadesBonificadas).some(input => 
                input.value?.trim() && parseInt(input.value) > 0
            );
            return hayCantidadBonificada;
        }
        
        return false;
    }

    function verificarConfiguracionLineaMarca() {
        const marca = marcaSelect?.value;
        const linea = lineaSelect?.value;
        const monto = montoMinimoProductos?.value;
        
        return !!(marca && linea && monto && parseFloat(monto) > 0);
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
            
            sucursalSelect.innerHTML = '<option value="">Seleccione una sucursal</option>';
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
            actualizarSelectsProductoBonificado();
        } catch (error) {
            console.error('❌ Error cargando artículos:', error);
            articulosDisponibles = [];
        }
    }

    // === MANEJO DE FILTROS ===
    function manejarCambioTipoFiltro() {
        console.log('🔄 Cambiando tipo de filtro...');
        
        const tipoSeleccionado = document.querySelector('input[name="tipo_filtro"]:checked')?.value;
        console.log(`📊 Tipo seleccionado: ${tipoSeleccionado}`);
        
        document.querySelectorAll('.configuracion-filtro').forEach(config => {
            config.classList.add('d-none');
        });

        // Remover required de TODOS los campos que pueden estar ocultos
        document.querySelectorAll('.productos-condicion-select').forEach(select => {
            select.removeAttribute('required');
        });

        if (tipoSeleccionado === 'linea_marca') {
            const configLinea = document.getElementById('config-linea-marca');
            if (configLinea) configLinea.classList.remove('d-none');
            
            if (marcaSelect) marcaSelect.required = true;
            if (lineaSelect) lineaSelect.required = true;
            if (montoMinimoProductos) montoMinimoProductos.required = true;
            
            document.querySelectorAll('.productos-condicion-select').forEach(select => {
                select.required = false;
                select.removeAttribute('required');
            });
            
        } else if (tipoSeleccionado === 'productos_especificos') {
            const configProductos = document.getElementById('config-productos-especificos');
            if (configProductos) configProductos.classList.remove('d-none');
            
            const primerProductoSelect = document.querySelector('.productos-condicion-select');
            if (primerProductoSelect) {
                primerProductoSelect.required = true;
            }
            
            if (marcaSelect) {
                marcaSelect.required = false;
                marcaSelect.removeAttribute('required');
            }
            if (lineaSelect) {
                lineaSelect.required = false;
                lineaSelect.removeAttribute('required');
            }
            if (montoMinimoProductos) {
                montoMinimoProductos.required = false;
                montoMinimoProductos.removeAttribute('required');
            }
        }

        evaluarEstadoFormulario();
    }

    // === MANEJO DE CONDICIONES ===
    function manejarCambioTipoCondicion() {
        console.log('🔄 Cambiando tipo de condición...');
        
        const tipoCondicion = tipoCondicionSelect.value;
        
        ocultarTodasLasCondiciones();

        if (tipoCondicion === 'cantidad') {
            const condicionesCantidad = document.getElementById('condiciones-cantidad');
            if (condicionesCantidad) condicionesCantidad.classList.remove('d-none');
        } else if (tipoCondicion === 'monto') {
            const condicionesMonto = document.getElementById('condiciones-monto');
            if (condicionesMonto) condicionesMonto.classList.remove('d-none');
        }

        evaluarEstadoFormulario();
        controlarPromocionEscalable();
    }

    function ocultarTodasLasCondiciones() {
        document.querySelectorAll('.condiciones-container').forEach(container => {
            container.classList.add('d-none');
        });
    }

    // === MANEJO DE BENEFICIOS ===
    function manejarCambioTipoBeneficio() {
        console.log('🔄 Cambiando tipo de beneficio...');
        
        const tipoBeneficioValue = tipoBeneficioSelect.value;
        
        ocultarTodosLosBeneficios();

        if (tipoBeneficioValue === '1') {
            const beneficioBonif = document.getElementById('beneficios-bonificacion');
            if (beneficioBonif) {
                beneficioBonif.classList.remove('d-none');
                actualizarSelectsBonificacion();
            }
        } else if (tipoBeneficioValue === '2') {
            const beneficioDesc = document.getElementById('beneficios-descuento');
            if (beneficioDesc) {
                beneficioDesc.classList.remove('d-none');
            }
        } else if (tipoBeneficioValue === '3') {
            const beneficioAmbos = document.getElementById('beneficios-ambos');
            if (beneficioAmbos) {
                beneficioAmbos.classList.remove('d-none');
                actualizarSelectsBonificacion();
            }
        }

        controlarPromocionEscalable();
    }

    function ocultarTodosLosBeneficios() {
        document.querySelectorAll('.beneficios-container').forEach(container => {
            container.classList.add('d-none');
        });
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
                evaluarEstadoFormulario();
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
        evaluarEstadoFormulario();
    }

    function eliminarProductoCondicion(boton) {
        const container = document.getElementById('productos-condicion-container');
        const filas = container.querySelectorAll('.producto-condicion');
        
        if (filas.length > 1) {
            boton.closest('.producto-condicion').remove();
            actualizarSelectsProductos();
            evaluarEstadoFormulario();
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

        const botonesAgregar = container.querySelectorAll('.btn-agregar-producto');
        const desactivarAgregar = usados >= articulosDisponibles.length;
        botonesAgregar.forEach(btn => {
            btn.disabled = desactivarAgregar;
        });

        filas.forEach(fila => {
            const btnEliminar = fila.querySelector('.btn-eliminar-producto');
            if (btnEliminar) {
                btnEliminar.disabled = filas.length === 1;
            }
        });
    }

    // === RANGOS - VERSIÓN CORREGIDA PARA RANGOS ILIMITADOS ===
    function configurarRangos() {
        document.addEventListener('click', function(e) {
            if (e.target.disabled) return;
            
            if (e.target.classList.contains('btn-agregar-rango-cantidad')) {
                e.preventDefault();
                e.stopPropagation();
                agregarRangoCantidad();
            } else if (e.target.classList.contains('btn-eliminar-rango-cantidad')) {
                e.preventDefault();
                e.stopPropagation();
                eliminarRangoCantidad(e.target);
            } else if (e.target.classList.contains('btn-agregar-producto-bonificado')) {
                e.preventDefault();
                e.stopPropagation();
                
                const tablaPadre = e.target.closest('table');
                if (tablaPadre && tablaPadre.id === 'tabla-rangos-cantidad') {
                    agregarProductoBonificado(e.target);
                } else if (tablaPadre && tablaPadre.id === 'tabla-rangos-monto') {
                    agregarProductoBonificadoMonto(e.target);
                }
                
            } else if (e.target.classList.contains('btn-quitar-producto-bonificado')) {
                e.preventDefault();
                e.stopPropagation();
                quitarProductoBonificado(e.target);
            }
            
            else if (e.target.classList.contains('btn-agregar-rango-monto')) {
                e.preventDefault();
                e.stopPropagation();
                agregarRangoMonto();
            } else if (e.target.classList.contains('btn-eliminar-rango-monto')) {
                e.preventDefault();
                e.stopPropagation();
                eliminarRangoMonto(e.target);
            }
        });

        document.addEventListener('change', function(e) {
            if (e.target.classList.contains('producto-bonificado-select')) {
                const fila = e.target.closest('.producto-bonificado-item');
                const cantidadInput = fila.querySelector('.cantidad-bonificada-input');
                if (cantidadInput) {
                    cantidadInput.disabled = !e.target.value;
                    if (!e.target.value) {
                        cantidadInput.value = '';
                    }
                }
                controlarPromocionEscalable();
            } else if (e.target.classList.contains('cantidad-min-input') || 
                     e.target.name === 'cantidad_max[]') {
                controlarPromocionEscalable();
            }
        });

        document.addEventListener('input', function(e) {
            if (e.target.classList.contains('cantidad-min-input') || 
                e.target.name === 'cantidad_max[]' ||
                e.target.classList.contains('descuento-input') ||
                e.target.classList.contains('cantidad-bonificada-input')) {
                setTimeout(() => {
                    controlarPromocionEscalable();
                }, 100);
            }
        });
    }

    function agregarRangoCantidad() {
        const tabla = document.getElementById('tabla-rangos-cantidad-body');
        if (!tabla) return;
        
        const botonesAgregar = document.querySelectorAll('.btn-agregar-rango-cantidad');
        botonesAgregar.forEach(btn => btn.disabled = true);
        
        const filasExistentes = tabla.querySelectorAll('.rango-cantidad-item');
        const nuevoIndice = filasExistentes.length;
        
        console.log(`✅ Agregando rango de cantidad con índice: ${nuevoIndice}`);
        
        const nuevaFila = document.createElement('tr');
        nuevaFila.className = 'rango-cantidad-item';
        nuevaFila.setAttribute('data-index', nuevoIndice);
        
        nuevaFila.innerHTML = `
            <td>
                <input type="number" name="cantidad_min[]" class="form-control cantidad-min-input" 
                       min="1" placeholder="Ej: 4" data-rango-index="${nuevoIndice}">
            </td>
            <td>
                <input type="number" name="cantidad_max[]" class="form-control" min="1" placeholder="Opcional"
                       data-rango-index="${nuevoIndice}">
                <small class="text-muted">Vacío = "en adelante"</small>
            </td>
            <td>
                <input type="number" name="porcentaje_descuento_cantidad[]" class="form-control descuento-input" 
                       min="0" max="100" step="0.01" placeholder="Ej: 5" data-rango-index="${nuevoIndice}">
            </td>
            <td>
                <div class="productos-bonificados-container">
                    <div class="producto-bonificado-item mb-2">
                        <div class="row">
                            <div class="col-7">
                                <select name="producto_bonificado_cantidad_${nuevoIndice}[]" class="form-select producto-bonificado-select">
                                    <option value="">Sin producto bonificado</option>
                                </select>
                            </div>
                            <div class="col-3">
                                <input type="number" name="cantidad_bonificada_cantidad_${nuevoIndice}[]" 
                                       class="form-control cantidad-bonificada-input" 
                                       min="1" placeholder="Cant." disabled>
                            </div>
                            <div class="col-2">
                                <button type="button" class="btn btn-danger btn-sm btn-quitar-producto-bonificado" 
                                        title="Quitar producto" style="display: none;">
                                    <i class="fas fa-times"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                <button type="button" class="btn btn-success btn-sm btn-agregar-producto-bonificado" 
                        title="Agregar más productos bonificados">
                    <i class="fas fa-plus"></i> Agregar Producto
                </button>
            </td>
            <td>
                <button type="button" class="btn btn-success btn-sm btn-agregar-rango-cantidad me-1 mb-1" 
                        title="Agregar rango">
                    <i class="fas fa-plus"></i>
                </button>
                <button type="button" class="btn btn-danger btn-sm btn-eliminar-rango-cantidad" 
                        title="Eliminar rango">
                    <i class="fas fa-times"></i>
                </button>
            </td>
        `;
        
        tabla.appendChild(nuevaFila);
        actualizarSelectsProductoBonificado();
        contadorRangosCantidad = nuevoIndice + 1;
        
        setTimeout(() => {
            botonesAgregar.forEach(btn => btn.disabled = false);
            controlarPromocionEscalable();
        }, 300);
        
        console.log(`✅ Rango de cantidad agregado. Total rangos: ${contadorRangosCantidad}`);
    }

    function eliminarRangoCantidad(boton) {
        const tabla = document.getElementById('tabla-rangos-cantidad-body');
        if (!tabla) return;
        
        const filas = tabla.querySelectorAll('.rango-cantidad-item');
        
        if (filas.length > 1) {
            const filaAEliminar = boton.closest('.rango-cantidad-item');
            const indiceEliminado = parseInt(filaAEliminar.getAttribute('data-index') || '0');
            
            console.log(`🗑️ Eliminando rango de cantidad ${indiceEliminado}`);
            
            boton.disabled = true;
            filaAEliminar.remove();
            
            // REINDEXAR todas las filas restantes
            const filasRestantes = tabla.querySelectorAll('.rango-cantidad-item');
            filasRestantes.forEach((fila, nuevoIndice) => {
                console.log(`🔄 Reindexando fila de ${fila.getAttribute('data-index')} a ${nuevoIndice}`);
                
                fila.setAttribute('data-index', nuevoIndice);
                
                const inputs = fila.querySelectorAll('input[data-rango-index]');
                inputs.forEach(input => {
                    input.setAttribute('data-rango-index', nuevoIndice);
                });
                
                const selectsProductos = fila.querySelectorAll('select[name*="producto_bonificado_cantidad_"]');
                const inputsCantidades = fila.querySelectorAll('input[name*="cantidad_bonificada_cantidad_"]');
                
                selectsProductos.forEach(select => {
                    select.name = `producto_bonificado_cantidad_${nuevoIndice}[]`;
                });
                
                inputsCantidades.forEach(input => {
                    input.name = `cantidad_bonificada_cantidad_${nuevoIndice}[]`;
                });
            });
            
            contadorRangosCantidad = filasRestantes.length;
            console.log(`✅ Rango eliminado. Rangos restantes: ${contadorRangosCantidad}`);
            controlarPromocionEscalable();
        }
    }

    function agregarRangoMonto() {
        const tabla = document.getElementById('tabla-rangos-monto-body');
        if (!tabla) return;
        
        const botonesAgregar = document.querySelectorAll('.btn-agregar-rango-monto');
        botonesAgregar.forEach(btn => btn.disabled = true);
        
        const filasExistentes = tabla.querySelectorAll('.rango-monto-item');
        const nuevoIndice = filasExistentes.length;
        
        console.log(`✅ Agregando rango de monto con índice: ${nuevoIndice}`);
        
        const nuevaFila = document.createElement('tr');
        nuevaFila.className = 'rango-monto-item';
        nuevaFila.setAttribute('data-index', nuevoIndice);
        
        nuevaFila.innerHTML = `
            <td>
                <input type="number" name="monto_minimo[]" class="form-control monto-min-input" 
                       min="0" step="0.01" placeholder="Ej: 300" data-rango-index="${nuevoIndice}">
            </td>
            <td>
                <input type="number" name="monto_maximo[]" class="form-control" min="0" step="0.01" placeholder="Opcional"
                       data-rango-index="${nuevoIndice}">
                <small class="text-muted">Vacío = "en adelante"</small>
            </td>
            <td>
                <input type="number" name="porcentaje_descuento_monto[]" class="form-control descuento-input" 
                       min="0" max="100" step="0.01" placeholder="Ej: 5" data-rango-index="${nuevoIndice}">
            </td>
            <td>
                <div class="productos-bonificados-container">
                    <div class="producto-bonificado-item mb-2">
                        <div class="row">
                            <div class="col-7">
                                <select name="producto_bonificado_monto_${nuevoIndice}[]" class="form-select producto-bonificado-select">
                                    <option value="">Sin producto bonificado</option>
                                </select>
                            </div>
                            <div class="col-3">
                                <input type="number" name="cantidad_bonificada_monto_${nuevoIndice}[]" 
                                       class="form-control cantidad-bonificada-input" 
                                       min="1" placeholder="Cant." disabled>
                            </div>
                            <div class="col-2">
                                <button type="button" class="btn btn-danger btn-sm btn-quitar-producto-bonificado" 
                                        title="Quitar producto" style="display: none;">
                                    <i class="fas fa-times"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                <button type="button" class="btn btn-success btn-sm btn-agregar-producto-bonificado" 
                        title="Agregar más productos bonificados">
                    <i class="fas fa-plus"></i> Agregar Producto
                </button>
            </td>
            <td>
                <button type="button" class="btn btn-success btn-sm btn-agregar-rango-monto me-1 mb-1" 
                        title="Agregar rango">
                    <i class="fas fa-plus"></i>
                </button>
                <button type="button" class="btn btn-danger btn-sm btn-eliminar-rango-monto" 
                        title="Eliminar rango">
                    <i class="fas fa-times"></i>
                </button>
            </td>
        `;
        
        tabla.appendChild(nuevaFila);
        actualizarSelectsProductoBonificado();
        contadorRangosMonto = nuevoIndice + 1;
        
        setTimeout(() => {
            botonesAgregar.forEach(btn => btn.disabled = false);
        }, 300);
        
        console.log(`✅ Rango de monto agregado. Total rangos: ${contadorRangosMonto}`);
    }

    function eliminarRangoMonto(boton) {
        const tabla = document.getElementById('tabla-rangos-monto-body');
        if (!tabla) return;
        
        const filas = tabla.querySelectorAll('.rango-monto-item');
        
        if (filas.length > 1) {
            const filaAEliminar = boton.closest('.rango-monto-item');
            const indiceEliminado = parseInt(filaAEliminar.getAttribute('data-index') || '0');
            
            console.log(`🗑️ Eliminando rango de monto ${indiceEliminado}`);
            
            boton.disabled = true;
            filaAEliminar.remove();
            
            // REINDEXAR todas las filas restantes
            const filasRestantes = tabla.querySelectorAll('.rango-monto-item');
            filasRestantes.forEach((fila, nuevoIndice) => {
                console.log(`🔄 Reindexando fila de ${fila.getAttribute('data-index')} a ${nuevoIndice}`);
                
                fila.setAttribute('data-index', nuevoIndice);
                
                const inputs = fila.querySelectorAll('input[data-rango-index]');
                inputs.forEach(input => {
                    input.setAttribute('data-rango-index', nuevoIndice);
                });
                
                const selectsProductos = fila.querySelectorAll('select[name*="producto_bonificado_monto_"]');
                const inputsCantidades = fila.querySelectorAll('input[name*="cantidad_bonificada_monto_"]');
                
                selectsProductos.forEach(select => {
                    select.name = `producto_bonificado_monto_${nuevoIndice}[]`;
                });
                
                inputsCantidades.forEach(input => {
                    input.name = `cantidad_bonificada_monto_${nuevoIndice}[]`;
                });
            });
            
            contadorRangosMonto = filasRestantes.length;
            console.log(`✅ Rango eliminado. Rangos restantes: ${contadorRangosMonto}`);
        }
    }

    function agregarProductoBonificado(boton) {
        const fila = boton.closest('tr');
        const container = fila.querySelector('.productos-bonificados-container');
        const rangoIndex = fila.getAttribute('data-index') || '0';
        
        console.log(`🎁 Agregando producto bonificado al rango ${rangoIndex}`);
        
        boton.disabled = true;
        
        const nuevoProductoDiv = document.createElement('div');
        nuevoProductoDiv.className = 'producto-bonificado-item mb-2';
        nuevoProductoDiv.innerHTML = `
            <div class="row">
                <div class="col-7">
                    <select name="producto_bonificado_cantidad_${rangoIndex}[]" class="form-select producto-bonificado-select">
                        <option value="">Seleccione producto</option>
                    </select>
                </div>
                <div class="col-3">
                    <input type="number" name="cantidad_bonificada_cantidad_${rangoIndex}[]" 
                           class="form-control cantidad-bonificada-input" 
                           min="1" placeholder="Cant." disabled>
                </div>
                <div class="col-2">
                    <button type="button" class="btn btn-danger btn-sm btn-quitar-producto-bonificado" 
                            title="Quitar producto">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;
        
        container.appendChild(nuevoProductoDiv);
        actualizarSelectsProductoBonificado();
        actualizarBotonesQuitarProducto(container);
        
        setTimeout(() => {
            boton.disabled = false;
        }, 300);
        
        console.log(`✅ Producto bonificado agregado al rango ${rangoIndex}`);
    }

    function agregarProductoBonificadoMonto(boton) {
        const fila = boton.closest('tr');
        const container = fila.querySelector('.productos-bonificados-container');
        const rangoIndex = fila.getAttribute('data-index') || '0';
        
        console.log(`🎁 Agregando producto bonificado al rango de monto ${rangoIndex}`);
        
        boton.disabled = true;
        
        const nuevoProductoDiv = document.createElement('div');
        nuevoProductoDiv.className = 'producto-bonificado-item mb-2';
        nuevoProductoDiv.innerHTML = `
            <div class="row">
                <div class="col-7">
                    <select name="producto_bonificado_monto_${rangoIndex}[]" class="form-select producto-bonificado-select">
                        <option value="">Seleccione producto</option>
                    </select>
                </div>
                <div class="col-3">
                    <input type="number" name="cantidad_bonificada_monto_${rangoIndex}[]" 
                           class="form-control cantidad-bonificada-input" 
                           min="1" placeholder="Cant." disabled>
                </div>
                <div class="col-2">
                    <button type="button" class="btn btn-danger btn-sm btn-quitar-producto-bonificado" 
                            title="Quitar producto">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;
        
        container.appendChild(nuevoProductoDiv);
        actualizarSelectsProductoBonificado();
        actualizarBotonesQuitarProducto(container);
        
        setTimeout(() => {
            boton.disabled = false;
        }, 300);
        
        console.log(`✅ Producto bonificado agregado al rango de monto ${rangoIndex}`);
    }

    function quitarProductoBonificado(boton) {
        const fila = boton.closest('tr');
        const container = fila.querySelector('.productos-bonificados-container');
        const productosItems = container.querySelectorAll('.producto-bonificado-item');
        
        if (productosItems.length > 1) {
            boton.closest('.producto-bonificado-item').remove();
            actualizarBotonesQuitarProducto(container);
            controlarPromocionEscalable();
            console.log('✅ Producto bonificado eliminado');
        }
    }

    function actualizarBotonesQuitarProducto(container) {
        const productosItems = container.querySelectorAll('.producto-bonificado-item');
        const botonesQuitar = container.querySelectorAll('.btn-quitar-producto-bonificado');
        
        botonesQuitar.forEach((btn, index) => {
            if (productosItems.length > 1) {
                btn.style.display = 'block';
            } else {
                btn.style.display = 'none';
            }
        });
    }

    function actualizarSelectsProductoBonificado() {
        const selects = document.querySelectorAll('.producto-bonificado-select');
        
        selects.forEach(select => {
            const valorActual = select.value;
            select.innerHTML = '<option value="">Sin producto bonificado</option>';
            
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
        
        document.querySelectorAll('.productos-bonificados-container').forEach(container => {
            actualizarBotonesQuitarProducto(container);
        });
    }

    // === BONIFICACIONES ===
    function configurarBonificaciones() {
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('btn-agregar-bonificacion')) {
                agregarBonificacion();
            } else if (e.target.classList.contains('btn-eliminar-bonificacion')) {
                eliminarBonificacion(e.target);
            } else if (e.target.classList.contains('btn-agregar-bonificacion-ambos')) {
                agregarBonificacionAmbos();
            } else if (e.target.classList.contains('btn-eliminar-bonificacion-ambos')) {
                eliminarBonificacionAmbos(e.target);
            }
        });
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

    // === FUNCIONES NUEVAS PARA RANGOS ILIMITADOS ===
    function contarRangosActivos() {
        const rangosCantidad = document.querySelectorAll('#tabla-rangos-cantidad-body .rango-cantidad-item');
        const rangosMonto = document.querySelectorAll('#tabla-rangos-monto-body .rango-monto-item');
        
        return {
            cantidad: rangosCantidad.length,
            monto: rangosMonto.length,
            total: rangosCantidad.length + rangosMonto.length
        };
    }

    function validarIndicesRangos() {
        console.log('\n🔍 === VALIDANDO ÍNDICES DE RANGOS ===');
        
        const rangosCantidad = document.querySelectorAll('#tabla-rangos-cantidad-body .rango-cantidad-item');
        rangosCantidad.forEach((fila, indiceEsperado) => {
            const indiceAtributo = parseInt(fila.getAttribute('data-index') || '0');
            const isValid = indiceAtributo === indiceEsperado;
            
            if (!isValid) {
                console.log(`🔧 Corrigiendo índice de cantidad ${indiceAtributo} a ${indiceEsperado}`);
                fila.setAttribute('data-index', indiceEsperado);
            }
            
            const selectsProductos = fila.querySelectorAll('select[name*="producto_bonificado_cantidad_"]');
            selectsProductos.forEach(select => {
                const nombreEsperado = `producto_bonificado_cantidad_${indiceEsperado}[]`;
                if (select.name !== nombreEsperado) {
                    select.name = nombreEsperado;
                }
            });
        });
        
        const rangosMonto = document.querySelectorAll('#tabla-rangos-monto-body .rango-monto-item');
        rangosMonto.forEach((fila, indiceEsperado) => {
            const indiceAtributo = parseInt(fila.getAttribute('data-index') || '0');
            const isValid = indiceAtributo === indiceEsperado;
            
            if (!isValid) {
                console.log(`🔧 Corrigiendo índice de monto ${indiceAtributo} a ${indiceEsperado}`);
                fila.setAttribute('data-index', indiceEsperado);
            }
            
            const selectsProductos = fila.querySelectorAll('select[name*="producto_bonificado_monto_"]');
            selectsProductos.forEach(select => {
                const nombreEsperado = `producto_bonificado_monto_${indiceEsperado}[]`;
                if (select.name !== nombreEsperado) {
                    select.name = nombreEsperado;
                }
            });
        });
        
        console.log('=== FIN VALIDACIÓN ÍNDICES ===\n');
    }

    // ✅ FUNCIÓN 1: Determinar si se requieren rangos
    function seRequierenRangos() {
        const tipoFiltro = document.querySelector('input[name="tipo_filtro"]:checked')?.value;
        const productosSeleccionados = Array.from(document.querySelectorAll('.productos-condicion-select'))
            .map(s => s.value).filter(val => val !== '');
        
        // CASO 1: Productos específicos con EXACTAMENTE 1 producto → SÍ requiere rangos
        if (tipoFiltro === 'productos_especificos' && productosSeleccionados.length === 1) {
            return true;
        }
        
        // CASO 2: Productos específicos con MÁS de 1 producto → NO requiere rangos
        if (tipoFiltro === 'productos_especificos' && productosSeleccionados.length > 1) {
            return false;
        }
        
        // CASO 3: Marca/Línea completa → NO requiere rangos
        if (tipoFiltro === 'linea_marca') {
            return false;
        }
        
        // Por defecto, no se requieren rangos
        return false;
    }

    // ✅ FUNCIÓN 2: Validar consistencia solo cuando se requieren rangos
    function validarConsistenciaRangos() {
        console.log('\n🔧 === VALIDANDO CONSISTENCIA DE RANGOS ===');
        
        // ✅ NUEVO: Verificar si se requieren rangos
        if (!seRequierenRangos()) {
            console.log('✅ No se requieren rangos para esta configuración, saltando validación');
            return true;
        }
        
        console.log('🎯 Se requieren rangos, procediendo con validación...');
        
        // Validar y corregir índices si es necesario
        validarIndicesRangos();
        
        // Contar rangos activos
        const stats = contarRangosActivos();
        
        if (stats.total === 0) {
            console.log('❌ Se requieren rangos pero no hay ninguno configurado');
            return false;
        }
        
        // Verificar que cada rango tenga datos mínimos
        let rangosValidos = 0;
        
        // Validar rangos de cantidad
        const rangosCantidad = document.querySelectorAll('#tabla-rangos-cantidad-body .rango-cantidad-item');
        rangosCantidad.forEach((fila, indice) => {
            const cantidadMin = fila.querySelector('input[name="cantidad_min[]"]')?.value;
            if (cantidadMin && parseInt(cantidadMin) > 0) {
                rangosValidos++;
                console.log(`✅ Rango cantidad ${indice}: válido (min: ${cantidadMin})`);
            } else {
                console.log(`⚠️ Rango cantidad ${indice}: inválido (min: ${cantidadMin})`);
            }
        });
        
        // Validar rangos de monto
        const rangosMonto = document.querySelectorAll('#tabla-rangos-monto-body .rango-monto-item');
        rangosMonto.forEach((fila, indice) => {
            const montoMin = fila.querySelector('input[name="monto_minimo[]"]')?.value;
            if (montoMin && parseFloat(montoMin) > 0) {
                rangosValidos++;
                console.log(`✅ Rango monto ${indice}: válido (min: S/${montoMin})`);
            } else {
                console.log(`⚠️ Rango monto ${indice}: inválido (min: ${montoMin})`);
            }
        });
        
        console.log(`📊 Resumen: ${rangosValidos} rangos válidos de ${stats.total} total`);
        console.log('=== FIN VALIDACIÓN CONSISTENCIA ===\n');
        
        return rangosValidos > 0;
    }

    // === VALIDACIONES ===
    function validarFormulario() {
        console.log('🔍 === INICIANDO VALIDACIÓN DEL FORMULARIO ===');
        
        // 1. Validar información básica SIEMPRE
        if (!verificarInformacionBasica()) {
            console.log('❌ Validación fallida: Información básica incompleta');
            alert('Por favor complete toda la información básica obligatoria:\n- Descripción\n- Empresa\n- Sucursal\n- Canal de Cliente\n- Fecha de Inicio\n- Fecha de Fin');
            return false;
        }
        console.log('✅ Información básica válida');

        // 2. Validar configuración de productos SIEMPRE
        if (!verificarConfiguracionProductos()) {
            console.log('❌ Validación fallida: Configuración de productos incompleta');
            alert('Por favor complete la configuración de productos');
            return false;
        }
        console.log('✅ Configuración de productos válida');

        // 3. Validar estructura específica según el tipo de filtro
        const tipoFiltro = document.querySelector('input[name="tipo_filtro"]:checked')?.value;
        const productosSeleccionados = Array.from(document.querySelectorAll('.productos-condicion-select'))
            .map(s => s.value).filter(val => val !== '');
        
        console.log(`📊 Tipo de filtro: ${tipoFiltro}`);
        console.log(`📦 Productos seleccionados: ${productosSeleccionados.length}`);

        if (tipoFiltro === 'linea_marca') {
            // CASO: Por Marca/Línea completa - DEBE tener beneficios
            const tipoBeneficio = tipoBeneficioSelect?.value;
            if (!tipoBeneficio) {
                console.log('❌ Validación fallida: Falta tipo de beneficio para marca/línea');
                alert('Para promociones por Marca/Línea debe seleccionar un tipo de beneficio');
                return false;
            }
            
            if (!validarBeneficios(tipoBeneficio)) {
                return false;
            }
            console.log('✅ Promoción por Marca/Línea válida');
            
        } else if (tipoFiltro === 'productos_especificos') {
            
            if (productosSeleccionados.length === 1) {
                // CASO: 1 producto específico - DEBE tener condiciones/rangos
                console.log('🎯 Validando caso: 1 producto específico (requiere rangos)');
                
                const tipoCondicion = tipoCondicionSelect?.value;
                if (!tipoCondicion) {
                    console.log('❌ Validación fallida: Falta tipo de condición para producto específico');
                    alert('Para 1 producto específico debe configurar las condiciones de activación');
                    return false;
                }
                
                if (!validarCondiciones(tipoCondicion)) {
                    return false;
                }
                console.log('✅ Producto específico con condiciones válido');
                
            } else if (productosSeleccionados.length > 1) {
                // CASO: Múltiples productos específicos - DEBE tener beneficios (NO rangos)
                console.log('🎁 Validando caso: múltiples productos específicos (requiere beneficios, NO rangos)');
                
                const tipoBeneficio = tipoBeneficioSelect?.value;
                if (!tipoBeneficio) {
                    console.log('❌ Validación fallida: Falta tipo de beneficio para múltiples productos');
                    alert('Para múltiples productos específicos debe seleccionar un tipo de beneficio');
                    return false;
                }
                
                if (!validarBeneficios(tipoBeneficio)) {
                    return false;
                }
                console.log('✅ Múltiples productos específicos con beneficios válido');
            }
        }

        console.log('✅ === FORMULARIO VÁLIDO COMPLETAMENTE ===');
        return true;
    }

    function validarCondiciones(tipoCondicion) {
        if (tipoCondicion === 'cantidad') {
            const cantidadesMin = document.querySelectorAll('[name="cantidad_min[]"]');
            const primerCantidad = cantidadesMin[0]?.value;
            
            if (!primerCantidad || parseInt(primerCantidad) <= 0) {
                alert('Debe especificar al menos una cantidad mínima válida en las condiciones');
                return false;
            }
            
        } else if (tipoCondicion === 'monto') {
            const montosMin = document.querySelectorAll('[name="monto_minimo[]"]');
            const primerMonto = montosMin[0]?.value;
            
            if (!primerMonto || parseFloat(primerMonto) <= 0) {
                alert('Debe especificar al menos un monto mínimo válido en las condiciones');
                return false;
            }
        }
        
        return true;
    }

    function validarBeneficios(tipoBeneficio) {
        if (tipoBeneficio === '1') {
            const productos = document.querySelectorAll('#beneficios-bonificacion [name="productos_bonificados[]"]');
            const cantidades = document.querySelectorAll('#beneficios-bonificacion [name="cantidad_bonificada[]"]');
            
            if (!productos[0]?.value || !cantidades[0]?.value || parseInt(cantidades[0].value) <= 0) {
                alert('Debe seleccionar al menos un producto bonificado con su cantidad');
                return false;
            }
            
        } else if (tipoBeneficio === '2') {
            const descuento = document.querySelector('#beneficios-descuento [name="porcentaje_descuento"]');
            
            if (!descuento?.value || parseFloat(descuento.value) <= 0) {
                alert('Debe especificar un porcentaje de descuento válido mayor a 0');
                return false;
            }
            
        } else if (tipoBeneficio === '3') {
            const productos = document.querySelectorAll('#beneficios-ambos [name="productos_bonificados_ambos[]"]');
            const cantidades = document.querySelectorAll('#beneficios-ambos [name="cantidad_bonificada_ambos[]"]');
            const descuento = document.querySelector('#beneficios-ambos [name="porcentaje_descuento_ambos"]');
            
            if (!productos[0]?.value || !cantidades[0]?.value || parseInt(cantidades[0].value) <= 0) {
                alert('Debe seleccionar al menos un producto bonificado con su cantidad');
                return false;
            }
            
            if (!descuento?.value || parseFloat(descuento.value) <= 0) {
                alert('Debe especificar un porcentaje de descuento válido mayor a 0');
                return false;
            }
        }
        
        return true;
    }

    // === UTILIDADES ===
    function resetSelect(select, placeholder) {
        if (select) {
            select.innerHTML = `<option value="">${placeholder}</option>`;
            select.disabled = true;
        }
    }

    function agregarClaseDeshabilitada(elemento) {
        if (elemento) {
            elemento.classList.add('seccion-deshabilitada');
            elemento.style.opacity = '0.6';
            elemento.style.pointerEvents = 'none';
        }
    }

    function quitarClaseDeshabilitada(elemento) {
        if (elemento) {
            elemento.classList.remove('seccion-deshabilitada');
            elemento.style.opacity = '1';
            elemento.style.pointerEvents = 'auto';
        }
    }

    // === EVENT LISTENER PRINCIPAL DEL FORMULARIO ===
    const formulario = document.getElementById('form-promocion');
    if (formulario) {
        formulario.addEventListener('submit', function(e) {
            console.log('\n📝 === SUBMIT CON VALIDACIÓN DE RANGOS ILIMITADOS ===');
            e.preventDefault();
            
            if (!validarConsistenciaRangos()) {
                alert('❌ Error: Hay problemas con la configuración de rangos');
                return false;
            }
            
            debugFormularioDetallado();
            
            if (validarFormulario()) {
                console.log('✅ Formulario válido, enviando...');
                
                const stats = contarRangosActivos();
                console.log(`🚀 Enviando promoción con ${stats.total} rangos (${stats.cantidad} cantidad + ${stats.monto} monto)`);
                
                this.removeEventListener('submit', arguments.callee);
                this.submit();
            } else {
                console.log('❌ Validación fallida');
            }
            
            return false;
        });
        
        console.log('✅ Event listener configurado para rangos ilimitados');
    }

    // === AUTO-VALIDACIÓN ===
    document.addEventListener('change', function(e) {
        if (e.target.matches('input[name*="cantidad_min"], input[name*="monto_minimo"]')) {
            setTimeout(() => {
                const stats = contarRangosActivos();
                console.log(`🔄 Rangos modificados. Total activos: ${stats.total}`);
            }, 500);
        }
    });


    // ✅ FUNCIÓN 6: Debug mejorado que muestra el contexto
    function debugFormularioDetallado() {
        console.log('\n🔍 === DEBUG DETALLADO DEL FORMULARIO ===');
        
        const form = document.getElementById('form-promocion');
        if (!form) {
            console.log('❌ Formulario no encontrado');
            return;
        }
        
        const formData = new FormData(form);
        
        // Debug información básica
        console.log('📋 INFORMACIÓN BÁSICA:');
        console.log(`   descripcion: ${formData.get('descripcion')}`);
        console.log(`   empresa: ${formData.get('empresa')}`);
        
        // Debug configuración de productos
        const tipoFiltro = formData.get('tipo_filtro');
        console.log('\n📦 CONFIGURACIÓN DE PRODUCTOS:');
        console.log(`   tipo_filtro: ${tipoFiltro}`);
        
        if (tipoFiltro === 'linea_marca') {
            console.log(`   grupo_proveedor: ${formData.get('grupo_proveedor')}`);
            console.log(`   linea_articulo: ${formData.get('linea_articulo')}`);
            console.log(`   monto_minimo_productos: ${formData.get('monto_minimo_productos')}`);
        } else {
            const productos = formData.getAll('productos_condicion');
            console.log(`   productos_condicion: ${JSON.stringify(productos)}`);
            console.log(`   total productos: ${productos.filter(p => p !== '').length}`);
        }
        
        // Debug contexto de validación
        const requiereRangos = seRequierenRangos();
        console.log('\n🎯 CONTEXTO DE VALIDACIÓN:');
        console.log(`   requiere_rangos: ${requiereRangos}`);
        
        // Debug condiciones (solo si se requieren rangos)
        if (requiereRangos) {
            const tipoCondicion = formData.get('tipo_condicion');
            console.log(`   tipo_condicion: ${tipoCondicion}`);
            
            if (tipoCondicion === 'cantidad') {
                const cantidadMin = formData.getAll('cantidad_min[]');
                console.log(`   📊 RANGOS DE CANTIDAD: ${cantidadMin.length}`);
                
                for (let i = 0; i < cantidadMin.length; i++) {
                    if (cantidadMin[i]) {
                        const productos = formData.getAll(`producto_bonificado_cantidad_${i}[]`);
                        const cantidades = formData.getAll(`cantidad_bonificada_cantidad_${i}[]`);
                        console.log(`   📦 Rango cantidad ${i}: ${productos.filter(p => p !== '').length} productos`);
                    }
                }
                
            } else if (tipoCondicion === 'monto') {
                const montoMin = formData.getAll('monto_minimo[]');
                console.log(`   📊 RANGOS DE MONTO: ${montoMin.length}`);
                
                for (let i = 0; i < montoMin.length; i++) {
                    if (montoMin[i]) {
                        const productos = formData.getAll(`producto_bonificado_monto_${i}[]`);
                        const cantidades = formData.getAll(`cantidad_bonificada_monto_${i}[]`);
                        console.log(`   📦 Rango monto ${i}: ${productos.filter(p => p !== '').length} productos`);
                    }
                }
            }
        } else {
            console.log('   ⚠️ No se requieren rangos para esta configuración');
        }
        
        // Debug beneficios
        const tipoBeneficio = formData.get('tipo_beneficio');
        if (tipoBeneficio) {
            console.log('\n🎁 BENEFICIOS:');
            console.log(`   tipo_beneficio: ${tipoBeneficio}`);
            
            if (tipoBeneficio === '1') {
                const productos = formData.getAll('productos_bonificados[]');
                console.log(`   productos_bonificados: ${productos.filter(p => p !== '').length} productos`);
            } else if (tipoBeneficio === '2') {
                console.log(`   porcentaje_descuento: ${formData.get('porcentaje_descuento')}%`);
            } else if (tipoBeneficio === '3') {
                const productos = formData.getAll('productos_bonificados_ambos[]');
                console.log(`   productos_bonificados_ambos: ${productos.filter(p => p !== '').length} productos`);
                console.log(`   porcentaje_descuento_ambos: ${formData.get('porcentaje_descuento_ambos')}%`);
            }
        }
        
        console.log('=== FIN DEBUG DETALLADO ===\n');
    }

    console.log('✅ jvPromos.js configurado para RANGOS ILIMITADOS - Versión Completa con Condiciones de Guardado');
});