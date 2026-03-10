# parser_xml.py

import xml.etree.ElementTree as ET

def leer_factura(xml_file):

    # --------------------------------------
    # PARSEAR XML PRINCIPAL
    # --------------------------------------

    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError:
        return [], None, None


    # --------------------------------------
    # BUSCAR FACTURA DENTRO DEL CDATA
    # --------------------------------------

    descripcion_node = root.find(".//{*}Description")

    if descripcion_node is None or descripcion_node.text is None:
        return [], None, None

    descripcion = descripcion_node.text


    # --------------------------------------
    # LIMPIAR TEXTO DEL CDATA
    # --------------------------------------

    if descripcion:

        # quitar espacios basura
        descripcion = descripcion.strip()

        # buscar inicio real del XML
        inicio = descripcion.find("<?xml")

        if inicio != -1:
            descripcion = descripcion[inicio:]

        else:
            # si no aparece <?xml, buscar <Invoice directamente
            inicio = descripcion.find("<Invoice")

            if inicio != -1:
                descripcion = descripcion[inicio:]
            else:
                return [], None, None


    # --------------------------------------
    # PARSEAR LA FACTURA REAL
    # --------------------------------------

    try:
        invoice_root = ET.fromstring(descripcion)
    except ET.ParseError:
        return [], None, None


    # --------------------------------------
    # VERIFICAR QUE SEA FACTURA DIAN
    # --------------------------------------

    if invoice_root.find(".//{*}InvoiceLine") is None:
        return [], None, None


    # --------------------------------------
    # OBTENER FECHA DE FACTURA
    # --------------------------------------

    fecha_node = invoice_root.find(".//{*}IssueDate")
    fecha = fecha_node.text if fecha_node is not None else None


    # --------------------------------------
    # OBTENER PROVEEDOR (PAYEE)
    # --------------------------------------

    supplier_node = invoice_root.find(".//{*}AccountingSupplierParty//{*}Name")

    if supplier_node is None:
        supplier_node = invoice_root.find(".//{*}RegistrationName")

    proveedor = supplier_node.text.strip() if supplier_node is not None else "Proveedor desconocido"


    # --------------------------------------
    # EXTRAER ITEMS DE LA FACTURA
    # --------------------------------------

    items = []

    for line in invoice_root.findall(".//{*}InvoiceLine"):

        producto = line.find(".//{*}Description")
        precio = line.find(".//{*}PriceAmount")
        cantidad = line.find(".//{*}InvoicedQuantity")

        nombre_producto = producto.text.strip() if producto is not None else "UNKNOWN"

        try:
            precio_valor = float(precio.text)
        except:
            precio_valor = 0

        try:
            cantidad_valor = float(cantidad.text)
        except:
            cantidad_valor = 1

        items.append({
            "producto": nombre_producto,
            "precio": precio_valor,
            "cantidad": cantidad_valor
        })


    # --------------------------------------
    # RESULTADO FINAL
    # --------------------------------------

    return items, fecha, proveedor
