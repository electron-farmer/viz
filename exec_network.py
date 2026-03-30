from pathlib import Path
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.network import TransitGateway, ELB
from diagrams.aws.compute import EKS
from diagrams.aws.database import RDS
from diagrams.aws.storage import S3
from diagrams.onprem.ci import Jenkins
from diagrams.custom import Custom

_ICONS = Path(__file__).parent / "icons"
OTEL_ICON   = str(_ICONS / "opentelemetry.png")
SIGNOZ_ICON = str(_ICONS / "signoz.png")

# Edge styles
traffic    = {"style": "solid",  "color": "#2C5F8A", "penwidth": "2",   "label": "Private traffic\n(Transit Gateway)"}
blocked    = {"style": "dashed", "color": "#C0392B", "penwidth": "2",   "label": "Isolated\n(no direct route)"}
telemetry  = {"style": "dashed", "color": "#7F8C8D", "penwidth": "1.5", "label": "Telemetry"}
deploy     = {"style": "dashed", "color": "#27AE60", "penwidth": "1.5", "label": "Deployments"}
internet   = {"style": "solid",  "color": "#E67E22", "penwidth": "1.5", "label": "Internet (HTTPS)"}
db_peer    = {"style": "dashed", "color": "#8E44AD", "penwidth": "1.5", "label": "Private peering"}


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
        "Network Architecture — Hub & Spoke",
        show=False,
        filename="diagrams/exec_network",
        direction="LR",
        graph_attr=graph_attrs,
        node_attr=node_attrs,
    ):
        # ── External ─────────────────────────────────────────────────────
        with Cluster("External"):
            internet_users = ELB("Users\n(Internet)")
            mongodb = RDS("MongoDB Atlas\n(Managed DB)")

        # ── Core Network Hub ─────────────────────────────────────────────
        with Cluster("Core Network  —  HUB"):
            tgw = TransitGateway("Transit Gateway\nCentral routing & isolation")

        # ── IQA Environment ──────────────────────────────────────────────
        with Cluster("IQA Environment  —  Spoke"):
            lb_iqa  = ELB("Load Balancer")
            eks_iqa = EKS("Application\n(EKS)")
            db_iqa  = RDS("Database")
            s3_iqa  = S3("Storage")
            lb_iqa >> eks_iqa
            eks_iqa >> db_iqa
            eks_iqa >> s3_iqa

        # ── Sandbox Environment ───────────────────────────────────────────
        with Cluster("Sandbox Environment  —  Spoke"):
            lb_sb  = ELB("Load Balancer")
            eks_sb = EKS("Application\n(EKS)")
            db_sb  = RDS("Database")
            s3_sb  = S3("Storage")
            lb_sb >> eks_sb
            eks_sb >> db_sb
            eks_sb >> s3_sb

        # ── Observability & CI ────────────────────────────────────────────
        with Cluster("Observability & CI  —  Spoke"):
            otel    = Custom("Metrics &\nTracing", OTEL_ICON)
            signoz  = Custom("Dashboards\n& Alerts", SIGNOZ_ICON)
            jenkins = Jenkins("CI / CD\nPipelines")
            otel >> signoz

        # ── Internet ingress ──────────────────────────────────────────────
        internet_users >> Edge(**internet) >> lb_iqa
        internet_users >> Edge(**internet) >> lb_sb

        # ── Hub connects spokes ───────────────────────────────────────────
        tgw >> Edge(**traffic) >> eks_iqa
        tgw >> Edge(**traffic) >> eks_sb
        tgw >> Edge(**traffic) >> otel

        # ── IQA ↔ Sandbox: explicitly blocked ────────────────────────────
        eks_iqa >> Edge(**blocked) >> eks_sb

        # ── Telemetry flows to observability ─────────────────────────────
        eks_iqa >> Edge(**telemetry) >> otel
        eks_sb  >> Edge(**telemetry) >> otel

        # ── CI/CD deploys to environments ────────────────────────────────
        jenkins >> Edge(**deploy) >> eks_iqa
        jenkins >> Edge(**deploy) >> eks_sb

        # ── MongoDB via private peering ───────────────────────────────────
        tgw >> Edge(**db_peer) >> mongodb


if __name__ == "__main__":
    print("Generating exec network diagram...")
    create_exec_network_diagram()
    print("  diagrams/exec_network.png")
    print("Done.")
