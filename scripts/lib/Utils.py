from lxml import etree

def createXMLCopy(element):
    if element is None:
        return None
    return etree.fromstring(etree.tostring(element))        