"""Calculate the RI's for each AWS service."""

from __future__ import absolute_import

from collections import defaultdict
import datetime

import boto3

from check_reserved_instances.calculate import calc_expiry_time


# instance IDs/name to report with unreserved instances
instance_ids = defaultdict(list)

# reserve expiration time to report with unused reservations
reserve_expiry = defaultdict(list)


def create_boto_session(account):
    """Set up the boto3 session to connect to AWS.

    Args:
        account (dict): The AWS Account to scan as loaded from the
            configuration file.

    Returns:
        The authenticated boto3 session.

    """
    aws_access_key_id = account['aws_access_key_id']
    aws_secret_access_key = account['aws_secret_access_key']
    aws_role_arn = account['aws_role_arn']
    region = account['region']
    aws_profile = account['aws_profile']

    if aws_role_arn:
        sts_client = boto3.client('sts', region_name=region)
        creds = sts_client.assume_role(
            RoleArn=aws_role_arn, RoleSessionName='check-reserved-instances')
        aws_access_key_id = creds['Credentials']['AccessKeyId']
        aws_secret_access_key = creds['Credentials']['SecretAccessKey']
        aws_session_token = creds['Credentials']['SessionToken']
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name=region,
            profile_name=aws_profile,
        )
    else:
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region,
            profile_name=aws_profile,
        )

    return session


def calculate_ec2_ris(session, results):
    """Calculate the running/reserved instances in EC2.

    This function is unique as it performs both checks for both VPC-launched
    instances, and EC2-Classic instances. Classic and VPC
    instances/reservations are treated separately in the report.

    Args:
        session (:boto3:session.Session): The authenticated boto3 session.
        results (dict): Global results in dictionary format to be appended.

    Returns:
        A dictionary of the running/reserved instances for both VPC and Classic
        instances.

    """
    ec2_conn = session.client('ec2')

    # check to see if account is VPC-only (affects reserved instance reporting)
    account_is_vpc_only = (
        [{'AttributeValue': 'VPC'}] == ec2_conn.describe_account_attributes(
            AttributeNames=['supported-platforms'])['AccountAttributes'][0]
        ['AttributeValues'])

    paginator = ec2_conn.get_paginator('describe_instances')
    page_iterator = paginator.paginate(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])

    # Loop through running EC2 instances and record their AZ, type, and
    # Instance ID or Name Tag if it exists.
    for page in page_iterator:
        for reservation in page['Reservations']:
            for instance in reservation['Instances']:
                # Ignore spot instances
                if 'SpotInstanceRequestId' not in instance:
                    az = instance['Placement']['AvailabilityZone']
                    instance_type = instance['InstanceType']
                    # Check for 'skip reservation' tag and name tag
                    found_skip_tag = False
                    instance_name = None
                    if 'Tags' in instance:
                        for tag in instance['Tags']:
                            if tag['Key'] == 'NoReservation' and len(
                                tag['Value']) > 0 and tag[
                                    'Value'].lower() == 'true':
                                found_skip_tag = True
                            if tag['Key'] == 'Name' and len(tag['Value']) > 0:
                                instance_name = tag['Value']

                    # If skip tag is not found, increment running instances
                    # count and add instance name/ID
                    if not found_skip_tag:
                        # not in vpc
                        if not instance.get('VpcId'):
                            results['ec2_classic_running_instances'][(
                                instance_type,
                                az)] = results[
                                'ec2_classic_running_instances'].get(
                                (instance_type, az), 0) + 1
                            instance_ids[(instance_type, az)].append(
                                instance['InstanceId'] if not instance_name
                                else instance_name)
                        else:
                            # inside vpc
                            results['ec2_vpc_running_instances'][
                                (instance_type,
                                 az)] = results[
                                'ec2_vpc_running_instances'].get(
                                (instance_type, az), 0) + 1
                            instance_ids[(instance_type, az)].append(
                                instance['InstanceId'] if not instance_name
                                else instance_name)

    # Loop through active EC2 RIs and record their AZ and type.
    for reserved_instance in ec2_conn.describe_reserved_instances(
            Filters=[{'Name': 'state', 'Values': ['active']}])[
            'ReservedInstances']:
        # Detect if an EC2 RI is a regional benefit RI or not
        if reserved_instance['Scope'] == 'Availability Zone':
            az = reserved_instance['AvailabilityZone']
        else:
            az = 'All'

        instance_type = reserved_instance['InstanceType']
        # check if VPC/Classic reserved instance
        if account_is_vpc_only or 'VPC' in reserved_instance.get(
                'ProductDescription'):
            results['ec2_vpc_reserved_instances'][(
                instance_type, az)] = results[
                'ec2_vpc_reserved_instances'].get(
                (instance_type, az), 0) + reserved_instance['InstanceCount']
        else:
            results['ec2_classic_reserved_instances'][(
                instance_type, az)] = results[
                'ec2_classic_reserved_instances'].get(
                (instance_type, az), 0) + reserved_instance['InstanceCount']

        reserve_expiry[(instance_type, az)].append(calc_expiry_time(
            expiry=reserved_instance['End']))

    return results


