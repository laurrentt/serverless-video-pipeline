import json
import os
import uuid

import boto3
from chalice import Chalice, Response

VIDEO_BINARY_TYPES = [
    'application/octet-stream',
    'audio/basic',
    'audio/mp4',
    'audio/mpeg',
    'audio/ogg',
    'audio/wav',
    'audio/webm',
    'video/mpeg',
    'video/ogg',
    'video/webm',
]

app = Chalice(app_name='serverless-video-pipeline-api')
app.debug = os.environ.get('DEBUG', 'false').lower() == 'true'


@app.route('/upload', methods=['PUT'], content_types=VIDEO_BINARY_TYPES)
def upload_to_s3():
    unique_id = uuid.uuid4().hex[:8]
    s3_key = f'inputs/{unique_id}'

    # upload tmp file to s3 bucket
    s3_resource = boto3.resource('s3')
    s3_object = s3_resource.Object(os.environ['TRANSCODER_BUCKET'], s3_key)
    s3_object.put(Body=app.current_request.raw_body)

    stepfunctions_client = boto3.client('stepfunctions')
    stepfunctions_client.start_execution(
        stateMachineArn=os.environ['STATE_MACHINE_ARN'],
        name=unique_id,
        input=json.dumps(
            {
                'UniqueId': unique_id
            }
        )
    )

    return {'JobId': unique_id}


@app.route('/job/{unique_id}/status')
def get_job_status(unique_id):
    stepfunctions_client = boto3.client('stepfunctions')
    describe_execution_response = stepfunctions_client.describe_execution(
        executionArn=os.environ['STATE_MACHINE_EXECUTION_BASE_ARN'] + unique_id,
    )
    status = describe_execution_response['status']

    response = {'Status': status}

    if status == 'SUCCEEDED':
        output_key = json.loads(describe_execution_response['output'])['PlaylistOutputKey'] + '.m3u8'
        bucket_name = os.environ['TRANSCODER_BUCKET']
        bucket_location = boto3.client('s3').get_bucket_location(Bucket=bucket_name)['LocationConstraint']
        bucket_location = f'-{bucket_location}' if bucket_location else ''
        response['PlaylistUrl'] = f'https://s3{bucket_location}.amazonaws.com/{bucket_name}/{output_key}'

    return response

