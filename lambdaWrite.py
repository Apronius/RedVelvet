import json
import boto3
import os
from Classes import Document

dynamodb = boto3.client('dynamodb')

def getJobResults(jobId):
    """
    Get readed pages based on jobId
    """

    pages = []
    textract = boto3.client('textract')
    response = textract.get_document_analysis(JobId=jobId)
    
    pages.append(response)

    nextToken = None
    if('NextToken' in response):
        nextToken = response['NextToken']

    while(nextToken):
        response = textract.get_document_analysis(JobId=jobId, NextToken=nextToken)
        pages.append(response)
        nextToken = None
        if('NextToken' in response):
            nextToken = response['NextToken']

    return pages

def convert_row_to_list(row):
    """
    Helper method to convert a row to a list.
    """
    list_of_cells = [cell.text.strip() for cell in row.cells]
    return list_of_cells


def write_dict_to_db(mydict):
#NOT SURE#
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('ttlDynamoTestTable')

    table.put_item(
        Item={
                'IDnumber': '',
                'FirstName': '',
                'Last_name': '',
            }
)

def lambda_handler(event, context):
    dynamodb = boto3.client('dynamodb')
    """
    Get Extraction Status, JobTag and JobId from SNS. 
    If the Status is SUCCEEDED then create a dict of the values and write those to the RDS database.
    """
    notificationMessage = json.loads(json.dumps(event))['Records'][0]['Sns']['Message']
    
    pdfTextExtractionStatus = json.loads(notificationMessage)['Status']
    pdfTextExtractionJobTag = json.loads(notificationMessage)['JobTag']
    pdfTextExtractionJobId = json.loads(notificationMessage)['JobId']
    
    print(pdfTextExtractionJobTag + ' : ' + pdfTextExtractionStatus)
    
    if(pdfTextExtractionStatus == 'SUCCEEDED'):
        response = getJobResults(pdfTextExtractionJobId)
        doc = Document(response)

    all_values = []

    for page in doc.pages:
        for table in page.tables:
            for i, row in enumerate(table.rows):
                if i == 0:
                    keys = convert_row_to_list(table.rows[0])
                else:
                    values = convert_row_to_list(row)
                    all_values.append(dict(zip(keys, values)))

    for dictionary in all_values:
        write_dict_to_db(dictionary)