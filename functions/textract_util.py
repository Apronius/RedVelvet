import os
import time
from xml.dom import minidom
from xml.etree import ElementTree
from collections import defaultdict
from collections import OrderedDict 
from xml.etree.ElementTree import Element, SubElement, Comment, tostring

#Function to group all block elements from textract response by type
def groupBlocksByType(responseBlocks):
    blocks = {}

    for block in responseBlocks:
        blocktype = block['BlockType']
        if blocktype not in blocks.keys():
            blocks[blocktype] = [block]
        else:
            blocks[blocktype].append(block)
    print("Extracted Block Types:")
    for blocktype in blocks.keys():
        print("                       {} = {}".format(blocktype, len(blocks[blocktype])))
    return blocks

#Function to retrieve result of completed analysis job
def GetTextDetectionResult(textract, jobId):
    maxResults = int(os.environ['max_results']) #1000
    paginationToken = None
    finished = False 
    retryInterval = int(os.environ['retry_interval']) #30
    maxRetryAttempt = int(os.environ['max_retry_attempt']) #5

    result = []

    while finished == False:
        retryCount = 0

        try:
            if paginationToken is None:
                response = textract.get_document_text_detection(JobId=jobId,
                                            MaxResults=maxResults)  
            else:
                response = textract.get_document_text_detection(JobId=jobId,
                                                MaxResults=maxResults,
                                                NextToken=paginationToken)
        except Exception as e:
            exceptionType = str(type(e))
            if exceptionType.find("AccessDeniedException") > 0:
                finished = True
                print("You aren't authorized to perform textract.analyze_document action.")    
            elif exceptionType.find("InvalidJobIdException") > 0:
                finished = True
                print("An invalid job identifier was passed.")   
            elif exceptionType.find("InvalidParameterException") > 0:
                finished = True
                print("An input parameter violated a constraint.")        
            else:
                if retryCount < maxRetryAttempt:
                    retryCount = retryCount + 1
                else:
                    print(e)
                    print("Result retrieval failed, after {} retry, aborting".format(maxRetryAttempt))                       
                if exceptionType.find("InternalServerError") > 0:
                    print("Amazon Textract experienced a service issue. Trying in {} seconds.".format(retryInterval))   
                    time.sleep(retryInterval)
                elif exceptionType.find("ProvisionedThroughputExceededException") > 0:
                    print("The number of requests exceeded your throughput limit. Trying in {} seconds.".format(retryInterval*3))
                    time.sleep(retryInterval*3)
                elif exceptionType.find("ThrottlingException") > 0:
                    print("Amazon Textract is temporarily unable to process the request. Trying in {} seconds.".format(retryInterval*6))

        #Get the text blocks
        blocks=[]
        if 'Blocks' in response:
            blocks=response['Blocks']
            print ('Retrieved {} Blocks from Textract Text Detection response'.format(len(blocks)))      
        else:
            print("No blocks found in Textract Text Detection response, could be a result of unreadable document.")
            finished = True           

        # Display block information
        for block in blocks:
            result.append(block)
            if 'NextToken' in response:
                paginationToken = response['NextToken']
            else:
                paginationToken = None
                finished = True  
    
    if 'DocumentMetadata' not in response:
        return 0, result      
    return response['DocumentMetadata']['Pages'], result

#Function to extract lines of text from all pages from textract response
def extractTextBody(blocks):
    total_line = 0
    document_text = {}
    for page in blocks['PAGE']:
        document_text['Page-{0:02d}'.format(page['Page'])] = {}
        print("Page-{} contains {} Lines".format(page['Page'], len(page['Relationships'][0]['Ids'])))
        total_line += len(page['Relationships'][0]['Ids'])
        for i, line_id in enumerate(page['Relationships'][0]['Ids']):
            page_line = None
            for line in blocks['LINE']:
                if line['Id'] == line_id:
                    page_line = line
                    break
            document_text['Page-{0:02d}'.format(page['Page'])]['Line-{0:04d}'.format(i+1)] = {}
            document_text['Page-{0:02d}'.format(page['Page'])]['Line-{0:04d}'.format(i+1)]['Text'] = page_line['Text']
    print(total_line)
    return document_text, total_line
