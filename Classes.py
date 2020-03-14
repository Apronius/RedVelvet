class Document:

    def __init__(self, responsePages):

        if(not isinstance(responsePages, list)):
            rps = []
            rps.append(responsePages)
            responsePages = rps

        self._responsePages = responsePages
        self._pages = []

        self._parse()

    def __str__(self):
        s = "\nDocument\n==========\n"
        for p in self._pages:
            s = s + str(p) + "\n\n"
        return s

    def _parseDocumentPagesAndBlockMap(self):

        blockMap = {}

        documentPages = []
        documentPage = None
        for page in self._responsePages:
            for block in page['Blocks']:
                if('BlockType' in block and 'Id' in block):
                    blockMap[block['Id']] = block

                if(block['BlockType'] == 'PAGE'):
                    if(documentPage):
                        documentPages.append({"Blocks" : documentPage})
                    documentPage = []
                    documentPage.append(block)
                else:
                    documentPage.append(block)
        if(documentPage):
            documentPages.append({"Blocks" : documentPage})
        return documentPages, blockMap

    def _parse(self):

        self._responseDocumentPages, self._blockMap = self._parseDocumentPagesAndBlockMap()
        for documentPage in self._responseDocumentPages:
            page = Page(documentPage["Blocks"], self._blockMap)
            self._pages.append(page)

    @property
    def blocks(self):
        return self._responsePages

    @property
    def pageBlocks(self):
        return self._responseDocumentPages

    @property
    def pages(self):
        return self._pages

    def getBlockById(self, blockId):
        block = None
        if(self._blockMap and blockId in self._blockMap):
            block = self._blockMap[blockId]
        return block