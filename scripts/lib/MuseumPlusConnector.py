"""
Class for connecting to MuseumPlus via the REST API

Usage:
    client = MPWrapper(url=<url>, username=<username>, password=<password>)

Arguments:
    url: URL of the MuseumPlus instance
    username: Username to use for authentication
    password: Password to use for authentication
"""


import requests
from lxml import etree
from os.path import join

class MPWrapper:
    
    BASE_XML_SEARCH = """
       <application xmlns="http://www.zetcom.com/ria/ws/module/search" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.zetcom.com/ria/ws/module/search http://www.zetcom.com/ria/ws/module/search/search_1_1.xsd"></application>
    """
    
    
    def __init__(self, *, url: str, username: str, password: str):
        self.url = join(url, 'ria-ws/application')
        session = requests.Session()
        session.auth = (username, password)
        session.headers.update({
            "Content-Type": "application/xml",
            "Accept": "application/xml;charset=UTF-8",
            "Accept-Language": "de"
        })
        self.session = session
        
    def _get(self, url: str, *, params: dict = {}, timeout=300) -> requests.Request:
        """
        Sends a get request to the given URL

        Args:
            url (str): The URL to send the request to
            parameters (dict, optional): The parameters to send with the request. Defaults to None.
        """
        try:
            r = self.session.get(url, params=params, timeout=(None, timeout))
        except requests.exceptions.Timeout as e:
            raise e
        r.raise_for_status()
        return r
    
    def _post(self, url: str, query: etree.Element, *, timeout=300) -> requests.Request:
        """
        Sends a POST request to the given URL with the given query

        Args:
            url (str): The URL to send the request to
            query (etree.Element): The XML query to send
        """
        data = etree.tostring(query)
        try:
            r = self.session.post(url, data=data, timeout=(None, timeout))
        except requests.exceptions.Timeout as e:
            raise e
        r.raise_for_status()
        return r
    
    def _getAllItemsQuery(self, *, module: str, limit: int = False, offset: int = False, lastUpdated: str = None) -> etree.Element:
        """
        Returns the XML query for getting all items of a module

        Args:
            module (str): The module name
            limit (int, optional): The limit of items to return. Defaults to False.
            offset (int, optional): The offset of the items to return. Defaults to False.
            lastUpdated (str, optional): The date from which on the items should be counted. Defaults to None.
        """
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
    
    def _getItemQueryById(self, *, module: str, id: int) -> etree.Element:
        query = etree.fromstring(self.BASE_XML_SEARCH)
        modules = etree.SubElement(query, 'modules')
        requestedModule = etree.SubElement(modules, 'module')
        requestedModule.set('name', module)
        search = etree.SubElement(requestedModule, 'search')
        expert = etree.SubElement(search, 'expert')
        equalsField = etree.SubElement(expert, 'equalsField')
        equalsField.set('fieldPath', '__id')
        equalsField.set('operand', str(id))
        return query
    
    def _getItemQueryByUuid(self, *, module: str, uuid: str) -> etree.Element:
        query = etree.fromstring(self.BASE_XML_SEARCH)
        modules = etree.SubElement(query, 'modules')
        requestedModule = etree.SubElement(modules, 'module')
        requestedModule.set('name', module)
        search = etree.SubElement(requestedModule, 'search')
        expert = etree.SubElement(search, 'expert')
        equalsField = etree.SubElement(expert, 'equalsField')
        equalsField.set('fieldPath', '__uuid')
        equalsField.set('operand', uuid)
        return query

    def _getModuleSearchUrl(self, module: str) -> str:
        """
        Returns the search URL for the given module

        Args:
            module (str): The module name
        """
        return f"{self.url}/module/{module}/search"
    
    def _getVocabularySearchUrl(self, vocabulary: str) -> str:
        """
        Returns the search URL for the given vocabulary

        Args:
            vocabulary (str): The vocabulary name
        """
        return f"{self.url}/vocabulary/instances/{vocabulary}/nodes/search"

    def existsItem(self, *, module: str, uuid: str) -> bool:
        query = self._getItemQueryByUuid(module=module, uuid=uuid)
        search = query.find('.//search')
        select = etree.SubElement(search, 'select')
        field = etree.SubElement(select, 'field')
        field.set('fieldPath', '__uuid')
        url = self._getModuleSearchUrl(module)
        response = self._post(url, query)
        if not response.content:
            return False
        tree = etree.fromstring(response.content)
        size = int(tree.find('.//{http://www.zetcom.com/ria/ws/module}module').get('totalSize'))
        return size > 0
    
    def getNumberOfItems(self, *, module: str, lastUpdated = None) -> int:
        """
        Returns the number of items in the module

        Args:
            module (str): The module name
            lastUpdated (str, optional): The date from which on the items should be counted. Defaults to None.            
        """
        query = self._getAllItemsQuery(module=module, limit=1, offset=0, lastUpdated=lastUpdated)
        search = query.find('.//search')
        select = etree.SubElement(search, 'select')
        field = etree.SubElement(select, 'field')
        field.set('fieldPath', '__id')
        url = self._getModuleSearchUrl(module)
        response = self._post(url, query)
        if not response.content:
            return 0
        tree = etree.fromstring(response.content)
        size = int(tree.find('.//{http://www.zetcom.com/ria/ws/module}module').get('totalSize'))
        return size
        
    def getItemByOffset(self, offset: int, *, module: str, lastUpdated = None) -> etree.Element:
        """
        Returns the item at the given offset

        Args:
            offset (int): The offset of the item
            module (str): The module name
            lastUpdated (str, optional): The date from which on the items should be counted. Defaults to None.
        """
        url = self._getModuleSearchUrl(module)
        query = self._getAllItemsQuery(module=module, limit=1, offset=offset, lastUpdated=lastUpdated)
        try:
            response = self._post(url, query)
        except requests.exceptions.HTTPError as e:
            raise e
        item = etree.fromstring(response.content)
        return item
    
    def getVocabularyNodes(self, vocabulary: str) -> etree.Element:
        url = self._getVocabularySearchUrl(vocabulary)
        params = { 
            'limit': 100000,
            'status': ['valid']
        }
        try:
            response = self._get(url, params=params)
        except requests.exceptions.HTTPError as e:
            raise e
        nodes = etree.fromstring(response.content)
        return nodes