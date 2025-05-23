document.addEventListener('DOMContentLoaded', function () {
    const empresaSelect = document.getElementById('id_empresa');
    const sucursalSelect = document.getElementById('id_sucursal');
    const productosCondicionContainer = document.getElementById('productos-condicion-container');
    const tipoBeneficioSelect = document.getElementById('id_tipo_beneficio');
    const cardBonificaciones = document.getElementById('card-bonificaciones');
    const bonificacionesContainer = document.getElementById('bonificaciones-container');
    const cardDescuento = document.getElementById('card-descuento');
    const tipoCondicionSelect = document.getElementById('id_tipo_condicion');
    const cardCondicionPrecios = document.getElementById('card-condicion-precios');
    const rangosPrecioContainer = document.getElementById('rangos-precio-container');
    const inputFechaInicio = document.getElementById('id_fecha_inicio');
    const inputFechaFin = document.getElementById('id_fecha_fin');
    const cardCondicionCantidad = document.getElementById('card-condicion-cantidad');
    const contenedorCondicionCantidad = document.getElementById('condicion-cantidad-container');



    let articulosDisponibles = [];
    let articulosBonificables = [];

    // Obtener la fecha actual en formato YYYY-MM-DD
    const hoy = new Date().toISOString().split('T')[0];

    if (tipoCondicionSelect) {
        tipoCondicionSelect.addEventListener('change', function () {
            const valor = this.value.toLowerCase();

            if (valor === 'cantidad') {
                cardCondicionCantidad.classList.remove('d-none');
                actualizarCondicionCantidad();
            } else {
                cardCondicionCantidad.classList.add('d-none');
                contenedorCondicionCantidad.innerHTML = ''; // limpiar
            }

            if (valor === 'monto' || valor === 'precios') {
                cardCondicionPrecios.classList.remove('d-none');
                actualizarRangosPrecio();
            } else {
                cardCondicionPrecios.classList.add('d-none');
            }
        });
    }

    const bloqueConfigCantidad = document.getElementById('bloque-configuracion-producto');

    if (bloqueConfigCantidad) {
        bloqueConfigCantidad.addEventListener('click', function (e) {
            if (e.target.classList.contains('btn-agregar-config')) {
                const fila = e.target.closest('.configuracion-cantidad-item');
                const nuevo = fila.cloneNode(true);

                // Limpiar los valores de los inputs
                nuevo.querySelectorAll('input').forEach(input => input.value = '');
                nuevo.querySelectorAll('select').forEach(select => select.value = '');

                bloqueConfigCantidad.appendChild(nuevo);
                actualizarConfiguracionCantidad();
            }

            if (e.target.classList.contains('btn-eliminar-config')) {
                const filas = bloqueConfigCantidad.querySelectorAll('.configuracion-cantidad-item');
                if (filas.length > 1) {
                    e.target.closest('.configuracion-cantidad-item').remove();
                    actualizarConfiguracionCantidad();
                }
            }
        });

        function actualizarConfiguracionCantidad() {
            const filas = bloqueConfigCantidad.querySelectorAll('.configuracion-cantidad-item');
            filas.forEach(fila => {
                const btnEliminar = fila.querySelector('.btn-eliminar-config');
                if (filas.length === 1) {
                    btnEliminar.disabled = true;
                    btnEliminar.title = 'Debe haber al menos una configuración';
                } else {
                    btnEliminar.disabled = false;
                    btnEliminar.title = 'Eliminar configuración';
                }
            });
        }

        actualizarConfiguracionCantidad(); // Ejecutar al cargar
    }


    function actualizarCondicionCantidad() {
        const productos = productosCondicionContainer.querySelectorAll('.productos-condicion-select');
        contenedorCondicionCantidad.innerHTML = '';

        productos.forEach((select, index) => {
            const productoId = select.value;
            const productoTexto = select.options[select.selectedIndex]?.textContent || 'Producto sin nombre';

            if (productoId) {
                const bloque = document.createElement('div');
                bloque.className = 'border rounded p-3 mb-3 bg-light';

                bloque.innerHTML = `
                    <strong>${productoTexto}</strong>
                    <div class="row mt-2">
                        <div class="col-md-3">
                            <label>Cantidad Mínima</label>
                            <input type="number" name="productos_configurados[${productoId}][cantidad_min][]" class="form-control" min="0">
                        </div>
                        <div class="col-md-3">
                            <label>Cantidad Máxima</label>
                            <input type="number" name="productos_configurados[${productoId}][cantidad_max][]" class="form-control" min="0">
                        </div>
                        <div class="col-md-3">
                            <label>Tipo de Selección</label>
                            <select name="productos_configurados[${productoId}][tipo_seleccion]" class="form-select">
                                <option value="">--</option>
                                <option value="producto">Producto Gratis</option>
                                <option value="porcentaje">Porcentaje Descuento</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label>Valor (Cantidad o %)</label>
                            <input type="number" name="productos_configurados[${productoId}][valor][]" class="form-control" min="0" step="0.01">
                        </div>
                    </div>
                `;
                contenedorCondicionCantidad.appendChild(bloque);
            }
        });
    }




    // Establecer la fecha mínima para "fecha inicio"
    if (inputFechaInicio) {
        inputFechaInicio.setAttribute('min', hoy);
    }

    // Establecer dinámicamente la fecha mínima para "fecha fin"
    if (inputFechaFin && inputFechaInicio) {
        inputFechaInicio.addEventListener('change', function () {
            const fechaSeleccionada = this.value;
            inputFechaFin.value = ''; // limpiar si ya había una
            inputFechaFin.setAttribute('min', fechaSeleccionada);
        });
    }

    // Cargar sucursales según empresa
    if (empresaSelect && sucursalSelect) {
        sucursalSelect.disabled = true;
        empresaSelect.addEventListener('change', function () {
            fetch(`/core/api/sucursales/?empresa_id=${this.value}`)
                .then(res => res.json())
                .then(data => {
                    sucursalSelect.disabled = false;
                    sucursalSelect.innerHTML = '<option value="">---------</option>';
                    data.forEach(sucursal => {
                        const option = document.createElement('option');
                        option.value = sucursal.sucursal_id;
                        option.textContent = sucursal.nombre;
                        sucursalSelect.appendChild(option);
                    });
                });
        });
    }

    // Cargar artículos al cambiar sucursal
    sucursalSelect.addEventListener('change', function () {
        const sucursalId = this.value;

        fetch(`/core/api/articulos_por_sucursal/?sucursal_id=${sucursalId}`)
            .then(res => res.json())
            .then(data => {
                articulosDisponibles = data;
                articulosBonificables = data;
                actualizarTodosLosSelects();
                actualizarBonificaciones();
            });
    });

    // Agregar/eliminar productos condicionales
    productosCondicionContainer.addEventListener('click', function (e) {
        if (e.target.classList.contains('btn-agregar-producto')) {
            const template = productosCondicionContainer.querySelector('.producto-condicion');
            const nuevo = template.cloneNode(true);
            nuevo.querySelector('.productos-condicion-select').value = "";
            productosCondicionContainer.appendChild(nuevo);
            actualizarTodosLosSelects();
        }

        if (e.target.classList.contains('btn-eliminar-producto')) {
            const fila = e.target.closest('.producto-condicion');
            if (fila) {
                fila.remove();
                actualizarTodosLosSelects();
            }
        }
    });

    productosCondicionContainer.addEventListener('change', function (e) {
        if (e.target.classList.contains('productos-condicion-select')) {
            actualizarTodosLosSelects();
            if (tipoCondicionSelect.value.toLowerCase() === 'cantidad') {
                actualizarCondicionCantidad();
            }
    }
    });

    function actualizarTodosLosSelects() {
        const selects = productosCondicionContainer.querySelectorAll('.productos-condicion-select');
        const seleccionados = Array.from(selects).map(s => s.value).filter(val => val !== '');

        selects.forEach(select => {
            const actual = select.value;
            select.innerHTML = '<option value="">Seleccione un producto</option>';
            articulosDisponibles.forEach(art => {
                if (!seleccionados.includes(art.articulo_id) || art.articulo_id === actual) {
                    const option = document.createElement('option');
                    option.value = art.articulo_id;
                    option.textContent = `${art.codigo} - ${art.descripcion}`;
                    if (art.articulo_id === actual) {
                        option.selected = true;
                    }
                    select.appendChild(option);
                }
            });
        });

        // Desactivar "+" si ya no hay productos disponibles
        const botonesAgregar = productosCondicionContainer.querySelectorAll('.btn-agregar-producto');
        const usados = seleccionados.length;
        const max = articulosDisponibles.length;
        const desactivar = usados >= max;

        botonesAgregar.forEach(btn => {
            btn.disabled = desactivar;
            btn.title = desactivar ? 'No hay más productos disponibles' : '';
        });

        // Desactivar "X" si solo hay uno
        const filas = productosCondicionContainer.querySelectorAll('.producto-condicion');
        filas.forEach(fila => {
            const btnEliminar = fila.querySelector('.btn-eliminar-producto');
            if (filas.length === 1) {
                btnEliminar.disabled = true;
                btnEliminar.title = 'Debe haber al menos un producto';
            } else {
                btnEliminar.disabled = false;
                btnEliminar.title = 'Eliminar producto';
            }
        });
    }

    // Mostrar card bonificaciones si se elige ese tipo
    if (tipoBeneficioSelect) {
        tipoBeneficioSelect.addEventListener('change', function () { 
            const seleccionado = this.options[this.selectedIndex].text.toLowerCase();

            if (seleccionado.includes('bonificación') && !seleccionado.includes('ambos')) {
                // Solo bonificación
                cardBonificaciones.classList.remove('d-none');
                cardDescuento.classList.add('d-none');
                actualizarBonificaciones();
            } else if (seleccionado.includes('descuento') && !seleccionado.includes('ambos')) {
                // Solo descuento
                cardDescuento.classList.remove('d-none');
                cardBonificaciones.classList.add('d-none');
            } else if (seleccionado.includes('ambos')) {
                // Mostrar ambos
                cardBonificaciones.classList.remove('d-none');
                cardDescuento.classList.remove('d-none');
                actualizarBonificaciones();
            } else {
                // Ocultar todo si no se selecciona nada
                cardBonificaciones.classList.add('d-none');
                cardDescuento.classList.add('d-none');
            }
        });
    }


    // Agregar/eliminar productos bonificados
    bonificacionesContainer.addEventListener('click', function (e) {
        if (e.target.classList.contains('btn-agregar-bonificacion')) {
            const fila = e.target.closest('.bonificacion-item');
            const nuevo = fila.cloneNode(true);
            nuevo.querySelector('.select-bonificacion').value = "";
            nuevo.querySelector('.input-cantidad-bonificada').value = "";
            bonificacionesContainer.appendChild(nuevo);
            actualizarBonificaciones();
        }

        if (e.target.classList.contains('btn-eliminar-bonificacion')) {
            const fila = e.target.closest('.bonificacion-item');
            if (fila) {
                fila.remove();
                actualizarBonificaciones();
            }
        }
    });

    bonificacionesContainer.addEventListener('change', function (e) {
        if (e.target.classList.contains('select-bonificacion')) {
            actualizarBonificaciones();
        }
    });

    function actualizarBonificaciones() {
        const selects = bonificacionesContainer.querySelectorAll('.select-bonificacion');
        const seleccionados = Array.from(selects).map(s => s.value).filter(val => val !== '');

        selects.forEach(select => {
            const actual = select.value;
            select.innerHTML = '<option value="">Seleccione un producto</option>';
            articulosBonificables.forEach(art => {
                if (!seleccionados.includes(art.articulo_id) || art.articulo_id === actual) {
                    const option = document.createElement('option');
                    option.value = art.articulo_id;
                    option.textContent = `${art.codigo} - ${art.descripcion}`;
                    if (art.articulo_id === actual) {
                        option.selected = true;
                    }
                    select.appendChild(option);
                }
            });
        });

        // Desactivar "+" si ya no hay productos disponibles
        const botonesAgregar = bonificacionesContainer.querySelectorAll('.btn-agregar-bonificacion');
        const usados = seleccionados.length;
        const max = articulosBonificables.length;
        const desactivar = usados >= max;

        botonesAgregar.forEach(btn => {
            btn.disabled = desactivar;
            btn.title = desactivar ? 'No hay más productos disponibles' : '';
        });

        // Desactivar "X" si solo hay uno
        const filas = bonificacionesContainer.querySelectorAll('.bonificacion-item');
        filas.forEach(fila => {
            const btnEliminar = fila.querySelector('.btn-eliminar-bonificacion');
            if (filas.length === 1) {
                btnEliminar.disabled = true;
                btnEliminar.title = 'Debe haber al menos un producto';
            } else {
                btnEliminar.disabled = false;
                btnEliminar.title = 'Eliminar bonificación';
            }
        });
    }

    if (tipoCondicionSelect) {
        tipoCondicionSelect.addEventListener('change', function () {
            const valor = this.value.toLowerCase();
            if (valor === 'monto') {
                cardCondicionPrecios.classList.remove('d-none');
                actualizarRangosPrecio();
            } else {
                cardCondicionPrecios.classList.add('d-none');
            }
        });
    }

    rangosPrecioContainer.addEventListener('click', function (e) {
        if (e.target.classList.contains('btn-agregar-rango')) {
            const fila = e.target.closest('.rango-precio-item');
            const nuevo = fila.cloneNode(true);

            nuevo.querySelector('.input-minimo').value = '';
            nuevo.querySelector('.input-maximo').value = '';
            nuevo.querySelector('.input-porcentaje').value = '';

            rangosPrecioContainer.appendChild(nuevo);
            actualizarRangosPrecio();
        }

        if (e.target.classList.contains('btn-eliminar-rango')) {
            const filas = rangosPrecioContainer.querySelectorAll('.rango-precio-item');
            if (filas.length > 1) {
                e.target.closest('.rango-precio-item').remove();
                actualizarRangosPrecio();
            }
        }
    });

    function actualizarRangosPrecio() {
        const filas = rangosPrecioContainer.querySelectorAll('.rango-precio-item');
        filas.forEach(fila => {
            const btnEliminar = fila.querySelector('.btn-eliminar-rango');
            if (filas.length === 1) {
                btnEliminar.disabled = true;
                btnEliminar.title = 'Debe haber al menos un rango';
            } else {
                btnEliminar.disabled = false;
                btnEliminar.title = 'Eliminar rango';
            }
        });
    }

    const selectProductoCantidad = document.getElementById('select-producto-cantidad');
    const bloqueConfiguracion = document.getElementById('bloque-configuracion-producto');


    function actualizarSelectorProductoCantidad() {
        if (!selectProductoCantidad) return;

        selectProductoCantidad.innerHTML = '<option value="">Seleccione un producto</option>';

        const productos = productosCondicionContainer.querySelectorAll('.productos-condicion-select');
        productos.forEach(select => {
            const val = select.value;
            const text = select.options[select.selectedIndex]?.textContent;
            if (val) {
                const option = document.createElement('option');
                option.value = val;
                option.textContent = text;
                selectProductoCantidad.appendChild(option);
            }
        });
    }

    if (selectProductoCantidad) {
        selectProductoCantidad.addEventListener('change', function () {
            const productoId = this.value;
            bloqueConfiguracion.innerHTML = '';

            if (productoId) {
                bloqueConfiguracion.classList.remove('d-none');

                bloqueConfiguracion.innerHTML = `
                    <div class="row mb-3">
                        <div class="col-md-4">
                            <label>Tipo de Selección</label>
                            <select class="form-select" name="productos_configurados[${productoId}][tipo_seleccion]">
                                <option value="">--</option>
                                <option value="producto">Producto Gratis</option>
                                <option value="porcentaje">Porcentaje Descuento</option>
                            </select>
                        </div>
                    </div>

                    <div class="configuracion-cantidad-item row mb-2">
                        <div class="col-md-3">
                            <label>Cantidad Mínima</label>
                            <input type="number" name="productos_configurados[${productoId}][cantidad_min][]" class="form-control">
                        </div>
                        <div class="col-md-3">
                            <label>Cantidad Máxima</label>
                            <input type="number" name="productos_configurados[${productoId}][cantidad_max][]" class="form-control">
                        </div>
                        <div class="col-md-4">
                            <label>Se Bonifica (Cantidad o %)</label>
                            <input type="number" name="productos_configurados[${productoId}][valor][]" class="form-control">
                        </div>
                        <div class="col-md-2 d-flex align-items-end gap-2">
                            <button type="button" class="btn btn-success btn-agregar-config">+</button>
                            <button type="button" class="btn btn-danger btn-eliminar-config">X</button>
                        </div>
                    </div>
                `;
            } else {
                bloqueConfiguracion.classList.add('d-none');
            }
        });

    }


    productosCondicionContainer.addEventListener('change', function (e) {
        if (e.target.classList.contains('productos-condicion-select')) {
            actualizarTodosLosSelects();
            actualizarSelectorProductoCantidad();
        }
    });


    actualizarSelectorProductoCantidad();

    

});
