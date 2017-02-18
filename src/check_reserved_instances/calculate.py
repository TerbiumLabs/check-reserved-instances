"""Calculate the RI's for each AWS service."""

from collections import defaultdict
import datetime

import boto
import boto.elasticache
import boto.rds
import boto3
import dateutil.parser


# instance IDs/name to report with unreserved instances
instance_ids = defaultdict(list)

# reserve expiration time to report with unused reservations
reserve_expiry = defaultdict(list)


def calc_expiry_time(expiry):
    """Calculate the number of days until the reserved instance expires.

    Args:
        expiry: Either a string of the ISO 8601 timestamp from the AWS instance
            reservation expiration date, or a UNIX timestamp (float).

    Returns:
        The number of days between the expiration date and now.
    """
    if isinstance(expiry, float):
        expiry_datetime = datetime.datetime.fromtimestamp(expiry).replace(
            tzinfo=None)
    else:
        expiry_datetime = dateutil.parser.parse(expiry).replace(tzinfo=None)
    return (expiry_datetime - datetime.datetime.utcnow()).days


def calculate_ec2_ris(account):
    """Calculate the running/reserved instances in EC2.

    Args:
        account (dict): The AWS Account to scan as loaded from the
            configuration file.

    Returns:
        Results of running the `report_diffs` function.
    """
    aws_access_key_id = account['aws_access_key_id']
    aws_secret_access_key = account['aws_secret_access_key']
    region = account['region']
    client = boto3.client('ec2')
    ec2 = boto3.resource("ec2", region_name=region)

    ec2_conn = boto.ec2.connect_to_region(
        region_name=region, aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key)
    ec2_reservations = ec2_conn.get_all_instances()

    # Loop through running EC2 instances and record their AZ, type, and
    # Instance ID or Name Tag if it exists.
    ec2_running_instances = {}
    for reservation in ec2_reservations:
        for instance in reservation.instances:
            # Ignore non-running and spot instances
            if (instance.state == 'running' and not
                    instance.spot_instance_request_id):
                instance_type = instance.instance_type
		az = region
                ec2_running_instances[(
                    instance_type, az)] = ec2_running_instances.get(
                    (instance_type, az), 0) + 1

                if 'Name' in instance.tags and len(instance.tags['Name']) > 0:
                    instance_ids[(instance_type, az)].append(
                        instance.tags['Name'])
                else:
                    instance_ids[(instance_type, az)].append(instance.id)

    # Loop through active EC2 RIs and record their AZ and type.
    ec2_reserved_instances = {}
    for reserved_instance in client.describe_reserved_instances()["ReservedInstances"]:
        if reserved_instance["State"] == 'active':
            instance_type = reserved_instance["InstanceType"]
            az = region
            ec2_reserved_instances[(
                instance_type, az)] = ec2_reserved_instances.get(
                (instance_type, az), 0) + reserved_instance["InstanceCount"]

            reserve_expiry[(instance_type, az)].append(calc_expiry_time(
                expiry=str(reserved_instance["End"])))

    results = report_diffs(ec2_running_instances, ec2_reserved_instances,
                           'EC2')
    return results

def calculate_elc_ris(account):
    """Calculate the running/reserved instances in ElastiCache.

    Args:
        account (dict): The AWS Account to scan as loaded from the
            configuration file.

    Returns:
        Results of running the `report_diffs` function.
    """
    aws_access_key_id = account['aws_access_key_id']
    aws_secret_access_key = account['aws_secret_access_key']
    region = account['region']

    elc_conn = boto.elasticache.connect_to_region(
        region_name=region, aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key)

    # describe_cache_clusters() is limited to 100 results.
    elc_reservations = elc_conn.describe_cache_clusters()

    # Loop through running ElastiCache instance and record their engine,
    # type, and name.
    elc_running_instances = {}
    for instance in (elc_reservations['DescribeCacheClustersResponse']
                                     ['DescribeCacheClustersResult']
                                     ['CacheClusters']):
        if instance['CacheClusterStatus'] == 'available':
            engine = instance['Engine']
            instance_type = instance['CacheNodeType']

            elc_running_instances[(
                instance_type, engine)] = elc_running_instances.get(
                    (instance_type, engine), 0) + 1

            instance_ids[(instance_type, engine)].append(
                instance['CacheClusterId'])

    # Loop through active ElastiCache RIs and record their type and engine.
    elc_reserved_instances = {}
    # describe_reserved_cache_nodes() is limited to 100 results.
    for reserved_instance in (elc_conn.describe_reserved_cache_nodes()
                              ['DescribeReservedCacheNodesResponse']
                              ['DescribeReservedCacheNodesResult']
                              ['ReservedCacheNodes']):
        if reserved_instance['State'] == 'active':
            engine = reserved_instance['ProductDescription']
            instance_type = reserved_instance['CacheNodeType']

            elc_reserved_instances[(
                instance_type, engine)] = (elc_reserved_instances.get(
                                           (instance_type, engine), 0) +
                                           reserved_instance['CacheNodeCount'])

            expiry_time = (
                reserved_instance['StartTime'] + reserved_instance['Duration'])

            reserve_expiry[(instance_type, engine)].append(calc_expiry_time(
                expiry=expiry_time))

    results = report_diffs(elc_running_instances, elc_reserved_instances,
                           'ElastiCache')
    return results


