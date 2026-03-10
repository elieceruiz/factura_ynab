import xml.etree.ElementTree as ET

NS = {
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
}

def leer_factura(xml_file):

    tree = ET.parse(xml_file)
    root = tree.getroot()

    items = []

    for line in root.findall(".//cac:InvoiceLine", NS):

        desc = line.find(".//cbc:Description", NS)
        price = line.find(".//cbc:LineExtensionAmount", NS)

        if desc is None or price is None:
            continue

        items.append({
            "producto": desc.text.strip(),
            "precio": float(price.text)
        })

    return items
