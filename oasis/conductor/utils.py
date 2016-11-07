from oasis.objects import nodepool_policy


def retrieve_nodepool_policy(context, nodepool):
    return nodepool_policy.NodePoolPolicy.get_by_id(context, nodepool.nodepool_policy_id)