def calculate_rds_ris(account):
    """Calculate the running/reserved instances in RDS.

    Args:
        account (dict): The AWS Account to scan as loaded from the
            configuration file.

    Returns:
        Results of running the `report_diffs` function.
    """
    aws_access_key_id = account['aws_access_key_id']
    aws_secret_access_key = account['aws_secret_access_key']
    region = account['region']

    # rds and boto3 rds are required - rds supports full listing of RDS
    # instances (no pagination/max limit), boto3 rds supports RDS reserved
    # instances.
    rds_conn = boto.rds.connect_to_region(
        region_name=region, aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key)
    boto3_rds_conn = boto3.client(
        'rds', region_name=region, aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key)

    rds_reservations = rds_conn.get_all_dbinstances()

    # Loop through running RDS instances and record their Multi-AZ setting,
    # type, and Name
    rds_running_instances = {}
    for instance in rds_reservations:
        if instance.status == 'available':
            az = instance.multi_az
            instance_type = instance.instance_class
            rds_running_instances[(
                instance_type, az)] = rds_running_instances.get(
                    (instance_type, az), 0) + 1

            instance_ids[(instance_type, az)].append(instance.id)

    # Loop through active RDS RIs and record their type and Multi-AZ setting.
    rds_reserved_instances = {}
    # describe_reserved_db_instances() is limited to 100 results.
    for reserved_instance in (boto3_rds_conn.describe_reserved_db_instances()
                              ['ReservedDBInstances']):
        if reserved_instance['State'] == 'active':
            az = reserved_instance['MultiAZ']
            instance_type = reserved_instance['DBInstanceClass']
            rds_reserved_instances[(
                instance_type, az)] = rds_reserved_instances.get(
                (instance_type, az), 0) + reserved_instance['DBInstanceCount']

            expiry_time = (
                float(reserved_instance['StartTime'].strftime('%s')) +
                reserved_instance['Duration'])

            reserve_expiry[(instance_type, az)].append(calc_expiry_time(
                expiry=expiry_time))

    results = report_diffs(rds_running_instances, rds_reserved_instances,
                           'RDS')
    return results


def report_diffs(running_instances, reserved_instances, service):
    """Calculate differences between reserved instances and running instances.

    Prints a message string containg unused reservations, unreserved instances,
    and counts of running and reserved instances.

    Args:
        running_instances (dict): Dictionary object of running instances. Key
            is the unique identifier for RI's (instance type and availability
            zone). Value is the count of instances with those properties.
        reserved_instances (dict): Dictionary of reserved instances in the same
            format as running_instances.
        service (str): The AWS service of reservation to report, such as EC2,
            RDS, etc. Used only for outputting in the report.

    Returns:
        A dict of the unused reservations, unreserved instances and counts of
        each.
    """
    instance_diff = dict([(x, reserved_instances[x] -
                           running_instances.get(x, 0))
                          for x in reserved_instances])

    for placement_key in running_instances:
        if placement_key not in reserved_instances:
            instance_diff[placement_key] = -running_instances[
                placement_key]

    unused_reservations = dict((key, value) for key, value in
                               instance_diff.items() if value > 0)

    unreserved_instances = dict((key, -value) for key, value in
                                instance_diff.items() if value < 0)

    qty_running_instances = 0
    for instance_count in running_instances.values():
        qty_running_instances += instance_count

    qty_reserved_instances = 0
    for instance_count in reserved_instances.values():
        qty_reserved_instances += instance_count

    return {
        service: (
            unused_reservations, unreserved_instances,
            qty_running_instances, qty_reserved_instances
        )
    }
