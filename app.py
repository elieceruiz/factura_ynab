# app.py

# Importamos Streamlit para construir la interfaz
import streamlit as st

# Función que parsea el XML y extrae items, fecha y proveedor
from parser_xml import leer_factura

# Funciones para interactuar con la API de YNAB
from ynab_api import traer_categorias, crear_transaccion

# Conexión a MongoDB donde guardamos la memoria de categorías por producto
from db import productos


# ID de la cuenta de YNAB donde se registrarán los gastos
ACCOUNT_ID = st.secrets["ACCOUNT_ID"]


# ---------------------------------------------------
# BLOQUE DE ESTILOS (SOLO FRONTEND / SOLO VISUAL)
# ---------------------------------------------------
# Este CSS no afecta backend, Mongo ni YNAB.
# Solo cambia cómo se ve la interfaz.

st.markdown("""
<style>

.card {
    background-color: #ffffff;   /* fondo blanco */
    border-radius: 14px;         /* bordes redondeados */
    border: 1px solid #eeeeee;   /* borde suave */
    padding: 18px;               /* espacio interno */
    margin-bottom: 12px;         /* separación entre tarjetas */
}

.product {
    font-size: 16px;
    font-weight: 600;            /* texto seminegrita */
}

.price {
    font-size: 20px;
    font-weight: 700;
    color: #ff4b4b;              /* rojo tipo fintech para gastos */
}

.meta {
    color: #666;
    font-size: 13px;
}

</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------
# TÍTULO DE LA APP
# ---------------------------------------------------

st.title("Factura → YNAB")


# ---------------------------------------------------
# SUBIDA DE ARCHIVO XML
# ---------------------------------------------------
# Aquí el usuario sube la factura electrónica

archivo = st.file_uploader("Sube factura XML")


# ---------------------------------------------------
# SOLO SE EJECUTA SI HAY ARCHIVO
# ---------------------------------------------------

if archivo:

    # Leemos el XML y obtenemos:
    # items (productos)
    # fecha de factura
    # proveedor
    items, fecha, proveedor = leer_factura(archivo)


    # ---------------------------------------------------
    # INFORMACIÓN DE LA FACTURA
    # ---------------------------------------------------

    # Creamos dos columnas para mostrar proveedor y fecha
    colA, colB = st.columns(2)

    with colA:
        st.markdown(f"**Proveedor**  \n{proveedor}")

    with colB:
        st.markdown(f"**Fecha factura**  \n{fecha}")


    # ---------------------------------------------------
    # TOTAL DE LA FACTURA
    # ---------------------------------------------------

    # Sumamos todos los precios detectados
    total = sum(i["precio"] for i in items)

    # Mostramos el total como métrica financiera
    st.metric("Total factura", f"${total:,.0f}")


    # ---------------------------------------------------
    # TRAER CATEGORÍAS DESDE YNAB
    # ---------------------------------------------------

    categorias = traer_categorias()

    # Convertimos la lista en diccionario
    # nombre_categoria → id_categoria
    mapa_cat = {c["nombre"]: c["id"] for c in categorias}

    # Lista de nombres para el dropdown
    nombres_cat = list(mapa_cat.keys())


    # ---------------------------------------------------
    # LISTA DE ITEMS DE LA FACTURA
    # ---------------------------------------------------

    st.subheader("Gastos detectados")


    # Lista donde guardaremos lo que el usuario selecciona
    seleccion = []


    # ---------------------------------------------------
    # RECORRER CADA PRODUCTO DE LA FACTURA
    # ---------------------------------------------------

    for i in items:

        producto = i["producto"]
        precio = i["precio"]


        # ---------------------------------------------------
        # MEMORIA DE CATEGORÍAS (MongoDB)
        # ---------------------------------------------------

        # Buscamos si ya clasificamos este producto antes
        memoria = productos.find_one({"producto": producto})

        if memoria:
            categoria_default = memoria["categoria"]
        else:
            categoria_default = nombres_cat[0]


        # ---------------------------------------------------
        # TARJETA VISUAL DEL PRODUCTO
        # ---------------------------------------------------

        # Abrimos una tarjeta con bordes redondeados
        st.markdown("<div class='card'>", unsafe_allow_html=True)


        # Creamos dos columnas:
        # izquierda = producto + categoría
        # derecha = precio
        col1, col2 = st.columns([5,1])


        # ---------------------------------------------------
        # COLUMNA IZQUIERDA
        # ---------------------------------------------------

        with col1:

            # Nombre del producto
            st.markdown(
                f"<div class='product'>{producto}</div>",
                unsafe_allow_html=True
            )

            # Dropdown para seleccionar categoría
            categoria = st.selectbox(
                "Categoría",
                nombres_cat,
                index=nombres_cat.index(categoria_default)
                if categoria_default in nombres_cat else 0,
                key=producto
            )


        # ---------------------------------------------------
        # COLUMNA DERECHA
        # ---------------------------------------------------

        with col2:

            # Precio mostrado en rojo y con signo negativo
            st.markdown(
                f"<div class='price'>-${precio:,.0f}</div>",
                unsafe_allow_html=True
            )


        # Cerramos la tarjeta visual
        st.markdown("</div>", unsafe_allow_html=True)


        # Guardamos la selección del usuario
        seleccion.append({
            "producto": producto,
            "precio": precio,
            "categoria": categoria,
            "categoria_id": mapa_cat[categoria]
        })


    # ---------------------------------------------------
    # BOTÓN DE ENVÍO A YNAB
    # ---------------------------------------------------

    if st.button("🚀 Enviar factura a YNAB", use_container_width=True):

        for s in seleccion:

            # Crear transacción en YNAB
            crear_transaccion(
                ACCOUNT_ID,
                s["categoria_id"],
                proveedor,
                s["precio"],
                fecha,
                s["producto"]
            )


            # Guardar memoria en MongoDB
            productos.update_one(
                {"producto": s["producto"]},
                {"$set": {
                    "categoria": s["categoria"],
                    "categoria_id": s["categoria_id"]
                }},
                upsert=True
            )

        # Confirmación visual
        st.success("Factura enviada a YNAB")
