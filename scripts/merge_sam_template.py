# This script will become obsolete once https://github.com/awslabs/serverless-application-model/issues/90 is fixed
import click
import yaml
import collections


def update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


@click.command()
@click.argument('base')
@click.argument('to_merge')
def merge_sam_template(base, to_merge):
    with open(base, 'r') as b:
        base_template_data = yaml.load(b)

    with open(to_merge, 'r') as m:
        to_merge_template_data = yaml.load(m)

    merged_template_data = update(base_template_data, to_merge_template_data)

    with open(base, 'w') as b:
        yaml.dump(merged_template_data, b)


if __name__ == '__main__':
    merge_sam_template()
