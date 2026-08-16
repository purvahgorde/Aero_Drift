import networkx as nx


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
        except nx.NetworkXNoPath:
            return None

  