def calculate_elc_ris(session, results):
    """Calculate the running/reserved instances in ElastiCache.

    Args:
        session (:boto3:session.Session): The authenticated boto3 session.
        results (dict): Global results in dictionary format to be appended.

    Returns:
        A dictionary of the running/reserved instances for ElastiCache nodes.

    """
    elc_conn = session.client('elasticache')

    paginator = elc_conn.get_paginator('describe_cache_clusters')
    page_iterator = paginator.paginate()
    # Loop through running ElastiCache instance and record their engine,
    # type, and name.
    for page in page_iterator:
        for instance in page['CacheClusters']:
            if instance['CacheClusterStatus'] == 'available':
                engine = instance['Engine']
                instance_type = instance['CacheNodeType']

                results['elc_running_instances'][(
                    instance_type, engine)] = results[
                    'elc_running_instances'].get(
                        (instance_type, engine), 0) + instance['NumCacheNodes']
                instance_ids[(instance_type, engine)].append(
                    instance['CacheClusterId'])

    paginator = elc_conn.get_paginator('describe_reserved_cache_nodes')
    page_iterator = paginator.paginate()
    # Loop through active ElastiCache RIs and record their type and engine.
    for page in page_iterator:
        for reserved_instance in page['ReservedCacheNodes']:
            if reserved_instance['State'] == 'active':
                engine = reserved_instance['ProductDescription']
                instance_type = reserved_instance['CacheNodeType']

                results['elc_reserved_instances'][(instance_type, engine)] = (
                    results['elc_reserved_instances'].get((
                        instance_type, engine), 0) + reserved_instance[
                        'CacheNodeCount'])

                # No end datetime is returned, so calculate from 'StartTime'
                # (a `DateTime`) and 'Duration' in seconds (integer)
                expiry_time = reserved_instance[
                    'StartTime'] + datetime.timedelta(
                        seconds=reserved_instance['Duration'])

                reserve_expiry[(instance_type, engine)].append(
                    calc_expiry_time(expiry=expiry_time))

    return results


def calculate_rds_ris(session, results):
    """Calculate the running/reserved instances in RDS.

    Args:
        session (:boto3:session.Session): The authenticated boto3 session.
        results (dict): Global results in dictionary format to be appended.

    Returns:
        A dictionary of the running/reserved instances for RDS instances.

    """
    rds_conn = session.client('rds')

    paginator = rds_conn.get_paginator('describe_db_instances')
    page_iterator = paginator.paginate()

    # Loop through running RDS instances and record their Multi-AZ setting,
    # type, and Name
    for page in page_iterator:
        for instance in page['DBInstances']:
            az = instance['MultiAZ']
            instance_type = instance['DBInstanceClass']
            results['rds_running_instances'][(
                instance_type, az)] = results['rds_running_instances'].get(
                    (instance_type, az), 0) + 1
            instance_ids[(instance_type, az)].append(
                instance['DBInstanceIdentifier'])

    paginator = rds_conn.get_paginator('describe_reserved_db_instances')
    page_iterator = paginator.paginate()
    # Loop through active RDS RIs and record their type and Multi-AZ setting.
    for page in page_iterator:
        for reserved_instance in page['ReservedDBInstances']:
            if reserved_instance['State'] == 'active':
                az = reserved_instance['MultiAZ']
                instance_type = reserved_instance['DBInstanceClass']
                results['rds_reserved_instances'][(
                    instance_type, az)] = results[
                    'rds_reserved_instances'].get(
                    (instance_type, az), 0) + reserved_instance[
                    'DBInstanceCount']

                # No end datetime is returned, so calculate from 'StartTime'
                # (a `DateTime`) and 'Duration' in seconds (integer)
                expiry_time = reserved_instance[
                    'StartTime'] + datetime.timedelta(
                        seconds=reserved_instance['Duration'])

                reserve_expiry[(instance_type, az)].append(calc_expiry_time(
                    expiry=expiry_time))

    return results
