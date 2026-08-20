import networkx as nx
from app.graph.nodes import CloudNode


class CloudTopology:

    def __init__(self):
        self.graph = nx.DiGraph()

    def add_node(self, resource):
        self.graph.add_node(
            resource.resource_id,
            resource_type=resource.resource_type,
            name=resource.name
        )

    def add_relationship(self, source_id, target_id):
        self.graph.add_edge(source_id, target_id)

    def find_path(self, source_id, target_id):
        try:
            return nx.shortest_path(
                self.graph,
                source=source_id,
                target=target_id
            )
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def get_nodes(self):
        return list(self.graph.nodes(data=True))

    def get_edges(self):
        return list(self.graph.edges()) 

    def get_graph_summary(self):
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges()
        }


def create_network_graph(resources: dict) -> CloudTopology:
    """Build a CloudTopology graph from discovered cloud resources."""
    topology = CloudTopology()

    # Add VPCs
    for vpc in resources.get("vpcs", []):
        vpc_id = vpc.get("id") or vpc.get("VpcId")
        if not vpc_id:
            continue
        name = None
        for tag in vpc.get("tags", []):
            if isinstance(tag, dict) and tag.get("Key") == "Name":
                name = tag.get("Value")
        topology.add_node(CloudNode(vpc_id, "VPC", name=name))

    # Add Subnets
    for subnet in resources.get("subnets", []):
        subnet_id = subnet.get("id") or subnet.get("SubnetId")
        if not subnet_id:
            continue
        topology.add_node(CloudNode(subnet_id, "Subnet", name=subnet.get("name")))
        vpc_id = subnet.get("vpc_id") or subnet.get("VpcId")
        if vpc_id:
            topology.add_relationship(vpc_id, subnet_id)

    # Add EC2 Instances
    instances = resources.get("instances", resources.get("ec2", []))
    for instance in instances:
        instance_id = instance.get("id") or instance.get("InstanceId")
        if not instance_id:
            continue
        topology.add_node(CloudNode(instance_id, "EC2", name=instance.get("name")))
        subnet_id = instance.get("subnet_id") or instance.get("SubnetId")
        vpc_id = instance.get("vpc_id") or instance.get("VpcId")
        if subnet_id:
            topology.add_relationship(subnet_id, instance_id)
        elif vpc_id:
            topology.add_relationship(vpc_id, instance_id)

        for sg_id in instance.get("security_group_ids", []):
            topology.add_relationship(instance_id, sg_id)

    # Add Security Groups (nodes only – edges come from EC2 instances)
    for sg in resources.get("security_groups", []):
        sg_id = sg.get("id") or sg.get("GroupId")
        if not sg_id:
            continue
        topology.add_node(CloudNode(sg_id, "SecurityGroup", name=sg.get("name") or sg.get("GroupName")))

    return topology