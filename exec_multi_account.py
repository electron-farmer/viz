from pathlib import Path
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.network import TransitGateway, ELB
from diagrams.aws.compute import EKS
from diagrams.aws.database import RDS
from diagrams.aws.storage import S3
from diagrams.aws.security import IAM
from diagrams.onprem.ci import Jenkins
from diagrams.custom import Custom

_ICONS = Path(__file__).parent / "icons"
OTEL_ICON   = str(_ICONS / "opentelemetry.png")
SIGNOZ_ICON = str(_ICONS / "signoz.png")
IPA_ICON    = str(_ICONS / "freeipa.png")

# Edge styles
hub_spoke  = {"style": "solid",  "color": "#2C5F8A", "penwidth": "3",   "headlabel": "Private network\n(Transit Gateway)", "fontsize": "14"}
blocked    = {"style": "dashed", "color": "#C0392B", "penwidth": "3",   "headlabel": "Isolated — no route", "fontsize": "14"}
telemetry  = {"style": "dashed", "color": "#7F8C8D", "penwidth": "2.5", "headlabel": "Telemetry", "fontsize": "14"}
deploy     = {"style": "dashed", "color": "#27AE60", "penwidth": "2.5", "headlabel": "Deploy", "fontsize": "14"}
db_peer    = {"style": "dashed", "color": "#8E44AD", "penwidth": "2.5", "headlabel": "Private peering", "fontsize": "14"}
internet   = {"style": "solid",  "color": "#E67E22", "penwidth": "2.5", "headlabel": "Internet", "fontsize": "14"}


def create_exec_multi_account_diagram():
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
        "Multi-Account Infrastructure",
        show=False,
        filename="diagrams/exec_multi_account",
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

        # ── Core Network Account ──────────────────────────────────────────
        with Cluster("Core Network Account", graph_attr=aa):
            with Cluster("Transit Gateway\nCentral routing & security boundary", graph_attr=aa):
                tgw = TransitGateway("")
            with Cluster("Identity Server\n(IPA)", graph_attr=aa):
                ipa = Custom("", IPA_ICON)
            tgw >> ipa

        # ── IQA Account ───────────────────────────────────────────────────
        with Cluster("IQA Account", graph_attr=aa):
            with Cluster("Load Balancer", graph_attr=aa):
                lb_iqa = ELB("")
            with Cluster("Application\n(EKS)", graph_attr=aa):
                eks_iqa = EKS("")
            with Cluster("Database", graph_attr=aa):
                db_iqa = RDS("")
            with Cluster("Storage", graph_attr=aa):
                s3_iqa = S3("")
            lb_iqa >> eks_iqa
            eks_iqa >> db_iqa
            eks_iqa >> s3_iqa

        # ── Observability & CI Account ────────────────────────────────────
        with Cluster("Observability & CI Account", graph_attr=aa):
            with Cluster("Management EKS Cluster", graph_attr=aa):
                with Cluster("Metrics & Tracing\n(OpenTelemetry)", graph_attr=aa):
                    otel = Custom("", OTEL_ICON)
                with Cluster("Dashboards & Alerts\n(SigNoz)", graph_attr=aa):
                    signoz = Custom("", SIGNOZ_ICON)
                with Cluster("CI / CD Pipelines\n(Jenkins)", graph_attr=aa):
                    jenkins = Jenkins("")
                otel >> signoz

        # ── Internet ingress ──────────────────────────────────────────────
        users >> Edge(**internet) >> lb_iqa

        # ── TGW connects spokes ───────────────────────────────────────────
        tgw >> Edge(forward=True, reverse=True, **hub_spoke) >> eks_iqa
        tgw >> Edge(forward=True, reverse=True, **hub_spoke) >> otel

        # ── Telemetry to observability ────────────────────────────────────
        eks_iqa >> Edge(**telemetry) >> otel

        # ── CI/CD deploys to environment ─────────────────────────────────
        jenkins >> Edge(**deploy) >> eks_iqa

        # ── MongoDB via private peering through hub ───────────────────────
        tgw >> Edge(forward=True, reverse=True, **db_peer) >> mongodb


if __name__ == "__main__":
    print("Generating exec multi-account diagram...")
    create_exec_multi_account_diagram()
    print("  diagrams/exec_multi_account.png")
    print("Done.")
