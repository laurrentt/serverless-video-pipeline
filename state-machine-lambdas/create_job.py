import os
import uuid

import boto3

ELASTIC_TRANSCODER_PRESET_IDS = {
    'HLS_2M': '1351620000001-200010',
    'HLS_400K': '1351620000001-200050',
}


def lambda_handler(event, _):
    generated_output_id = str(uuid.uuid4())

    outputs = [
        {
            'Key': f'outputs/{generated_output_id}/out_400K',
            'PresetId': ELASTIC_TRANSCODER_PRESET_IDS['HLS_400K'],
            'SegmentDuration': '10',
            'Watermarks': [
                {
                    'PresetWatermarkId': 'BottomRight',
                    'InputKey': 'watermarks/aws_user_group_400K.png',
                }
            ]
        },
        {
            'Key': f'outputs/{generated_output_id}/out_2M',
            'PresetId': ELASTIC_TRANSCODER_PRESET_IDS['HLS_2M'],
            'SegmentDuration': '10',
            'Watermarks': [
                {
                    'PresetWatermarkId': 'BottomRight',
                    'InputKey': 'watermarks/aws_user_group_2M.png',
                }
            ]
        }
    ]

    create_job_response = boto3.client('elastictranscoder').create_job(
        PipelineId=os.environ['TRANSCODER_PIPELINE_ID'],
        Input={
            'Key': event['Input']['Key']
        },
        Outputs=outputs,
        Playlists=[
            {
                'Name': f'outputs/{generated_output_id}/out',
                'Format': 'HLSv3',
                'OutputKeys': [o['Key'] for o in outputs],
            }
        ]
    )

    event['Job'] = create_job_response['Job']

    return event
