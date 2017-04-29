"""Compare instance reservations and running instances for AWS services."""

import click
import pkg_resources

from check_reserved_instances.calculate import (
    calculate_ec2_ris, calculate_elc_ris, calculate_rds_ris)
from check_reserved_instances.config import parse_config
from check_reserved_instances.report import report_results

try:
    __version__ = pkg_resources.get_distribution(
        'check_reserved_instances').version
except:  # pragma: no cover
    __version__ = 'unknown'

# global configuration object
current_config = {}
# will look like:
# current_config = {
#   'Accounts': [
#       {
#           'name': 'Account 1',
#           'aws_access_key_id': '',
#           'aws_secret_access_key': '',
#           'region': 'us-east-1',
#           'rds': True,
#           'elasticache': True,
#       }
#    ],
#    'Email': {
#       'smtp_host': '',
#       'smtp_port': 25,
#       'smtp_user': '',
#       'smtp_password': '',
#       'smtp_recipients': '',
#       'smtp_sendas': '',
#       'smtp_tls': False,
#    }
# }


@click.command()
@click.option(
    '--config', default='config.ini',
    help='Provide the path to the configuration file',
    type=click.Path(exists=True))
def cli(config):
    """Compare instance reservations and running instances for AWS services.

    Args:
        config (str): The path to the configuration file.
    """
    current_config = parse_config(config)

    results = {}

    aws_accounts = current_config['Accounts']

    for aws_account in aws_accounts:
        name = aws_account['name']
        results[name] = []
        ec2 = calculate_ec2_ris(account=aws_account)
        results[name].append(ec2[0])
        results[name].append(ec2[1])

        if aws_account['rds'] is True:
            results[name].append(calculate_rds_ris(account=aws_account))
        if aws_account['elasticache'] is True:
            results[name].append(calculate_elc_ris(account=aws_account))
    report_results(current_config, results)
