"""'Unit' tests.

Unfortunately, moto doesn't support creation of reserved instances (yet).

https://github.com/spulec/moto/blob/master/moto/ec2/responses/reserved_instances.py
"""
import datetime

from click.testing import CliRunner
import mock

from check_reserved_instances import cli


def get_ec2_instances():
    """Return a mocked list of EC2 instances."""
    return {
        u'Reservations': [
            {
                u'Groups': [],
                u'Instances': [
                    {
                        'Placement': {
                            'AvailabilityZone': 'us-east-1b',
                            'GroupName': '',
                            'Tenancy': 'default'
                        },
                        'InstanceType': 'm4.large',
                        'InstanceId': 'i-456sdf4g',
                        'Tags': [
                            {
                                'Key': 'Name',
                                'Value': 'test'
                            }
                        ]
                    }
                ]
            },
            {
                u'Groups': [],
                u'Instances': [
                    {
                        'Placement': {
                            'AvailabilityZone': 'us-east-1b',
                            'GroupName': '',
                            'Tenancy': 'default'
                        },
                        'InstanceType': 'c3.large',
                        'InstanceId': 'i-sdklfmi3',
                        'Tags': [
                            {
                                'Key': 'Name',
                                'Value': 'test2'
                            }
                        ]
                    }
                ]
            },
            {
                u'Groups': [],
                u'Instances': [
                    {
                        'Placement': {
                            'AvailabilityZone': 'us-east-1b',
                            'GroupName': '',
                            'Tenancy': 'default'
                        },
                        'InstanceType': 'c3.large',
                        'InstanceId': 'i-kcndnj3j',
                        'Tags': [
                            {
                                'Key': 'Name',
                                'Value': 'test2'
                            }
                        ]
                    }
                ]
            },
            {
                u'Groups': [],
                u'Instances': [
                    {
                        'Placement': {
                            'AvailabilityZone': 'us-east-1b',
                            'GroupName': '',
                            'Tenancy': 'default'
                        },
                        'InstanceType': 'c3.large',
                        'InstanceId': 'i-mnen9n4n',
                        'Tags': [
                            {
                                'Key': 'Name',
                                'Value': 'test2'
                            }
                        ]
                    }
                ]
            },
            {
                u'Groups': [],
                u'Instances': [
                    {
                        'Placement': {
                            'AvailabilityZone': 'us-east-1b',
                            'GroupName': '',
                            'Tenancy': 'default'
                        },
                        'InstanceType': 'c3.large',
                        'InstanceId': 'i-qnhvhzn3',
                        'Tags': [
                            {
                                'Key': 'Name',
                                'Value': 'test2'
                            }
                        ]
                    }
                ]
            },
            {
                u'Groups': [],
                u'Instances': [
                    {
                        'Placement': {
                            'AvailabilityZone': 'us-east-1d',
                            'GroupName': '',
                            'Tenancy': 'default'
                        },
                        'InstanceType': 'c3.large',
                        'VpcId': 'vpc-23hund21',
                        'InstanceId': 'i-lksjdfi2',
                        'Tags': [
                            {
                                'Key': 'Name',
                                'Value': 'test3'
                            }
                        ]
                    }
                ]
            },
            {
                u'Groups': [],
                u'Instances': [
                    {
                        'Placement': {
                            'AvailabilityZone': 'us-east-1b',
                            'GroupName': '',
                            'Tenancy': 'default'
                        },
                        'VpcId': 'vpc-23hund21',
                        'InstanceType': 'm4.large',
                        'InstanceId': 'i-sdf3f4d6'
                    }
                ]
            },
            {
                u'Groups': [],
                u'Instances': [
                    {
                        'Placement': {
                            'AvailabilityZone': 'us-east-1c',
                            'GroupName': '',
                            'Tenancy': 'default'
                        },
                        'InstanceType': 't1.micro',
                        'InstanceId': 'i-dfgeqa53',
                        'Tags': [
                            {
                                'Key': 'Random',
                                'Value': 'Tag'
                            }
                        ]
                    }
                ]
            },
            {
                u'Groups': [],
                u'Instances': [
                    {
                        'Placement': {
                            'AvailabilityZone': 'us-east-1c',
                            'GroupName': '',
                            'Tenancy': 'default'
                        },
                        'VpcId': 'vpc-23hund21',
                        'InstanceType': 't2.medium',
                        'InstanceId': 'i-sdfjj239',
                        'SpotInstanceRequestId':
                            'sfr-a1e8ac61-1029-4edc-8f06-92289516e0b7'
                    }
                ]
            },
            {
                u'Groups': [],
                u'Instances': [
                    {
                        'Placement': {
                            'AvailabilityZone': 'us-east-1c',
                            'GroupName': '',
                            'Tenancy': 'default'
                        },
                        'InstanceType': 't1.micro',
                        'InstanceId': 'i-odfg35vs',
                        'Tags': [
                            {
                                'Key': 'NoReservation',
                                'Value': 'True'
                            }
                        ]
                    }
                ]
            },
        ]
    }


