import requests
from lxml import etree
from os.path import join

class MPWrapper:
    
    BASE_XML_SEARCH = """
       <application xmlns="http://www.zetcom.com/ria/ws/module/search" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.zetcom.com/ria/ws/module/search http://www.zetcom.com/ria/ws/module/search/search_1_1.xsd"></application>
    """
    
    
    def __init__(self, *, url, username, password):
        self.url = join(url, 'ria-ws/application')
        session = requests.Session()
        session.auth = (username, password)
        session.headers.update({
            "Content-Type": "application/xml",
            "Accept": "application/xml;charset=UTF-8",
            "Accept-Language": "de"
        })
        self.session = session
        
    def _post(self, url, query) -> requests.Request:
        data = etree.tostring(query)
        r = self.session.post(url, data=data)
        r.raise_for_status()
        return r
    
    def _getAllItemsQuery(self, *, module: str, limit: int = False, offset: int = False, lastUpdated: str = None):
        query = etree.fromstring(self.BASE_XML_SEARCH)
        modules = etree.SubElement(query, 'modules')
        requestedModule = etree.SubElement(modules, 'module')
        requestedModule.set('name', module)
        search = etree.SubElement(requestedModule, 'search')
        if limit:
            search.set('limit', str(limit))
        if offset:
            search.set('offset', str(offset))
        if lastUpdated:
            expert = etree.SubElement(search, 'expert')
            betweenIncl = etree.SubElement(expert, 'betweenIncl')
            betweenIncl.set('fieldPath', '__lastModified')
            betweenIncl.set('operand1', lastUpdated)
            betweenIncl.set('operand2', '2100-01-01T00:00:00Z')
        fulltext = etree.SubElement(search, 'fulltext')
        fulltext.text = "*"
        return query
    
    def _getModuleSearchUrl(self, module):
        return f"{self.url}/module/{module}/search"
    
    def getNumberOfItems(self, *, module, lastUpdated = None):
        query = self._getAllItemsQuery(module=module, limit=1, offset=0, lastUpdated=lastUpdated)
        url = self._getModuleSearchUrl(module)
        response = self._post(url, query)
        tree = etree.fromstring(response.content)
        size = int(tree.find('.//{http://www.zetcom.com/ria/ws/module}module').get('totalSize'))
        return size
        
    def getItemByOffset(self, offset, *, module, lastUpdated = None):
        url = self._getModuleSearchUrl(module)
        query = self._getAllItemsQuery(module=module, limit=1, offset=offset, lastUpdated=lastUpdated)
        response = self._post(url, query)
        item = etree.fromstring(response.content)
        return item