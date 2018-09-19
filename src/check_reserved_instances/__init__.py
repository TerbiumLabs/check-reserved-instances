"""Compare instance reservations and running instances for AWS services."""

from __future__ import absolute_import

import click
import pkg_resources

from check_reserved_instances.aws import (
    calculate_ec2_ris, calculate_elc_ris, calculate_rds_ris,
    create_boto_session)
from check_reserved_instances.calculate import report_diffs
from check_reserved_instances.config import parse_config
from check_reserved_instances.report import report_results

try:
    __version__ = pkg_resources.get_distribution(
        'check_reserved_instances').version
except:  # pragma: no cover  # noqa: E722
    __version__ = 'unknown'

# global configuration object
current_config = {}
# will look like:
# current_config = {
#   'Accounts': [
#       {
#           'name': 'Account 1',
#           'aws_role_arn': '',
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
    # global results for all accounts
    results = {
        'ec2_classic_running_instances': {},
        'ec2_classic_reserved_instances': {},
        'ec2_vpc_running_instances': {},
        'ec2_vpc_reserved_instances': {},
        'elc_running_instances': {},
        'elc_reserved_instances': {},
        'rds_running_instances': {},
        'rds_reserved_instances': {},
    }
    aws_accounts = current_config['Accounts']

    for aws_account in aws_accounts:
        session = create_boto_session(aws_account)
        results = calculate_ec2_ris(session, results)

        if aws_account['rds'] is True:
            results = calculate_rds_ris(session, results)
        if aws_account['elasticache'] is True:
            results = calculate_elc_ris(session, results)

    report = {}
    report['EC2 Classic'] = report_diffs(
        results['ec2_classic_running_instances'],
        results['ec2_classic_reserved_instances'])
    report['EC2 VPC'] = report_diffs(
        results['ec2_vpc_running_instances'],
        results['ec2_vpc_reserved_instances'])
    report['ElastiCache'] = report_diffs(
        results['elc_running_instances'],
        results['elc_reserved_instances'])
    report['RDS'] = report_diffs(
        results['rds_running_instances'],
        results['rds_reserved_instances'])
    report_results(current_config, report)
