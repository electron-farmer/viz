from diagrams import Diagram, Cluster
from diagrams.aws.management import OrganizationsAccount

node_attrs = {
    "shape": "box",
    "style": "rounded,filled",
    "fillcolor": "#C9D9E8",
    "color": "#2C5F8A",
    "penwidth": "1.5",
    "labelloc": "t",
}
ca = {"margin": "4"}

with Diagram("Padding Test", show=False, filename="diagrams/padding_test", node_attr=node_attrs):
    with Cluster("Outer A", graph_attr=ca):
        a = OrganizationsAccount("Node A")
    with Cluster("Outer B", graph_attr=ca):
        b = OrganizationsAccount("Node B")
