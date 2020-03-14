import boto3

region=os.environ['AWS_REGION']


dynamodb = boto3.client('dynamodb')

textract = boto3.client('textract')

comprehend = boto3.client('comprehend')

s3 = boto3.resource('s3')
s3client = boto3.client('s3')

