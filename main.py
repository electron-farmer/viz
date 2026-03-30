from pathlib import Path
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import EKS
from diagrams.aws.database import RDS
from diagrams.aws.network import (
    ELB, NATGateway, InternetGateway,
    RouteTable, TransitGateway, TransitGatewayAttachment, VPCPeering,
)
from diagrams.aws.storage import S3
from diagrams.custom import Custom
from diagrams.onprem.ci import Jenkins

_ICONS = Path(__file__).parent / "icons"
OTEL_ICON   = str(_ICONS / "opentelemetry.png")
SIGNOZ_ICON = str(_ICONS / "signoz.png")
IPA_ICON    = str(_ICONS / "freeipa.png")

# Edge style helpers
tgw_attach  = {"style": "solid",  "color": "royalblue"}
tgw_blocked = {"style": "dashed", "color": "red",   "label": "TGW RT: denied\n(no propagation)"}
data_flow   = {"style": "dashed", "color": "gray"}
deploy_flow = {"style": "dashed", "color": "green", "label": "deploy"}
peer_edge   = {"style": "dashed", "color": "darkorange", "label": "VPC Peering"}


def create_infra_diagram():
    graph_attrs = {"fontsize": "20", "fontname": "Segoe UI", "labelloc": "t", "pad": "0.4", "splines": "ortho", "ranksep": "0.8", "nodesep": "0.5"}
    node_attrs  = {"fontsize": "13", "fontname": "Segoe UI", "labelloc": "t", "width": "2.0"}

    with Diagram(
        "Infrastructure Overview — Hub & Spoke (Transit Gateway)",
        show=False,
        filename="diagrams/infra_overview",
        direction="LR",
        graph_attr=graph_attrs,
        node_attr=node_attrs,
    ):
        # ── External: MongoDB (third-party managed VPC) ──────────────────
        with Cluster("MongoDB Atlas\n(Third-Party Managed VPC)"):
            mongodb = RDS("MongoDB")

        # ── Core Network (Hub) ────────────────────────────────────────────
        with Cluster("Core Network  [10.0.0.0/16]  — HUB"):
            ipa = Custom("IPA\nIdentity Server", IPA_ICON)

            tgw = TransitGateway(
                "Transit Gateway\n"
                "— TGW Route Table —\n"
                "IQA → Core, Obs\n"
                "Sandbox → Core, Obs\n"
                "Obs → IQA, Sandbox, Core\n"
                "Core → all\n"
                "IQA ↛ Sandbox (blocked)"
            )

            rt_core = RouteTable(
                "Core RT\n"
                "10.10.0.0/16 → TGW\n"
                "10.20.0.0/16 → TGW\n"
                "10.30.0.0/16 → TGW\n"
                "10.40.0.0/16 → MongoDB peer"
            )

            peer_core_mongo = VPCPeering("Peering → MongoDB")

        # ── IQA VPC (Spoke) ───────────────────────────────────────────────
        with Cluster("IQA VPC  [10.10.0.0/16]  — Spoke"):
            tgw_att_iqa = TransitGatewayAttachment("TGW Attachment")
            rt_iqa = RouteTable(
                "IQA RT\n"
                "0.0.0.0/0 → IGW\n"
                "10.0.0.0/8 → TGW\n"
                "(no route to Sandbox)"
            )
            with Cluster("Public Subnet"):
                igw = InternetGateway("Internet Gateway")
                nat = NATGateway("NAT Gateway")
                lb  = ELB("Load Balancer\n(Ingress)")
            with Cluster("Private Subnet"):
                eks_iqa = EKS("EKS Cluster")
                rds_iqa = RDS("RDS Instance")
                s3_app  = S3("App Bucket")
                s3_logs = S3("Logs Bucket")
                s3_art  = S3("Artifacts Bucket")

        # ── Sandbox VPC (Spoke) ───────────────────────────────────────────
        with Cluster("Sandbox VPC  [10.20.0.0/16]  — Spoke"):
            tgw_att_sb = TransitGatewayAttachment("TGW Attachment")
            rt_sb = RouteTable(
                "Sandbox RT\n"
                "0.0.0.0/0 → IGW\n"
                "10.0.0.0/8 → TGW\n"
                "(no route to IQA)"
            )
            with Cluster("Public Subnet "):
                igw_sb = InternetGateway("Internet Gateway")
                nat_sb = NATGateway("NAT Gateway")
                lb_sb  = ELB("Load Balancer\n(Ingress)")
            with Cluster("Private Subnet "):
                eks_sb     = EKS("EKS Cluster")
                rds_sb     = RDS("RDS Instance")
                s3_app_sb  = S3("App Bucket")
                s3_logs_sb = S3("Logs Bucket")
                s3_art_sb  = S3("Artifacts Bucket")

        # ── Observability & CI VPC (Spoke) ────────────────────────────────
        with Cluster("Observability & CI VPC  [10.30.0.0/16]  — Spoke"):
            tgw_att_obs = TransitGatewayAttachment("TGW Attachment")
            rt_obs = RouteTable(
                "Obs RT\n"
                "10.0.0.0/8 → TGW"
            )
            with Cluster("EKS Cluster"):
                otel    = Custom("OpenTelemetry\nCollector", OTEL_ICON)
                signoz  = Custom("SigNoz", SIGNOZ_ICON)
                jenkins = Jenkins("Jenkins Workers")

        # ── Internal VPC wiring ───────────────────────────────────────────
        igw >> lb >> eks_iqa
        nat >> igw
        eks_iqa >> rds_iqa
        eks_iqa >> [s3_app, s3_logs, s3_art]
        rt_iqa >> nat

        igw_sb >> lb_sb >> eks_sb
        nat_sb >> igw_sb
        eks_sb >> rds_sb
        eks_sb >> [s3_app_sb, s3_logs_sb, s3_art_sb]
        rt_sb >> nat_sb

        # ── TGW attachments (spokes → hub) ────────────────────────────────
        tgw_att_iqa >> Edge(**tgw_attach) >> tgw
        tgw_att_sb  >> Edge(**tgw_attach) >> tgw
        tgw_att_obs >> Edge(**tgw_attach) >> tgw
        rt_core     >> Edge(**tgw_attach) >> tgw

        # Route tables point traffic to TGW attachment
        rt_iqa >> Edge(**tgw_attach) >> tgw_att_iqa
        rt_sb  >> Edge(**tgw_attach) >> tgw_att_sb
        rt_obs >> Edge(**tgw_attach) >> tgw_att_obs

        # ── Core Network → MongoDB (peering, not TGW) ─────────────────────
        rt_core >> Edge(**peer_edge) >> peer_core_mongo >> mongodb

        # ── IQA ↔ Sandbox: explicitly blocked at TGW route table ─────────
        tgw_att_iqa >> Edge(**tgw_blocked) >> tgw_att_sb

        # ── Observability data flows (through TGW) ────────────────────────
        eks_iqa >> Edge(**data_flow, label="traces/metrics/logs") >> otel
        eks_sb  >> Edge(**data_flow, label="traces/metrics/logs") >> otel
        otel >> signoz

        # ── Jenkins deploys (through TGW) ─────────────────────────────────
        jenkins >> Edge(**deploy_flow) >> eks_iqa
        jenkins >> Edge(**deploy_flow) >> eks_sb

        # ── IPA reachable from spokes via TGW ─────────────────────────────
        tgw >> Edge(**tgw_attach) >> ipa


if __name__ == "__main__":
    print("Generating diagrams...")
    create_infra_diagram()
    print("  infra_overview.png")
    print("Done.")
