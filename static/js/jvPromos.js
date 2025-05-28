// static/js/jvPromos.js - VERSIÓN FINAL COMPLETA CON TODAS LAS CORRECCIONES
document.addEventListener('DOMContentLoaded', function () {
    console.log('🚀 jvPromos.js cargado correctamente');
    
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
        
        // Las secciones siempre son visibles, solo deshabilitamos los campos
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

        // Controlar visibilidad de secciones
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

        // Habilitar sección solo si:
        // 1. Información básica completa
        // 2. Tipo filtro es "productos_especificos"  
        // 3. Solo hay 1 producto seleccionado (si hay más de 1, se salta a beneficios)
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

        // Habilitar/deshabilitar tipo de condición
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
        const hayCondicionesLlenas = verificarCondicionesLlenas();
        
        let habilitarBeneficios = false;

        if (tipoFiltro === 'linea_marca') {
            // CASO 1: Por Marca/Línea completa
            // Se habilita cuando la configuración está completa
            habilitarBeneficios = informacionBasicaCompleta && configuracionProductosCompleta;
            
        } else if (tipoFiltro === 'productos_especificos') {
            // CASO 2: Productos específicos
            if (productosSeleccionados.length > 1) {
                // Si hay más de 1 producto: habilitar beneficios directamente (saltar condiciones)
                habilitarBeneficios = informacionBasicaCompleta && configuracionProductosCompleta;
            } else if (productosSeleccionados.length === 1) {
                // Si hay 1 producto: solo habilitar si hay condiciones llenas en intervalos
                habilitarBeneficios = informacionBasicaCompleta && 
                                    configuracionProductosCompleta && 
                                    hayCondicionesLlenas;
            }
        }

        if (seccionBeneficios) {
            if (habilitarBeneficios) {
                quitarClaseDeshabilitada(seccionBeneficios);
            } else {
                agregarClaseDeshabilitada(seccionBeneficios);
            }
        }

        // Habilitar/deshabilitar tipo de beneficio
        if (tipoBeneficioSelect) {
            tipoBeneficioSelect.disabled = !habilitarBeneficios;
            if (!habilitarBeneficios) {
                tipoBeneficioSelect.value = '';
                ocultarTodosLosBeneficios();
            }
        }

        console.log(`🎁 Beneficios: ${habilitarBeneficios ? 'HABILITADOS' : 'DESHABILITADOS'}`);
        console.log(`   📊 Tipo filtro: ${tipoFiltro}`);
        console.log(`   📦 Productos seleccionados: ${productosSeleccionados.length}`);
        console.log(`   ⚙️ Condiciones llenas: ${hayCondicionesLlenas}`);
    }

    function verificarCondicionesLlenas() {
        // Verificar si hay algún campo lleno en las tablas de condiciones
        const descuentosLlenos = Array.from(document.querySelectorAll('.descuento-input')).some(input => input.value.trim() !== '');
        const productosSeleccionados = Array.from(document.querySelectorAll('.producto-bonificado-select')).some(select => select.value !== '');
        
        return descuentosLlenos || productosSeleccionados;
    }

    function controlarPromocionEscalable() {
        if (!promocionEscalable) return;

        const tipoFiltro = document.querySelector('input[name="tipo_filtro"]:checked')?.value;
        const productosSeleccionados = Array.from(document.querySelectorAll('.productos-condicion-select'))
            .map(s => s.value).filter(val => val !== '');
        const tipoCondicion = tipoCondicionSelect?.value;
        const tipoBeneficio = tipoBeneficioSelect?.value;
        
        let habilitarEscalable = false;
        let razonDeshabilitacion = '';

        // === PRIMERA CONDICIÓN ===
        // Productos específicos + 1 producto + Intervalos de Cantidad + Solo cantidad mínima
        if (tipoFiltro === 'productos_especificos' && 
            productosSeleccionados.length === 1 && 
            tipoCondicion === 'cantidad') {
            
            // Verificar que solo se haya llenado la cantidad mínima
            const soloTieneCantidadMinima = verificarSoloCantidadMinima();
            
            if (soloTieneCantidadMinima) {
                habilitarEscalable = true;
                razonDeshabilitacion = 'Condición 1 cumplida: Producto específico + Intervalos de Cantidad + Solo cantidad mínima';
            } else {
                razonDeshabilitacion = 'Condición 1 incompleta: Hay más campos llenos además de cantidad mínima';
            }
        }
        
        // === SEGUNDA CONDICIÓN ===
        // Por Marca/Línea completa + Configuración completa + Tipo beneficio "Bonificación"
        else if (tipoFiltro === 'linea_marca') {
            const configuracionCompleta = verificarConfiguracionLineaMarca();
            const tipoBeneficioTexto = tipoBeneficioSelect?.options[tipoBeneficioSelect?.selectedIndex]?.textContent?.toLowerCase() || '';
            const esBonificacion = tipoBeneficioTexto.includes('bonificación') && !tipoBeneficioTexto.includes('ambos');
            
            if (configuracionCompleta && esBonificacion) {
                habilitarEscalable = true;
                razonDeshabilitacion = 'Condición 2 cumplida: Marca/Línea completa + Bonificación';
            } else if (!configuracionCompleta) {
                razonDeshabilitacion = 'Condición 2 incompleta: Falta completar campos de Marca/Línea';
            } else if (!esBonificacion) {
                razonDeshabilitacion = 'Condición 2 incompleta: Tipo de beneficio debe ser "Bonificación"';
            }
        }
        
        // === CASOS QUE NO CALIFICAN ===
        else {
            if (tipoFiltro === 'productos_especificos') {
                if (productosSeleccionados.length === 0) {
                    razonDeshabilitacion = 'Debe seleccionar exactamente 1 producto específico';
                } else if (productosSeleccionados.length > 1) {
                    razonDeshabilitacion = 'Debe seleccionar exactamente 1 producto (no múltiples)';
                } else if (tipoCondicion !== 'cantidad') {
                    razonDeshabilitacion = 'Debe seleccionar "Intervalos de Cantidad"';
                }
            } else {
                razonDeshabilitacion = 'Configuración no válida para promoción escalable';
            }
        }

        // Aplicar el estado
        promocionEscalable.disabled = !habilitarEscalable;
        if (!habilitarEscalable) {
            promocionEscalable.checked = false;
        }

        console.log(`♾️ Promoción Escalable: ${habilitarEscalable ? 'HABILITADA' : 'DESHABILITADA'}`);
        console.log(`   📝 Razón: ${razonDeshabilitacion}`);
        console.log(`   📊 Estado actual:`, {
            tipoFiltro,
            productosCount: productosSeleccionados.length,
            tipoCondicion,
            tipoBeneficio: tipoBeneficioSelect?.options[tipoBeneficioSelect?.selectedIndex]?.textContent || 'No seleccionado'
        });
    }

    // === FUNCIONES AUXILIARES PARA LAS VALIDACIONES ===

    function verificarSoloCantidadMinima() {
        // Verificar que en la primera fila de intervalos de cantidad:
        // - Solo esté llena la cantidad mínima
        // - Los demás campos estén vacíos (cantidad máxima, descuento, productos bonificados)
        
        const primeraFila = document.querySelector('.rango-cantidad-item');
        if (!primeraFila) return false;
        
        // Verificar cantidad mínima llena
        const cantidadMinima = primeraFila.querySelector('.cantidad-min-input')?.value?.trim();
        if (!cantidadMinima) return false;
        
        // Verificar que cantidad máxima esté vacía
        const cantidadMaxima = primeraFila.querySelector('input[name="cantidad_max[]"]')?.value?.trim();
        if (cantidadMaxima) return false;
        
        // Verificar que descuento esté vacío
        const descuento = primeraFila.querySelector('.descuento-input')?.value?.trim();
        if (descuento) return false;
        
        // Verificar que no haya productos bonificados seleccionados
        const productoBonificado = primeraFila.querySelector('.producto-bonificado-select')?.value;
        if (productoBonificado) return false;
        
        // Verificar que no haya filas adicionales de rangos
        const todasLasFilas = document.querySelectorAll('.rango-cantidad-item');
        if (todasLasFilas.length > 1) return false;
        
        return true;
    }

    function verificarConfiguracionLineaMarca() {
        // Verificar que estén completos los campos de marca/línea
        const marca = marcaSelect?.value;
        const linea = lineaSelect?.value;
        const monto = montoMinimoProductos?.value;
        
        return !!(marca && linea && monto);
    }

    // === FUNCIÓN AUXILIAR PARA DEBUG ===
    function mostrarEstadoEscalabilidad() {
        // Función opcional para debugging - puedes llamarla desde la consola
        console.log('🔍 ESTADO ACTUAL PARA PROMOCIÓN ESCALABLE:');
        
        const tipoFiltro = document.querySelector('input[name="tipo_filtro"]:checked')?.value;
        const productosSeleccionados = Array.from(document.querySelectorAll('.productos-condicion-select'))
            .map(s => s.value).filter(val => val !== '');
        const tipoCondicion = tipoCondicionSelect?.value;
        const tipoBeneficio = tipoBeneficioSelect?.value;
        
        console.log('📊 Configuración actual:', {
            tipoFiltro,
            productosSeleccionados: productosSeleccionados.length,
            tipoCondicion,
            tipoBeneficio
        });
        
        if (tipoFiltro === 'productos_especificos') {
            console.log('🔍 Verificando Condición 1...');
            console.log('   ✓ Productos específicos: SÍ');
            console.log(`   ${productosSeleccionados.length === 1 ? '✓' : '❌'} Exactamente 1 producto: ${productosSeleccionados.length === 1 ? 'SÍ' : 'NO'}`);
            console.log(`   ${tipoCondicion === 'cantidad' ? '✓' : '❌'} Intervalos de Cantidad: ${tipoCondicion === 'cantidad' ? 'SÍ' : 'NO'}`);
            
            if (tipoCondicion === 'cantidad') {
                const soloMinima = verificarSoloCantidadMinima();
                console.log(`   ${soloMinima ? '✓' : '❌'} Solo cantidad mínima: ${soloMinima ? 'SÍ' : 'NO'}`);
            }
        } else if (tipoFiltro === 'linea_marca') {
            console.log('🔍 Verificando Condición 2...');
            console.log('   ✓ Marca/Línea completa: SÍ');
            
            const configCompleta = verificarConfiguracionLineaMarca();
            console.log(`   ${configCompleta ? '✓' : '❌'} Configuración completa: ${configCompleta ? 'SÍ' : 'NO'}`);
            
            const tipoBeneficioTexto = tipoBeneficioSelect?.options[tipoBeneficioSelect?.selectedIndex]?.textContent || 'No seleccionado';
            const esBonificacion = tipoBeneficioTexto.toLowerCase().includes('bonificación') && !tipoBeneficioTexto.toLowerCase().includes('ambos');
            console.log(`   ${esBonificacion ? '✓' : '❌'} Tipo beneficio "Bonificación": ${esBonificacion ? 'SÍ' : 'NO'} (actual: ${tipoBeneficioTexto})`);
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
        
        // Ocultar todas las configuraciones
        document.querySelectorAll('.configuracion-filtro').forEach(config => {
            config.classList.add('d-none');
        });

        // Resetear campos específicos según el tipo
        if (tipoSeleccionado === 'linea_marca') {
            const configLinea = document.getElementById('config-linea-marca');
            if (configLinea) configLinea.classList.remove('d-none');
            
            // Hacer campos obligatorios
            if (marcaSelect) marcaSelect.required = true;
            if (lineaSelect) lineaSelect.required = true;
            if (montoMinimoProductos) montoMinimoProductos.required = true;
            
        } else if (tipoSeleccionado === 'productos_especificos') {
            const configProductos = document.getElementById('config-productos-especificos');
            if (configProductos) configProductos.classList.remove('d-none');
            
            // Quitar obligatoriedad de campos de marca/línea
            if (marcaSelect) marcaSelect.required = false;
            if (lineaSelect) lineaSelect.required = false;
            if (montoMinimoProductos) montoMinimoProductos.required = false;
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
        
        const tipoBeneficio = tipoBeneficioSelect.options[tipoBeneficioSelect.selectedIndex]?.textContent.toLowerCase();
        
        ocultarTodosLosBeneficios();

        if (tipoBeneficio.includes('bonificación') && !tipoBeneficio.includes('ambos')) {
            const beneficioBonif = document.getElementById('beneficios-bonificacion');
            if (beneficioBonif) {
                beneficioBonif.classList.remove('d-none');
                actualizarSelectsBonificacion();
                // Hacer campos obligatorios
                const selects = beneficioBonif.querySelectorAll('.select-bonificacion');
                const inputs = beneficioBonif.querySelectorAll('input[name="cantidad_bonificada[]"]');
                selects.forEach(select => select.required = true);
                inputs.forEach(input => input.required = true);
            }
        } else if (tipoBeneficio.includes('descuento') && !tipoBeneficio.includes('ambos')) {
            const beneficioDesc = document.getElementById('beneficios-descuento');
            if (beneficioDesc) {
                beneficioDesc.classList.remove('d-none');
                const descuentoInput = document.getElementById('descuento_general');
                if (descuentoInput) descuentoInput.required = true;
            }
        } else if (tipoBeneficio.includes('ambos')) {
            const beneficioAmbos = document.getElementById('beneficios-ambos');
            if (beneficioAmbos) {
                beneficioAmbos.classList.remove('d-none');
                actualizarSelectsBonificacion();
                // Hacer campos obligatorios
                const selects = beneficioAmbos.querySelectorAll('.select-bonificacion-ambos');
                const inputs = beneficioAmbos.querySelectorAll('input[name="cantidad_bonificada_ambos[]"]');
                const descuentoInput = document.getElementById('descuento_ambos');
                selects.forEach(select => select.required = true);
                inputs.forEach(input => input.required = true);
                if (descuentoInput) descuentoInput.required = true;
            }
        }

        controlarPromocionEscalable();
    }

    function ocultarTodosLosBeneficios() {
        document.querySelectorAll('.beneficios-container').forEach(container => {
            container.classList.add('d-none');
        });
        // Quitar obligatoriedad
        document.querySelectorAll('#beneficios-bonificacion .select-bonificacion, #beneficios-bonificacion input[name="cantidad_bonificada[]"]').forEach(el => el.required = false);
        document.querySelectorAll('#beneficios-ambos .select-bonificacion-ambos, #beneficios-ambos input[name="cantidad_bonificada_ambos[]"]').forEach(el => el.required = false);
        const descuentoGeneral = document.getElementById('descuento_general');
        const descuentoAmbos = document.getElementById('descuento_ambos');
        if (descuentoGeneral) descuentoGeneral.required = false;
        if (descuentoAmbos) descuentoAmbos.required = false;
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
                controlarPromocionEscalable();
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

    // === RANGOS - FUNCIONES CORREGIDAS ===
    function configurarRangos() {
        // Delegación de eventos para tablas de rangos - CORREGIDA
        document.addEventListener('click', function(e) {
            // Prevenir múltiples ejecuciones
            if (e.target.disabled) return;
            
            // Rangos de cantidad
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
                agregarProductoBonificado(e.target);
            } else if (e.target.classList.contains('btn-quitar-producto-bonificado')) {
                e.preventDefault();
                e.stopPropagation();
                quitarProductoBonificado(e.target);
            }
            
            // Rangos de monto
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

        // Delegación de eventos para cambios en selects - CORREGIDA
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
                evaluarEstadoFormulario();
            } else if (e.target.classList.contains('descuento-input')) {
                controlarPromocionEscalable();
                evaluarEstadoFormulario();
            }else if (e.target.classList.contains('cantidad-min-input') || 
                 e.target.name === 'cantidad_max[]') {
                controlarPromocionEscalable();
                evaluarEstadoFormulario();
            }
        });

        document.addEventListener('input', function(e) {
            if (e.target.classList.contains('cantidad-min-input') || 
                e.target.name === 'cantidad_max[]' ||
                e.target.classList.contains('descuento-input')) {
                // Usar setTimeout para dar tiempo a que se actualice el valor
                setTimeout(() => {
                    controlarPromocionEscalable();
                }, 100);
            }
        });
    }

    function agregarRangoCantidad() {
        const tabla = document.getElementById('tabla-rangos-cantidad-body');
        if (!tabla) return;
        
        // Deshabilitar temporalmente el botón para evitar doble click
        const botonesAgregar = document.querySelectorAll('.btn-agregar-rango-cantidad');
        botonesAgregar.forEach(btn => btn.disabled = true);
        
        const template = tabla.querySelector('.rango-cantidad-item');
        const nuevo = template.cloneNode(true);
        
        // Limpiar valores del nuevo elemento
        nuevo.querySelectorAll('input').forEach(input => {
            input.value = '';
            // Solo la primera fila tiene data-required
            if (input.hasAttribute('data-required')) {
                input.removeAttribute('data-required');
            }
        });
        
        nuevo.querySelectorAll('select').forEach(select => {
            select.value = '';
        });
        
        // Limpiar productos bonificados adicionales (dejar solo el primero)
        const container = nuevo.querySelector('.productos-bonificados-container');
        const productosItems = container.querySelectorAll('.producto-bonificado-item');
        // Eliminar todos excepto el primero
        for (let i = 1; i < productosItems.length; i++) {
            productosItems[i].remove();
        }
        
        // Actualizar índices
        const nuevoIndice = contadorRangosCantidad++;
        nuevo.setAttribute('data-index', nuevoIndice);
        
        tabla.appendChild(nuevo);
        actualizarSelectsProductoBonificado();
        
        // Reactivar botones después de un pequeño delay
        setTimeout(() => {
            botonesAgregar.forEach(btn => btn.disabled = false);
            controlarPromocionEscalable();
        }, 300);
        
        console.log('✅ Nuevo rango de cantidad agregado');
    }

    function eliminarRangoCantidad(boton) {
        const tabla = document.getElementById('tabla-rangos-cantidad-body');
        if (!tabla) return;
        
        const filas = tabla.querySelectorAll('.rango-cantidad-item');
        
        if (filas.length > 1) {
            // Deshabilitar botón temporalmente
            boton.disabled = true;
            
            boton.closest('.rango-cantidad-item').remove();
            
            // Restaurar obligatoriedad de la primera fila si es necesario
            const primeraFila = tabla.querySelector('.rango-cantidad-item');
            if (primeraFila) {
                const cantidadMinInput = primeraFila.querySelector('.cantidad-min-input');
                if (cantidadMinInput) {
                    cantidadMinInput.setAttribute('data-required', 'true');
                }
            }
            
            controlarPromocionEscalable();
            evaluarEstadoFormulario();
            
            console.log('✅ Rango de cantidad eliminado');
        }
    }

    function agregarRangoMonto() {
        const tabla = document.getElementById('tabla-rangos-monto-body');
        if (!tabla) return;
        
        // Deshabilitar temporalmente el botón para evitar doble click
        const botonesAgregar = document.querySelectorAll('.btn-agregar-rango-monto');
        botonesAgregar.forEach(btn => btn.disabled = true);
        
        const template = tabla.querySelector('.rango-monto-item');
        const nuevo = template.cloneNode(true);
        
        // Limpiar valores del nuevo elemento
        nuevo.querySelectorAll('input').forEach(input => {
            input.value = '';
            // Solo la primera fila tiene data-required
            if (input.hasAttribute('data-required')) {
                input.removeAttribute('data-required');
            }
        });
        
        nuevo.querySelectorAll('select').forEach(select => {
            select.value = '';
        });
        
        // Limpiar productos bonificados adicionales (dejar solo el primero)
        const container = nuevo.querySelector('.productos-bonificados-container');
        const productosItems = container.querySelectorAll('.producto-bonificado-item');
        // Eliminar todos excepto el primero
        for (let i = 1; i < productosItems.length; i++) {
            productosItems[i].remove();
        }
        
        // Actualizar índices
        const nuevoIndice = contadorRangosMonto++;
        nuevo.setAttribute('data-index', nuevoIndice);
        
        tabla.appendChild(nuevo);
        actualizarSelectsProductoBonificado();
        
        // Reactivar botones después de un pequeño delay
        setTimeout(() => {
            botonesAgregar.forEach(btn => btn.disabled = false);
        }, 300);
        
        console.log('✅ Nuevo rango de monto agregado');
    }

    function eliminarRangoMonto(boton) {
        const tabla = document.getElementById('tabla-rangos-monto-body');
        if (!tabla) return;
        
        const filas = tabla.querySelectorAll('.rango-monto-item');
        
        if (filas.length > 1) {
            // Deshabilitar botón temporalmente
            boton.disabled = true;
            
            boton.closest('.rango-monto-item').remove();
            
            // Restaurar obligatoriedad de la primera fila si es necesario
            const primeraFila = tabla.querySelector('.rango-monto-item');
            if (primeraFila) {
                const montoMinInput = primeraFila.querySelector('.monto-min-input');
                if (montoMinInput) {
                    montoMinInput.setAttribute('data-required', 'true');
                }
            }
            
            evaluarEstadoFormulario();
            
            console.log('✅ Rango de monto eliminado');
        }
    }

    function agregarProductoBonificado(boton) {
        const fila = boton.closest('tr');
        const container = fila.querySelector('.productos-bonificados-container');
        
        // Deshabilitar botón temporalmente
        boton.disabled = true;
        
        const nuevoProductoDiv = document.createElement('div');
        nuevoProductoDiv.className = 'producto-bonificado-item mb-2';
        nuevoProductoDiv.innerHTML = `
            <div class="row">
                <div class="col-7">
                    <select name="producto_bonificado_cantidad[]" class="form-select producto-bonificado-select">
                        <option value="">Seleccione producto</option>
                    </select>
                </div>
                <div class="col-3">
                    <input type="number" name="cantidad_bonificada_cantidad[]" 
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
        
        // Mostrar botones de quitar para todos los productos bonificados
        actualizarBotonesQuitarProducto(container);
        
        // Reactivar botón después de un delay
        setTimeout(() => {
            boton.disabled = false;
        }, 300);
        
        console.log('✅ Producto bonificado agregado a la fila');
    }

    function quitarProductoBonificado(boton) {
        const fila = boton.closest('tr');
        const container = fila.querySelector('.productos-bonificados-container');
        const productosItems = container.querySelectorAll('.producto-bonificado-item');
        
        // Solo permitir eliminar si hay más de uno
        if (productosItems.length > 1) {
            boton.closest('.producto-bonificado-item').remove();
            
            // Actualizar botones de quitar
            actualizarBotonesQuitarProducto(container);
            
            controlarPromocionEscalable();
            evaluarEstadoFormulario();
            
            console.log('✅ Producto bonificado eliminado');
        }
    }

    function actualizarBotonesQuitarProducto(container) {
        const productosItems = container.querySelectorAll('.producto-bonificado-item');
        const botonesQuitar = container.querySelectorAll('.btn-quitar-producto-bonificado');
        
        botonesQuitar.forEach((btn, index) => {
            // Mostrar botón de quitar solo si hay más de un producto
            if (productosItems.length > 1) {
                btn.style.display = 'block';
            } else {
                btn.style.display = 'none';
            }
        });
    }

    // FUNCIÓN ACTUALIZADA para manejar productos bonificados
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
        
        // Actualizar botones de quitar después de actualizar selects
        document.querySelectorAll('.productos-bonificados-container').forEach(container => {
            actualizarBotonesQuitarProducto(container);
        });
    }

    // === BONIFICACIONES ===
    function configurarBonificaciones() {
        // Delegación de eventos para bonificaciones
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

    // === VALIDACIONES ===
    const formulario = document.getElementById('form-promocion');
    if (formulario) {
        formulario.addEventListener('submit', function(e) {
            console.log('📝 Enviando formulario...');
            if (!validarFormulario()) {
                e.preventDefault();
                return false;
            }
        });
    }

    function validarFormulario() {
        // Validar información básica
        if (!verificarInformacionBasica()) {
            alert('Por favor complete toda la información básica obligatoria');
            return false;
        }

        // Validar configuración de productos
        if (!verificarConfiguracionProductos()) {
            alert('Por favor complete la configuración de productos');
            return false;
        }

        // Validaciones específicas según tipo de filtro
        const tipoFiltro = document.querySelector('input[name="tipo_filtro"]:checked')?.value;
        
        if (tipoFiltro === 'linea_marca') {
            // Para marca/línea, verificar que tipo de beneficio esté seleccionado
            if (!tipoBeneficioSelect?.value) {
                alert('Por favor seleccione el tipo de beneficio');
                return false;
            }
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

    console.log('✅ jvPromos.js inicializado completamente');
});