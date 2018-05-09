import os
import uuid

import boto3


def lambda_handler(event, _):
    read_job_response = boto3.client('elastictranscoder').read_job(
        Id=event['Job']['Id']
    )

    event['Job'] = read_job_response['Job']

    return event
