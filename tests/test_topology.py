from app.graph.topology import CloudTopology


topology = CloudTopology()

print(topology.graph)
print("Nodes:", topology.graph.number_of_nodes())
print("Edges:", topology.graph.number_of_edges())