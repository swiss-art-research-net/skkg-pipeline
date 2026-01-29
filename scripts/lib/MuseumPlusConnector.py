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

    def _addQueryAdditionToSearch(self, query: etree.Element, queryAddition: etree.Element) -> etree.Element:
        """
        Adds a query addition to the search element of the given query

        Args:
            query (etree.Element): The query to add the addition to
            queryAddition (etree.Element): The addition to add
        """
        queryExpert = query.find('.//expert')
        additionExpert = queryAddition.find('.//expert')
        if queryExpert is None and additionExpert is not None:
            query.find('.//search').append(additionExpert)
        elif queryExpert is not None and additionExpert is not None:
            existingChildren = list(queryExpert)
            newChildren = list(additionExpert)
            andElement = etree.SubElement(queryExpert, 'and')
            for child in existingChildren:
                queryExpert.remove(child)
                andElement.append(child)
            for child in newChildren:
                andElement.append(child)
        else:
            print("Query:")
            print(etree.tostring(query, pretty_print=True).decode())
            print("Query Addition:")
            print(etree.tostring(queryAddition, pretty_print=True).decode())
            raise ValueError("Could not add query addition to search query")
        return query
        
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

    def existsItem(self, *, module: str, uuid: str, queryAddition: etree.Element = None) -> bool:
        query = self._getItemQueryByUuid(module=module, uuid=uuid)
        search = query.find('.//search')
        select = etree.SubElement(search, 'select')
        field = etree.SubElement(select, 'field')
        field.set('fieldPath', '__uuid')
        url = self._getModuleSearchUrl(module)
        if queryAddition is not None:
            query = self._addQueryAdditionToSearch(query, queryAddition)
        response = self._post(url, query)
        if not response.content:
            return False
        tree = etree.fromstring(response.content)
        size = int(tree.find('.//{http://www.zetcom.com/ria/ws/module}module').get('totalSize'))
        return size > 0
    
    def getNumberOfItems(self, *, module: str, lastUpdated = None, queryAddition = None) -> int:
        """
        Returns the number of items in the module

        Args:
            module (str): The module name
            lastUpdated (str, optional): The date from which on the items should be counted. Defaults to None.       
            queryAddition (etree.Element, optional): Additional search query elements. Defaults to None.     
        """
        query = self._getAllItemsQuery(module=module, limit=1, offset=0, lastUpdated=lastUpdated)
        search = query.find('.//search')
        select = etree.SubElement(search, 'select')
        field = etree.SubElement(select, 'field')
        field.set('fieldPath', '__id')
        if queryAddition is not None:
            query = self._addQueryAdditionToSearch(query, queryAddition)
        url = self._getModuleSearchUrl(module)
        response = self._post(url, query)
        if not response.content:
            return 0
        tree = etree.fromstring(response.content)
        size = int(tree.find('.//{http://www.zetcom.com/ria/ws/module}module').get('totalSize'))
        return size
        
    def getItemByOffset(self, offset: int, *, module: str, lastUpdated = None, queryAddition = None) -> etree.Element:
        """
        Returns the item at the given offset

        Args:
            offset (int): The offset of the item
            module (str): The module name
            lastUpdated (str, optional): The date from which on the items should be counted. Defaults to None.
            queryAddition (etree.Element, optional): Additional search query elements. Defaults to None.
        """
        url = self._getModuleSearchUrl(module)
        query = self._getAllItemsQuery(module=module, limit=1, offset=offset, lastUpdated=lastUpdated)
        if queryAddition is not None:
            query = self._addQueryAdditionToSearch(query, queryAddition)
        try:
            response = self._post(url, query)
        except requests.exceptions.HTTPError as e:
            raise e
        item = etree.fromstring(response.content)
        return item
    
    def getItemByUuid(self, *, module: str, uuid: str, queryAddition: etree.Element = None) -> etree.Element:
        """
        Returns exactly one item matching the given UUID (or raises if not found).
        """
        url = self._getModuleSearchUrl(module)
        query = self._getItemQueryByUuid(module=module, uuid=uuid)

        if queryAddition is not None:
            query = self._addQueryAdditionToSearch(query, queryAddition)

        response = self._post(url, query)
        if not response.content:
            raise ValueError(f"No response content for uuid={uuid} in module={module}")

        item = etree.fromstring(response.content)

        # Verify totalSize if present
        mod = item.find('.//{http://www.zetcom.com/ria/ws/module}module')
        if mod is not None:
            total = int(mod.get("totalSize", "0"))
            if total < 1:
                raise ValueError(f"Item not found: uuid={uuid} in module={module}")

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
        content = response.content
        try:
            nodes = etree.fromstring(content)
        except etree.XMLSyntaxError as e:
            print("Error parsing XML response from MuseumPlus")
            raise e
        return nodes