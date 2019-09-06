"""Results calculation functions."""

from __future__ import absolute_import


import datetime

RI_BASE_INSTANCE_TYPE = 'large'
# normalization factor
# https://aws.amazon.com/blogs/aws/new-instance-size-flexibility-for-ec2-reserved-instances/
NORMALIZATION_FACTOR = {
    'nano': 0.25,
    'micro': 0.5,
    'small': 1,
    'medium': 2,
    'large': 4,
    'xlarge': 8,
    '2xlarge': 16,
    '4xlarge': 32,
    '8xlarge': 64,
    '9xlarge': 72,
    '10xlarge': 80,
    '12xlarge': 96,
    '16xlarge': 128,
    '18xlarge': 144,
    '24xlarge': 192,
    '32xlarge': 256,
}

def calc_expiry_time(expiry):
    """Calculate the number of days until the reserved instance expires.

    Args:
        expiry (DateTime): A timezone-aware DateTime object of the date when
            the reserved instance will expire.

    Returns:
        The number of days between the expiration date and now.

    """
    return (expiry.replace(tzinfo=None) - datetime.datetime.utcnow()).days

def convert_instance(placement_key, count):
    """
    Used to calculate normalisation factor. Converts an instance type to RI_BASE_INSTANCE_TYPE
    placement_key is a tuple with the instance type and region: e.g ('c4.2xlarge', 'us-west-2a')
    count: is an int

    """
    instance = placement_key[0]
    region = placement_key[1]
    family, instance_type = instance.split('.')

    # test if it is a t instance type
    if instance_type.startswith('t'):
        print instance_type
        return placement_key, count

    # test if we know the instance type
    if instance_type not in NORMALIZATION_FACTOR:
        return placement_key, count
    
    # convert instance to normalised instance
    multiplier = NORMALIZATION_FACTOR[instance_type] / NORMALIZATION_FACTOR[RI_BASE_INSTANCE_TYPE]

    normalised_placement_key = ("%s.%s" % (family, RI_BASE_INSTANCE_TYPE))
    normalised_count = multiplier * count

    #print("Normalised placement key -> %s: %s" % (normalised_placement_key, normalised_count))
    return normalised_placement_key, normalised_count


def report_diffs(running_instances, reserved_instances):
    """Calculate differences between reserved instances and running instances.

    Prints a message string containg unused reservations, unreserved instances,
    and counts of running and reserved instances.

    Args:
        running_instances (dict): Dictionary object of running instances. Key
            is the unique identifier for RI's (instance type and availability
            zone). Value is the count of instances with those properties.
        reserved_instances (dict): Dictionary of reserved instances in the same
            format as running_instances.

    Returns:
        A dict of the unused reservations, unreserved instances and counts of
        each.

    """

    normalised_running_instances = {}
    instance_diff = {}
    regional_benefit_ris = {}
    # loop through the reserved instances

    # normalise instances using normalisation factor
    for placement_key, count in running_instances.items():
        print("%s: %s" % (placement_key, count))
        # convert instance type using normalisation factor
        normalised_placement_key, normalised_count = convert_instance(placement_key, count)
        count_ = normalised_running_instances.get(normalised_placement_key, 0)
        normalised_running_instances[normalised_placement_key] = normalised_count + count_

    print("normalised running instances")
    print normalised_running_instances

    print("reserved")
    for placement_key, count in reserved_instances.items():
        print("%s: %s" % (placement_key, count))
        # if the AZ from an RI is 'All' (regional benefit RI)
        if placement_key[1] == 'All':
            # put into another dict for these RIs for processing later
            regional_benefit_ris[placement_key[0]] = reserved_instances[
                placement_key]
        else:
            instance_diff[placement_key] = reserved_instances[
                placement_key] - running_instances.get(placement_key, 0)

    # add unreserved instances to instance_diff
    for placement_key, count in running_instances.items():
        instance_type = placement_key[0]
        if placement_key not in reserved_instances:
            instance_diff[placement_key] = -running_instances[
                placement_key]

    # loop through regional benefit RI's
    for ri in regional_benefit_ris:
        # loop through the entire instace diff
        for placement_key in instance_diff:
            # find unreserved instances with the same type as the regional
            # benefit RI
            if (placement_key[0] == ri and placement_key[1] != 'All' and
                    instance_diff[placement_key] < 0):
                # loop while incrementing unreserved instances (less than 0)
                # and decrementing count of regional benefit RI's
                while True:
                    if (instance_diff[placement_key] == 0 or
                            regional_benefit_ris[ri] == 0):
                        break
                    instance_diff[placement_key] += 1
                    regional_benefit_ris[ri] -= 1

        instance_diff[(ri, 'All')] = regional_benefit_ris[ri]

    unused_reservations = {key: value for key, value in
                           instance_diff.items() if value > 0}
    unreserved_instances = {key: -value for key, value in
                            instance_diff.items() if value < 0}

    # TO DO: tidy up reserved instances

    qty_running_instances = 0
    for instance_count in running_instances.values():
        qty_running_instances += instance_count

    qty_reserved_instances = 0
    for instance_count in reserved_instances.values():
        qty_reserved_instances += instance_count

    qty_unreserved_instances = 0
    for instance_count in unreserved_instances.values():
        qty_unreserved_instances += instance_count
    return {
        'unused_reservations': unused_reservations,
        'unreserved_instances': unreserved_instances,
        'reserved_instances': reserved_instances,
        'qty_running_instances': qty_running_instances,
        'qty_reserved_instances': qty_reserved_instances,
        'qty_unreserved_instances': qty_unreserved_instances,
    }