def get_ec2_reserved_instances():
    """Return a mocked list of EC2 RIs."""
    return {
        'ReservedInstances': [
            {
                'Scope': 'Availability Zone',
                'AvailabilityZone': 'us-east-1b',
                'InstanceType': 'c4.large',
                'InstanceCount': 1,
                'ProductDescription': 'Linux/UNIX (Amazon VPC)',
                'End': datetime.datetime.utcnow() + datetime.timedelta(
                    days=365),
            },
            {
                'Scope': 'Availability Zone',
                'AvailabilityZone': 'us-east-1c',
                'InstanceType': 'm4.large',
                'InstanceCount': 1,
                'ProductDescription': 'Linux/UNIX (Amazon VPC)',
                'End': datetime.datetime.utcnow() + datetime.timedelta(
                    days=365),
            },
            {
                'Scope': 'Availability Zone',
                'AvailabilityZone': 'us-east-1b',
                'InstanceType': 'm4.large',
                'InstanceCount': 1,
                'ProductDescription': 'Linux/UNIX (Amazon VPC)',
                'End': datetime.datetime.utcnow() + datetime.timedelta(
                    days=365),
            },
            {
                'Scope': 'Region',
                'InstanceType': 'c3.large',
                'InstanceCount': 3,
                'ProductDescription': 'Linux/UNIX',
                'End': datetime.datetime.utcnow() + datetime.timedelta(
                    days=365),
            },
            {
                'Scope': 'Region',
                'InstanceType': 'm3.medium',
                'InstanceCount': 1,
                'ProductDescription': 'Linux/UNIX',
                'End': datetime.datetime.utcnow() + datetime.timedelta(
                    days=365),
            }
        ]
    }


def get_elc_instances():
    """Return a mocked list of ElastiCache instances."""
    return {
        'CacheClusters': [
            {
                'CacheClusterStatus': 'available',
                'Engine': 'redis',
                'CacheNodeType': 'cache.t2.small',
                'CacheClusterId': 'test1',
                'NumCacheNodes': 2,
            },
            {
                'CacheClusterStatus': 'stopped',
                'Engine': 'redis',
                'CacheNodeType': 'cache.m3.medium',
                'CacheClusterId': 'test2',
                'NumCacheNodes': 1,
            }
        ]
    }


def get_elc_reserved_instances():
    """Return a mocked list of ElastiCache RIs."""
    return {
        'ReservedCacheNodes': [
            {
                'State': 'active',
                'ProductDescription': 'redis',
                'CacheNodeType': 'cache.m1.medium',
                'CacheNodeCount': 1,
                'StartTime': datetime.datetime.utcnow(),
                'Duration': 31536000,
            },
            {
                'State': 'expired',
                'ProductDescription': 'redis',
                'CacheNodeType': 'cache.t2.small',
                'CacheNodeCount': 1,
                'StartTime': datetime.datetime.utcnow() - datetime.timedelta(
                    days=365),
                'Duration': 31536000,
            }
        ]
    }


def get_rds_instances():
    """Return a mocked list of RDS instances."""
    return {
        'DBInstances': [
            {
                'MultiAZ': True,
                'DBInstanceClass': 'db.t2.medium',
                'DBInstanceIdentifier': 'test1'
            },
            {
                'MultiAZ': False,
                'DBInstanceClass': 'db.m3.medium',
                'DBInstanceIdentifier': 'test2'
            }
        ]
    }


def get_rds_reserved_instances():
    """Return a mocked list of RDS RIs."""
    return {
        'ReservedDBInstances': [
            {
                'State': 'active',
                'MultiAZ': True,
                'DBInstanceClass': 'db.m4.xlarge',
                'DBInstanceCount': 1,
                'StartTime': datetime.datetime.utcnow(),
                'Duration': 31536000,
            },
            {
                'State': 'expired',
                'MultiAZ': False,
                'DBInstanceClass': 'db.m4.large',
                'DBInstanceCount': 1,
                'StartTime': datetime.datetime.utcnow(),
                'Duration': 31536000,
            }
        ]
    }


