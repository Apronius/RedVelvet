import json
import boto3

textract_client = boto3.client('textract')
s3_bucket = boto3.resource('s3').Bucket('ttltextractjsonfilesbucket')


def get_detected_text(job_id: str, keep_newlines: bool = False) -> str:
    max_results = 1000
    pagination_token = None
    finished = False
    text = ''

    while not finished:
        if pagination_token is None:
            response = textract_client.get_document_text_detection(JobId=job_id,
                                                                   MaxResults=max_results)
        else:
            response = textract_client.get_document_text_detection(JobId=job_id,
                                                                   MaxResults=max_results,
                                                                   NextToken=pagination_token)

        sep = ' ' if not keep_newlines else '\n'
        text += sep.join([x['Text'] for x in response['Blocks'] if x['BlockType'] == 'LINE'])

        if 'NextToken' in response:
            pagination_token = response['NextToken']
        else:
            finished = True

    return text


def handler(event, _):
    for record in event['Records']:
        message = json.loads(record['Sns']['Message'])
        job_id = message['JobId']
        status = message['Status']
        filename = message['DocumentLocation']['S3ObjectName']

        print(f'JobId {job_id} has finished with status {status} for file {filename}')

        if status != 'SUCCEEDED':
            return

        text = get_detected_text(job_id)
        to_json = {'Document': filename, 'ExtractedText': text, 'TextractJobId': job_id}
        json_content = json.dumps(to_json).encode('UTF-8')
        output_file_name = filename.split('/')[-1].rsplit('.', 1)[0] + '.json'
        s3_bucket.Object(f'{output_file_name}').put(Body=bytes(json_content))

        return message
