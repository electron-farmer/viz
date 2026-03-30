from pathlib import Path
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.network import TransitGateway, ELB
from diagrams.aws.compute import EKS
from diagrams.aws.database import RDS
from diagrams.custom import Custom

_ICONS = Path(__file__).parent / "icons"
OTEL_ICON   = str(_ICONS / "opentelemetry.png")
SIGNOZ_ICON = str(_ICONS / "signoz.png")
IPA_ICON    = str(_ICONS / "freeipa.png")

# Edge styles
hub_spoke  = {"style": "solid",  "color": "#2C5F8A", "penwidth": "3",   "headlabel": "Private network\n(Transit Gateway)", "fontsize": "14"}
db_peer    = {"style": "dashed", "color": "#8E44AD", "penwidth": "2.5", "headlabel": "Private peering", "fontsize": "14"}
internet   = {"style": "solid",  "color": "#E67E22", "penwidth": "2.5", "headlabel": "Internet", "fontsize": "14"}


def create_exec_network_diagram():
    graph_attrs = {
        "fontsize": "20",
        "fontname": "Segoe UI",
        "labelloc": "t",
        "pad": "0.4",
        "splines": "ortho",
        "ranksep": "0.8",
        "nodesep": "0.5",
        "bgcolor": "white",
    }
    node_attrs = {
        "fontsize": "13",
        "fontname": "Segoe UI",
        "labelloc": "t",
        "width": "2.0",
    }

    with Diagram(
        "Non-Production Network Architecture - Hub and Spoke Model",
        show=False,
        filename="diagrams/exec_network",
        direction="LR",
        graph_attr=graph_attrs,
        node_attr=node_attrs,
    ):
        aa = {"fontsize": "15", "fontname": "Segoe UI", "margin": "4"}

        # ── External ──────────────────────────────────────────────────────
        with Cluster("Users\n(Internet)", graph_attr=aa):
            users = ELB("")
        with Cluster("MongoDB Atlas\n(Managed DB)", graph_attr=aa):
            mongodb = RDS("")

        # ── Core Network — Hub ────────────────────────────────────────────
        with Cluster("Core Network  —  HUB", graph_attr=aa):
            with Cluster("Transit Gateway\nCentral routing & isolation\n\n*Note: Application environments/accounts cannot talk\nto one another. They can only communicate with\nMongoDB Atlas and the Management Cluster.", graph_attr=aa):
                tgw = TransitGateway("")

        # ── IQA Environment ───────────────────────────────────────────────
        with Cluster("IQA Environment  —  Account", graph_attr=aa):
            with Cluster("Load Balancer  ", graph_attr=aa):
                lb_iqa = ELB("")
            with Cluster("Application\n(EKS)  ", graph_attr=aa):
                eks_iqa = EKS("")
            lb_iqa >> eks_iqa

        # ── QA Environment ────────────────────────────────────────────────
        with Cluster("QA Environment  —  Account", graph_attr=aa):
            with Cluster("Load Balancer", graph_attr=aa):
                lb_qa = ELB("")
            with Cluster("Application\n(EKS)", graph_attr=aa):
                eks_qa = EKS("")
            lb_qa >> eks_qa

        # ── Sandbox Environment ───────────────────────────────────────────
        with Cluster("Sandbox Environment  —  Account", graph_attr=aa):
            with Cluster("Load Balancer ", graph_attr=aa):
                lb_sb = ELB("")
            with Cluster("Application\n(EKS) ", graph_attr=aa):
                eks_sb = EKS("")
            lb_sb >> eks_sb

        # ── Observability & CI ────────────────────────────────────────────
        with Cluster("Observability & CI  —  Account", graph_attr=aa):
            with Cluster("Management EKS Cluster", graph_attr=aa):
                eks_obs = EKS("")

        # ── Internet ingress ──────────────────────────────────────────────
        users >> Edge(**internet) >> lb_iqa
        users >> Edge(**internet) >> lb_qa
        users >> Edge(**internet) >> lb_sb

        # ── Hub connects spokes ───────────────────────────────────────────
        tgw >> Edge(forward=True, reverse=True, **hub_spoke) >> eks_iqa
        tgw >> Edge(forward=True, reverse=True, **hub_spoke) >> eks_qa
        tgw >> Edge(forward=True, reverse=True, **hub_spoke) >> eks_sb
        tgw >> Edge(forward=True, reverse=True, **hub_spoke) >> eks_obs

        # ── MongoDB via private peering ───────────────────────────────────
        tgw >> Edge(forward=True, reverse=True, **db_peer) >> mongodb


if __name__ == "__main__":
    print("Generating exec network diagram...")
    create_exec_network_diagram()
    print("  diagrams/exec_network.png")
    print("Done.")