@mock.patch('check_reserved_instances.aws.boto3.client')
@mock.patch('check_reserved_instances.aws.boto3.Session')
def test_aws_sts(mocked_session, mocked_client):
    """Test using AssumeRole to authenticate to AWS."""
    paginate = mocked_session.return_value.client.return_value.get_paginator
    paginate.return_value.paginate.return_value = [get_ec2_instances()]

    client = mocked_session.return_value.client
    client.return_value.describe_reserved_instances.return_value = (
        get_ec2_reserved_instances())

    sts_client = mocked_client.return_value.client
    sts_client.return_value.assume_role.return_value = {
        'Credentials': {
            'AccessKeyId': 'test',
            'SecretAccessKey': 'test',
            'SessionToken': 'test'
        }
    }

    runner = CliRunner()
    result = runner.invoke(
        cli, ['--config', 'tests/fixtures/config.ini.aws_sts'])

    assert 'Reserved Instances Report' in result.output
    assert 'Not sending email for this report' in result.output


def test_bad_email_config():
    """Test loading a bad config file with missing email options."""
    runner = CliRunner()
    result = runner.invoke(
        cli, ['--config', 'tests/fixtures/config.ini.bad_email'])

    assert ('Required configuration option for email '
            '(smtp_host)' in result.output)


def test_config_empty():
    """Test loading an empty config file."""
    runner = CliRunner()
    result = runner.invoke(
        cli, ['--config', 'tests/fixtures/config.ini.empty'])

    assert ('Please specify at least one [AWS ] section in the configuration '
            'file!' in result.output)


def test_not_aws_config():
    """Test loading a non-blank config with no AWS sections."""
    runner = CliRunner()
    result = runner.invoke(
        cli, ['--config', 'tests/fixtures/config.ini.no_aws'])

    assert ('Please specify at least one [AWS ] section in the configuration '
            'file!' in result.output)


@mock.patch('check_reserved_instances.aws.boto3.Session')
def test_success_no_email(mocked_boto3):
    """Test a successful run without email."""
    paginate = mocked_boto3.return_value.client.return_value.get_paginator
    paginate.return_value.paginate.return_value = [get_ec2_instances()]

    client = mocked_boto3.return_value.client
    client.return_value.describe_reserved_instances.return_value = (
        get_ec2_reserved_instances())

    runner = CliRunner()
    result = runner.invoke(
        cli, ['--config', 'tests/fixtures/config.ini.no_email'])

    assert 'Not sending email for this report' in result.output


@mock.patch('check_reserved_instances.aws.boto3.Session')
@mock.patch('check_reserved_instances.report.smtplib')
def test_success_no_email_tls(mocked_smtplib, mocked_boto3):
    """Test a successful run with email but without TLS or SMTP auth."""
    paginate = mocked_boto3.return_value.client.return_value.get_paginator
    paginate.return_value.paginate.return_value = [get_ec2_instances()]

    client = mocked_boto3.return_value.client
    client.return_value.describe_reserved_instances.return_value = (
        get_ec2_reserved_instances())

    mocked_smtplib.return_value.sendmail.return_value = True

    runner = CliRunner()
    result = runner.invoke(
        cli, ['--config', 'tests/fixtures/config.ini.email_no_tls'])

    assert 'Sending emails to test@example.com' in result.output


@mock.patch('check_reserved_instances.aws.boto3.Session')
@mock.patch('check_reserved_instances.report.smtplib')
def test_success_run(mocked_smtplib, mocked_boto3):
    """Test a successful run for all services with email."""
    paginate = mocked_boto3.return_value.client.return_value.get_paginator
    paginate.return_value.paginate.side_effect = [
        [get_ec2_instances()],
        [get_rds_instances()],
        [get_rds_reserved_instances()],
        [get_elc_instances()],
        [get_elc_reserved_instances()],
        [get_ec2_instances()],
    ]

    client = mocked_boto3.return_value.client
    client.return_value.describe_reserved_instances.return_value = (
        get_ec2_reserved_instances())

    mocked_smtplib.return_value.starttls.return_value = True
    mocked_smtplib.return_value.login.return_value = True
    mocked_smtplib.return_value.sendmail.return_value = True

    runner = CliRunner()
    result = runner.invoke(
        cli, ['--config', 'tests/fixtures/config.ini.testing'],
        catch_exceptions=False)

    assert 'Reserved Instances Report' in result.output
    assert 'Sending emails to test@example.com' in result.output
