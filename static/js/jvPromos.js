// static/js/jvPromos.js - VERSIÓN COMPLETA CON RANGOS ILIMITADOS Y CONDICIONES DE GUARDADO
document.addEventListener('DOMContentLoaded', function () {    
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
                cargarArticulos(this.value);
                evaluarEstadoFormulario();
            });
        }

        // Cambios en marca
        if (marcaSelect) {
            marcaSelect.addEventListener('change', function() {
                cargarLineasPorMarca(this.value);
                if (montoMinimoProductos) montoMinimoProductos.disabled = true;
                evaluarEstadoFormulario();
            });
        }

        // Cambios en línea
        if (lineaSelect) {
            lineaSelect.addEventListener('change', function() {
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
        const informacionBasicaCompleta = verificarInformacionBasica();
        const configuracionProductosCompleta = verificarConfiguracionProductos();
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
        if (!empresaId) {
            resetSelect(sucursalSelect, 'Seleccione una sucursal');
            return;
        }

        try {
            const response = await fetch(`/core/api/sucursales/?empresa_id=${empresaId}`);
            const sucursales = await response.json();            
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
        if (!empresaId) {
            resetSelect(marcaSelect, 'Seleccione una marca');
            return;
        }

        try {
            const response = await fetch(`/core/api/marcas_por_empresa/?empresa_id=${empresaId}`);
            const marcas = await response.json();            
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
        if (!marcaId) {
            resetSelect(lineaSelect, 'Seleccione una línea');
            return;
        }

        try {
            const response = await fetch(`/core/api/lineas_por_marca/?marca_id=${marcaId}`);
            const lineas = await response.json();            
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
        if (!sucursalId) {
            articulosDisponibles = [];
            actualizarSelectsProductos();
            return;
        }

        try {
            const response = await fetch(`/core/api/articulos_por_sucursal/?sucursal_id=${sucursalId}`);
            articulosDisponibles = await response.json();
                        
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
        const tipoSeleccionado = document.querySelector('input[name="tipo_filtro"]:checked')?.value;

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

        // ❌ REMOVER event listeners previos para evitar duplicados
        const clonedContainer = container.cloneNode(true);
        container.parentNode.replaceChild(clonedContainer, container);
        
        // ✅ AGREGAR event listeners solo una vez
        clonedContainer.addEventListener('click', function(e) {
            // Prevenir múltiples ejecuciones
            if (e.target.disabled) {
                e.preventDefault();
                e.stopPropagation();
                return;
            }

            if (e.target.classList.contains('btn-agregar-producto')) {
                e.preventDefault();
                e.stopPropagation();
                
                // Deshabilitar temporalmente
                e.target.disabled = true;
                setTimeout(() => {
                    if (e.target) e.target.disabled = false;
                }, 300);
                
                agregarProductoCondicion();
                
            } else if (e.target.classList.contains('btn-eliminar-producto')) {
                e.preventDefault();
                e.stopPropagation();
                
                e.target.disabled = true;
                setTimeout(() => {
                    if (e.target && e.target.parentNode) e.target.disabled = false;
                }, 300);
                
                eliminarProductoCondicion(e.target);
            }
        });

        clonedContainer.addEventListener('change', function(e) {
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
        // ✅ EVITAR múltiples configuraciones
        if (window.rangosEventoConfigurado) return;
        window.rangosEventoConfigurado = true;

        document.addEventListener('click', function(e) {
            if (e.target.disabled) {
                e.preventDefault();
                e.stopPropagation();
                return;
            }
            
            let manejado = false;
            
            // === RANGOS CANTIDAD ===
            if (e.target.classList.contains('btn-agregar-rango-cantidad')) {
                e.preventDefault();
                e.stopPropagation();                
                e.target.disabled = true;
                setTimeout(() => {
                    if (e.target) e.target.disabled = false;
                }, 400);
                
                agregarRangoCantidad();
                manejado = true;
                
            } else if (e.target.classList.contains('btn-eliminar-rango-cantidad')) {
                e.preventDefault();
                e.stopPropagation();
                
                e.target.disabled = true;
                eliminarRangoCantidad(e.target);
                manejado = true;
                
            } else if (e.target.classList.contains('btn-agregar-producto-bonificado')) {
                e.preventDefault();
                e.stopPropagation();
                
                const tablaPadre = e.target.closest('table');
                if (tablaPadre && tablaPadre.id === 'tabla-rangos-cantidad') {                    
                    e.target.disabled = true;
                    setTimeout(() => {
                        if (e.target) e.target.disabled = false;
                    }, 300);
                    
                    agregarProductoBonificado(e.target);
                    manejado = true;
                    
                } else if (tablaPadre && tablaPadre.id === 'tabla-rangos-monto') {
                    e.target.disabled = true;
                    setTimeout(() => {
                        if (e.target) e.target.disabled = false;
                    }, 300);
                    
                    agregarProductoBonificadoMonto(e.target);
                    manejado = true;
                }
                
            } else if (e.target.classList.contains('btn-quitar-producto-bonificado')) {
                e.preventDefault();
                e.stopPropagation();
                
                e.target.disabled = true;
                quitarProductoBonificado(e.target);
                manejado = true;
            }
            
            // === RANGOS MONTO ===
            else if (e.target.classList.contains('btn-agregar-rango-monto')) {
                e.preventDefault();
                e.stopPropagation();                
                e.target.disabled = true;
                setTimeout(() => {
                    if (e.target) e.target.disabled = false;
                }, 400);
                
                agregarRangoMonto();
                manejado = true;
                
            } else if (e.target.classList.contains('btn-eliminar-rango-monto')) {
                e.preventDefault();
                e.stopPropagation();
                
                e.target.disabled = true;
                eliminarRangoMonto(e.target);
                manejado = true;
            }
        });

        // Event listeners para cambios e inputs
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
    }

    function eliminarRangoCantidad(boton) {
        const tabla = document.getElementById('tabla-rangos-cantidad-body');
        if (!tabla) return;
        
        const filas = tabla.querySelectorAll('.rango-cantidad-item');
        
        if (filas.length > 1) {
            const filaAEliminar = boton.closest('.rango-cantidad-item');
            const indiceEliminado = parseInt(filaAEliminar.getAttribute('data-index') || '0');
                        
            boton.disabled = true;
            filaAEliminar.remove();
            
            // REINDEXAR todas las filas restantes
            const filasRestantes = tabla.querySelectorAll('.rango-cantidad-item');
            filasRestantes.forEach((fila, nuevoIndice) => {
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
        }, 10);
        
    }

    function eliminarRangoMonto(boton) {
        const tabla = document.getElementById('tabla-rangos-monto-body');
        if (!tabla) return;
        
        const filas = tabla.querySelectorAll('.rango-monto-item');
        
        if (filas.length > 1) {
            const filaAEliminar = boton.closest('.rango-monto-item');
            const indiceEliminado = parseInt(filaAEliminar.getAttribute('data-index') || '0');
                        
            boton.disabled = true;
            filaAEliminar.remove();
            
            // REINDEXAR todas las filas restantes
            const filasRestantes = tabla.querySelectorAll('.rango-monto-item');
            filasRestantes.forEach((fila, nuevoIndice) => {
                
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
        }
    }

    function agregarProductoBonificado(boton) {
        const fila = boton.closest('tr');
        const container = fila.querySelector('.productos-bonificados-container');
        const rangoIndex = fila.getAttribute('data-index') || '0';
                
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
        
    }

    function agregarProductoBonificadoMonto(boton) {
        const fila = boton.closest('tr');
        const container = fila.querySelector('.productos-bonificados-container');
        const rangoIndex = fila.getAttribute('data-index') || '0';
                
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
        
    }

    function quitarProductoBonificado(boton) {
        const fila = boton.closest('tr');
        const container = fila.querySelector('.productos-bonificados-container');
        const productosItems = container.querySelectorAll('.producto-bonificado-item');
        
        if (productosItems.length > 1) {
            boton.closest('.producto-bonificado-item').remove();
            actualizarBotonesQuitarProducto(container);
            controlarPromocionEscalable();
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
        // ✅ USAR event delegation en document - SOLO UNA VEZ
        if (window.bonificacionesEventoConfigurado) return;
        window.bonificacionesEventoConfigurado = true;
        
        document.addEventListener('click', function(e) {
            // Prevenir si está deshabilitado
            if (e.target.disabled) {
                e.preventDefault();
                e.stopPropagation();
                return;
            }

            let manejado = false;

            // === BONIFICACIONES SOLO BONIFICACIÓN ===
            if (e.target.classList.contains('btn-agregar-bonificacion')) {
                e.preventDefault();
                e.stopPropagation();
                
                // ✅ DESHABILITACIÓN MUY BREVE para evitar doble click
                e.target.disabled = true;
                
                agregarBonificacion();
                
                // ✅ REHABILITAR INMEDIATAMENTE después de agregar
                setTimeout(() => {
                    rehabilitarTodosLosBotonesBonificacion();
                }, 50);
                
                manejado = true;
                
            } else if (e.target.classList.contains('btn-eliminar-bonificacion')) {
                e.preventDefault();
                e.stopPropagation();                
                e.target.disabled = true;
                eliminarBonificacion(e.target);
                
                setTimeout(() => {
                    rehabilitarTodosLosBotonesBonificacion();
                }, 50);
                
                manejado = true;
            }

            // === BONIFICACIONES AMBOS ===
            else if (e.target.classList.contains('btn-agregar-bonificacion-ambos')) {
                e.preventDefault();
                e.stopPropagation();                
                e.target.disabled = true;
                
                agregarBonificacionAmbos();
                
                setTimeout(() => {
                    rehabilitarTodosLosBotonesAmbos();
                }, 50);
                
                manejado = true;
                
            } else if (e.target.classList.contains('btn-eliminar-bonificacion-ambos')) {
                e.preventDefault();
                e.stopPropagation();                
                e.target.disabled = true;
                eliminarBonificacionAmbos(e.target);
                
                setTimeout(() => {
                    rehabilitarTodosLosBotonesAmbos();
                }, 50);
                
                manejado = true;
            }
        });

        // Event listener para cambios en selects de bonificación
        document.addEventListener('change', function(e) {
            if (e.target.classList.contains('select-bonificacion') || 
                e.target.classList.contains('select-bonificacion-ambos')) {
                actualizarSelectsBonificacionMejorada();
            }
        });
    }

    function agregarBonificacion() {
        const tabla = document.getElementById('tabla-bonificaciones');
        if (!tabla) {
            console.error('❌ Tabla bonificaciones no encontrada');
            return;
        }
        
        const template = tabla.querySelector('.bonificacion-item');
        if (!template) {
            console.error('❌ Template bonificación no encontrado');
            return;
        }
        
        const nuevo = template.cloneNode(true);
        
        // Limpiar valores
        const select = nuevo.querySelector('.select-bonificacion');
        const input = nuevo.querySelector('input[name="cantidad_bonificada[]"]');
        
        if (select) select.value = '';
        if (input) input.value = '';
        
        // ✅ ASEGURAR que los botones estén habilitados
        const botonesEnNuevo = nuevo.querySelectorAll('button');
        botonesEnNuevo.forEach(btn => {
            btn.disabled = false;
            btn.classList.remove('disabled');
        });
        
        tabla.appendChild(nuevo);
        
        // ✅ REHABILITAR TODOS los botones después de agregar
        rehabilitarTodosLosBotonesBonificacion();
        actualizarSelectsBonificacionMejorada();
    }

    function rehabilitarTodosLosBotonesBonificacion() {        
        const tabla = document.getElementById('tabla-bonificaciones');
        if (!tabla) return;
        
        // Rehabilitar todos los botones "+" y "x" en la tabla
        const botones = tabla.querySelectorAll('.btn-agregar-bonificacion, .btn-eliminar-bonificacion');
        botones.forEach((btn, index) => {
            btn.disabled = false;
            btn.classList.remove('disabled');
        });
        
        // Gestionar visibilidad de botones eliminar
        const filas = tabla.querySelectorAll('.bonificacion-item');
        filas.forEach(fila => {
            const btnEliminar = fila.querySelector('.btn-eliminar-bonificacion');
            if (btnEliminar) {
                btnEliminar.disabled = filas.length === 1;
            }
        });
    }

    function rehabilitarTodosLosBotonesAmbos() {        
        const tabla = document.getElementById('tabla-bonificaciones-ambos');
        if (!tabla) return;
        
        // Rehabilitar todos los botones "+" y "x" en la tabla
        const botones = tabla.querySelectorAll('.btn-agregar-bonificacion-ambos, .btn-eliminar-bonificacion-ambos');
        botones.forEach((btn, index) => {
            btn.disabled = false;
            btn.classList.remove('disabled');
        });
        
        // Gestionar visibilidad de botones eliminar
        const filas = tabla.querySelectorAll('.bonificacion-ambos-item');
        filas.forEach(fila => {
            const btnEliminar = fila.querySelector('.btn-eliminar-bonificacion-ambos');
            if (btnEliminar) {
                btnEliminar.disabled = filas.length === 1;
            }
        });
    }

    function eliminarBonificacion(boton) {
        const tabla = document.getElementById('tabla-bonificaciones');
        if (!tabla) return;
        
        const filas = tabla.querySelectorAll('.bonificacion-item');
        
        if (filas.length > 1) {
            const filaAEliminar = boton.closest('.bonificacion-item');
            filaAEliminar.remove();
            // Actualizar selects después de eliminar
            actualizarSelectsBonificacionMejorada();
        } else {
            console.log('No se puede eliminar la última bonificación aqui ando fallando especial');
        }
    }

    function agregarBonificacionAmbos() {
        const tabla = document.getElementById('tabla-bonificaciones-ambos');
        if (!tabla) {
            console.error('❌ Tabla bonificaciones ambos no encontrada');
            return;
        }
        
        const template = tabla.querySelector('.bonificacion-ambos-item');
        if (!template) {
            console.error('❌ Template bonificación ambos no encontrado');
            return;
        }
        
        const nuevo = template.cloneNode(true);
        
        // Limpiar valores
        const select = nuevo.querySelector('.select-bonificacion-ambos');
        const input = nuevo.querySelector('input[name="cantidad_bonificada_ambos[]"]');
        
        if (select) select.value = '';
        if (input) input.value = '';
        
        // ✅ ASEGURAR que los botones estén habilitados
        const botonesEnNuevo = nuevo.querySelectorAll('button');
        botonesEnNuevo.forEach(btn => {
            btn.disabled = false;
            btn.classList.remove('disabled');
        });
        
        tabla.appendChild(nuevo);
        
        // ✅ REHABILITAR TODOS los botones después de agregar
        rehabilitarTodosLosBotonesAmbos();
        actualizarSelectsBonificacionMejorada();
    }

    function eliminarBonificacionAmbos(boton) {
        const tabla = document.getElementById('tabla-bonificaciones-ambos');
        if (!tabla) return;
        
        const filas = tabla.querySelectorAll('.bonificacion-ambos-item');
        
        if (filas.length > 1) {
            const filaAEliminar = boton.closest('.bonificacion-ambos-item');
            filaAEliminar.remove();            
            // Actualizar selects después de eliminar
            actualizarSelectsBonificacionMejorada();
        } else {
            console.log('No se puede eliminar la última bonificación aqui ando fallando especial');
        }
    }


    function actualizarSelectsBonificacionMejorada() {
        // === BONIFICACIONES SOLO BONIFICACIÓN ===
        const selectsSoloBonif = document.querySelectorAll('.select-bonificacion');
        const seleccionadosSoloBonif = Array.from(selectsSoloBonif).map(s => s.value).filter(val => val !== '');
                
        selectsSoloBonif.forEach(select => {
            const valorActual = select.value;
            select.innerHTML = '<option value="">Seleccione un producto</option>';
            
            articulosDisponibles.forEach(articulo => {
                // FILTRAR: No mostrar productos ya seleccionados en otros selects
                const yaSeleccionado = seleccionadosSoloBonif.includes(articulo.articulo_id) && 
                                    articulo.articulo_id !== valorActual;
                
                if (!yaSeleccionado) {
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
        
        // === BONIFICACIONES AMBOS ===
        const selectsAmbos = document.querySelectorAll('.select-bonificacion-ambos');
        const seleccionadosAmbos = Array.from(selectsAmbos).map(s => s.value).filter(val => val !== '');
                
        selectsAmbos.forEach(select => {
            const valorActual = select.value;
            select.innerHTML = '<option value="">Seleccione un producto</option>';
            
            articulosDisponibles.forEach(articulo => {
                // ✅ FILTRAR: No mostrar productos ya seleccionados en otros selects
                const yaSeleccionado = seleccionadosAmbos.includes(articulo.articulo_id) && 
                                    articulo.articulo_id !== valorActual;
                
                if (!yaSeleccionado) {
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
    }

    function actualizarSelectsBonificacion() {
        actualizarSelectsBonificacionMejorada();
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
        const rangosCantidad = document.querySelectorAll('#tabla-rangos-cantidad-body .rango-cantidad-item');
        rangosCantidad.forEach((fila, indiceEsperado) => {
            const indiceAtributo = parseInt(fila.getAttribute('data-index') || '0');
            const isValid = indiceAtributo === indiceEsperado;
            
            if (!isValid) {
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
    }

    function seRequierenRangos() {
        const tipoFiltro = document.querySelector('input[name="tipo_filtro"]:checked')?.value;
        const productosSeleccionados = Array.from(document.querySelectorAll('.productos-condicion-select'))
            .map(s => s.value).filter(val => val !== '');
        
        if (tipoFiltro === 'productos_especificos' && productosSeleccionados.length === 1) {
            return true;
        }
        
        if (tipoFiltro === 'productos_especificos' && productosSeleccionados.length > 1) {
            return false;
        }
        
        if (tipoFiltro === 'linea_marca') {
            return false;
        }
        
        return false;
    }

    function validarConsistenciaRangos() {        
        if (!seRequierenRangos()) {
            return true;
        }        
        validarIndicesRangos();
        
        const stats = contarRangosActivos();
        
        if (stats.total === 0) {
            return false;
        }
        
        let rangosValidos = 0;
        
        // Validar rangos de cantidad
        const rangosCantidad = document.querySelectorAll('#tabla-rangos-cantidad-body .rango-cantidad-item');
        rangosCantidad.forEach((fila, indice) => {
            const cantidadMin = fila.querySelector('input[name="cantidad_min[]"]')?.value;
            if (cantidadMin && parseInt(cantidadMin) > 0) {
                rangosValidos++;
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
        
        return rangosValidos > 0;
    }

    // === VALIDACIONES ===
    function validarFormulario() {        
        // 1. Validar información básica SIEMPRE
        if (!verificarInformacionBasica()) {
            alert('Por favor complete toda la información básica obligatoria:\n- Descripción\n- Empresa\n- Sucursal\n- Canal de Cliente\n- Fecha de Inicio\n- Fecha de Fin');
            return false;
        }
        // 2. Validar configuración de productos SIEMPRE
        if (!verificarConfiguracionProductos()) {
            alert('Por favor complete la configuración de productos');
            return false;
        }
        // 3. Validar estructura específica según el tipo de filtro
        const tipoFiltro = document.querySelector('input[name="tipo_filtro"]:checked')?.value;
        const productosSeleccionados = Array.from(document.querySelectorAll('.productos-condicion-select'))
            .map(s => s.value).filter(val => val !== '');

        if (tipoFiltro === 'linea_marca') {
            // CASO: Por Marca/Línea completa - DEBE tener beneficios
            const tipoBeneficio = tipoBeneficioSelect?.value;
            if (!tipoBeneficio) {
                alert('Para promociones por Marca/Línea debe seleccionar un tipo de beneficio');
                return false;
            }
            
            if (!validarBeneficios(tipoBeneficio)) {
                return false;
            }
            
        } else if (tipoFiltro === 'productos_especificos') {
            
            if (productosSeleccionados.length === 1) {
                // CASO: 1 producto específico - DEBE tener condiciones/rangos                
                const tipoCondicion = tipoCondicionSelect?.value;
                if (!tipoCondicion) {
                    alert('Para 1 producto específico debe configurar las condiciones de activación');
                    return false;
                }
                
                if (!validarCondiciones(tipoCondicion)) {
                    return false;
                }
                
            } else if (productosSeleccionados.length > 1) {
                // CASO: Múltiples productos específicos - DEBE tener beneficios (NO rangos)                
                const tipoBeneficio = tipoBeneficioSelect?.value;
                if (!tipoBeneficio) {
                    alert('Para múltiples productos específicos debe seleccionar un tipo de beneficio');
                    return false;
                }
                
                if (!validarBeneficios(tipoBeneficio)) {
                    return false;
                }
            }
        }
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
            e.preventDefault();
            
            if (!validarConsistenciaRangos()) {
                alert('❌ Error: Hay problemas con la configuración de rangos no estan bien asignados');
                return false;
            }
            
            debugFormularioDetallado();
            
            if (validarFormulario()) {                
                const stats = contarRangosActivos();
                
                this.removeEventListener('submit', arguments.callee);
                this.submit();
            } else {
                console.log('Validación fallida');
            }
            
            return false;
        });
    }

    // === AUTO-VALIDACIÓN ===
    document.addEventListener('change', function(e) {
        if (e.target.matches('input[name*="cantidad_min"], input[name*="monto_minimo"]')) {
            setTimeout(() => {
                const stats = contarRangosActivos();
            }, 200);
        }
    });


    // ✅ FUNCIÓN 6: Debug mejorado que muestra el contexto
    function debugFormularioDetallado() {        
        const form = document.getElementById('form-promocion');
        if (!form) {
            console.log('Formulario no encontrado - linea 1726 esta fallando');
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
});