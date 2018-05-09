import json

import boto3
from botocore.vendored import requests

SUCCESS = "SUCCESS"
FAILED = "FAILED"
FAILED_PHYSICAL_RESOURCE_ID = "FAILED_PHYSICAL_RESOURCE_ID"


def lambda_handler(event, context):
    try:
        _lambda_handler(event, context)
    except Exception as e:
        send(
            event,
            context,
            response_status=FAILED if event['RequestType'] != 'Delete' else SUCCESS,
            # Do not fail on delete to avoid rollback failure
            response_data=None,
            physical_resource_id=event.get('PhysicalResourceId', FAILED_PHYSICAL_RESOURCE_ID),
            reason=str(e)
        )
        raise


def _lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    resource_type = event['ResourceType']
    request_type = event['RequestType']
    physical_resource_id = event.get('PhysicalResourceId')

    client = boto3.client('elastictranscoder')

    if resource_type != "Custom::ElasticTranscoderPipeline":
        raise ValueError('Resource type "{resource_type}"'.format(resource_type=resource_type))

    if request_type == 'Create':
        resource_properties = event['ResourceProperties']
        clean_resource_properties(resource_properties)
        response = client.create_pipeline(**resource_properties)
        physical_resource_id = response['Pipeline']['Id']

    elif request_type == 'Update':
        resource_properties = event['ResourceProperties']
        resource_properties['Id'] = physical_resource_id
        clean_resource_properties(resource_properties)
        response = client.update_pipeline(**resource_properties)
        physical_resource_id = response['Pipeline']['Id']

    elif request_type == 'Delete':
        client.delete_pipeline(Id=physical_resource_id)

    else:
        print('Request type is {request_type}, doing nothing.'.format(request_type=request_type))

    send(
        event,
        context,
        response_status=SUCCESS,
        response_data={'PipelineId': physical_resource_id},
        physical_resource_id=physical_resource_id,
    )


def clean_resource_properties(resource_properties):
    del resource_properties['ServiceToken']


def send(event, context, response_status, response_data, physical_resource_id, reason=None):
    response_url = event['ResponseURL']

    response_body = {
        'Status': response_status,
        'Reason': str(reason) if reason else 'See the details in CloudWatch Log Stream: ' + context.log_stream_name,
        'PhysicalResourceId': physical_resource_id,
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'Data': response_data,
    }

    json_response_body = json.dumps(response_body)

    headers = {
        'content-type': '',
        'content-length': str(len(json_response_body))
    }

    requests.put(
        response_url,
        data=json_response_body,
        headers=headers
    )
