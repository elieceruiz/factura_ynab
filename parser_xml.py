import xml.etree.ElementTree as ET

def leer_factura(xml_file):

    tree = ET.parse(xml_file)
    root = tree.getroot()

    # buscar la factura dentro del CDATA
    descripcion_node = root.find(".//{*}Description")

    if descripcion_node is None or descripcion_node.text is None:
        return []

    descripcion = descripcion_node.text.strip()

    # parsear la factura real
    invoice_root = ET.fromstring(descripcion)

    items = []

    for line in invoice_root.findall(".//{*}InvoiceLine"):

        producto = line.find(".//{*}Description")
        precio = line.find(".//{*}PriceAmount")
        cantidad = line.find(".//{*}InvoicedQuantity")

        items.append({
            "producto": producto.text.strip() if producto is not None else "UNKNOWN",
            "precio": float(precio.text) if precio is not None else 0,
            "cantidad": float(cantidad.text) if cantidad is not None else 1
        })

    return items
