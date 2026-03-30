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
hub_spoke  = {"style": "solid",  "color": "#2C5F8A", "penwidth": "2",   "label": "Private network\n(Transit Gateway)"}
blocked    = {"style": "dashed", "color": "#C0392B", "penwidth": "2",   "label": "Isolated — no route"}
telemetry  = {"style": "dashed", "color": "#7F8C8D", "penwidth": "1.5", "label": "Telemetry"}
deploy     = {"style": "dashed", "color": "#27AE60", "penwidth": "1.5", "label": "Deploy"}
db_peer    = {"style": "dashed", "color": "#8E44AD", "penwidth": "1.5", "label": "Private peering"}
internet   = {"style": "solid",  "color": "#E67E22", "penwidth": "1.5", "label": "Internet"}


def create_exec_multi_account_diagram():
    graph_attrs = {
        "fontsize": "22",
        "fontname": "Helvetica",
        "pad": "1.8",
        "splines": "ortho",
        "ranksep": "2.0",
        "nodesep": "1.6",
        "bgcolor": "white",
    }
    node_attrs = {
        "fontsize": "18",
        "fontname": "Helvetica",
    }

    with Diagram(
        "Multi-Account Infrastructure — Hub & Spoke",
        show=False,
        filename="diagrams/exec_multi_account",
        direction="TB",
        graph_attr=graph_attrs,
        node_attr=node_attrs,
    ):
        # ── External ──────────────────────────────────────────────────────
        users   = ELB("Users\n(Internet)")
        mongodb = RDS("MongoDB Atlas\n(Managed DB)")

        # ── Networking OU — Hub ───────────────────────────────────────────
        with Cluster("Networking OU"):
            with Cluster("Core Network Account"):
                tgw = TransitGateway("Transit Gateway\nCentral routing & security boundary")
                ipa = Custom("Identity Server\n(IPA)", IPA_ICON)
                tgw >> ipa

        # ── Application OU — Spokes ───────────────────────────────────────
        with Cluster("Application OU"):

            with Cluster("IQA Account"):
                lb_iqa  = ELB("Load Balancer")
                eks_iqa = EKS("Application")
                db_iqa  = RDS("Database")
                s3_iqa  = S3("Storage")
                lb_iqa >> eks_iqa
                eks_iqa >> db_iqa
                eks_iqa >> s3_iqa

            with Cluster("Sandbox Account"):
                lb_sb  = ELB("Load Balancer")
                eks_sb = EKS("Application")
                db_sb  = RDS("Database")
                s3_sb  = S3("Storage")
                lb_sb >> eks_sb
                eks_sb >> db_sb
                eks_sb >> s3_sb

        # ── Platform OU ───────────────────────────────────────────────────
        with Cluster("Platform OU"):
            with Cluster("Observability & CI Account"):
                otel    = Custom("Metrics & Tracing\n(OpenTelemetry)", OTEL_ICON)
                signoz  = Custom("Dashboards & Alerts\n(SigNoz)", SIGNOZ_ICON)
                jenkins = Jenkins("CI / CD Pipelines\n(Jenkins)")
                otel >> signoz

        # ── Internet ingress ──────────────────────────────────────────────
        users >> Edge(**internet) >> lb_iqa
        users >> Edge(**internet) >> lb_sb

        # ── TGW connects spokes ───────────────────────────────────────────
        tgw >> Edge(**hub_spoke) >> eks_iqa
        tgw >> Edge(**hub_spoke) >> eks_sb
        tgw >> Edge(**hub_spoke) >> otel

        # ── IQA ↔ Sandbox: enforced isolation ────────────────────────────
        eks_iqa >> Edge(**blocked) >> eks_sb

        # ── Telemetry to observability ────────────────────────────────────
        eks_iqa >> Edge(**telemetry) >> otel
        eks_sb  >> Edge(**telemetry) >> otel

        # ── CI/CD deploys to both environments ───────────────────────────
        jenkins >> Edge(**deploy) >> eks_iqa
        jenkins >> Edge(**deploy) >> eks_sb

        # ── MongoDB via private peering through hub ───────────────────────
        tgw >> Edge(**db_peer) >> mongodb


if __name__ == "__main__":
    print("Generating exec multi-account diagram...")
    create_exec_multi_account_diagram()
    print("  diagrams/exec_multi_account.png")
    print("Done.")
