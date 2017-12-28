
import xml.etree.ElementTree as ET

xml_dicc = {}
tree = ET.parse('ua1.xml')
root = tree.getroot()
for child in root:
    xml_dicc[str(child.tag)] = child.attrib
print(self.client_address)