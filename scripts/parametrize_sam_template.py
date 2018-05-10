# This script will become obsolete once https://github.com/aws/chalice/pull/612 is merged
# or https://github.com/aws/chalice/issues/608 is closed
import json
import click


@click.command()
@click.argument('source_template')
@click.argument('destination_template')
def parametrize_sam_template(source_template, destination_template):
    with open(source_template, 'r') as s:
        source_template_data = json.load(s)

    env_vars = source_template_data['Resources']['APIHandler']['Properties']['Environment']['Variables']
    env_vars['TRANSCODER_BUCKET'] = {"Fn::GetAtt": "Transcoder.Outputs.TranscoderBucket"}
    env_vars['STATE_MACHINE_ARN'] = {"Fn::GetAtt": "StateMachine.Outputs.TranscoderStateMachineArn"}
    env_vars['STATE_MACHINE_EXECUTION_BASE_ARN'] = {"Fn::GetAtt": "StateMachine.Outputs.TranscoderStateMachineExecutionBaseArn"}

    source_template_data['Resources']['APIHandler']['Properties']['Role'] = {"Fn::GetAtt": "ApiExecutionRole.Arn"}

    with open(destination_template, 'w') as d:
        json.dump(source_template_data, d, indent=2)


if __name__ == '__main__':
    parametrize_sam_template()
