from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import EKS
from diagrams.aws.database import RDS
from diagrams.aws.network import (
    ELB, NATGateway, InternetGateway,
    RouteTable, TransitGateway, TransitGatewayAttachment, VPCPeering,
)
from diagrams.aws.storage import S3
from diagrams.aws.security import IAM
from diagrams.custom import Custom
from diagrams.onprem.ci import Jenkins

OTEL_ICON   = "icons/opentelemetry.png"
SIGNOZ_ICON = "icons/signoz.png"
IPA_ICON    = "icons/freeipa.png"

tgw_attach  = {"style": "solid",  "color": "royalblue"}
tgw_blocked = {"style": "dashed", "color": "red",    "label": "TGW RT: denied"}
data_flow   = {"style": "dashed", "color": "gray",   "label": "traces/metrics/logs"}
deploy_flow = {"style": "dashed", "color": "green",  "label": "deploy"}
ram_share   = {"style": "dashed", "color": "purple", "label": "RAM share"}
peer_edge   = {"style": "dashed", "color": "darkorange", "label": "VPC Peering"}
trust_edge  = {"style": "dotted", "color": "goldenrod",  "label": "cross-account\nIAM trust"}


def create_multi_account_diagram():
    graph_attrs = {"fontsize": "15", "pad": "1.2", "splines": "ortho"}

    with Diagram(
        "Multi-Account Infrastructure — Hub & Spoke",
        show=False,
        filename="diagrams/multi_account_overview",
        direction="LR",
        graph_attr=graph_attrs,
    ):
        # ── Networking OU (Hub) ───────────────────────────────────────────
        with Cluster("Networking OU"):

            with Cluster("Core Network Account\n[10.0.0.0/16]  — HUB"):
                ipa = Custom("IPA\nIdentity Server", IPA_ICON)
                tgw = TransitGateway(
                    "Transit Gateway\n"
                    "TGW RT:\n"
                    "IQA → Core, Obs\n"
                    "Sandbox → Core, Obs\n"
                    "Obs → IQA, Sandbox, Core\n"
                    "IQA ↛ Sandbox"
                )
                rt_core = RouteTable("Core RT\n10.10/16 → TGW\n10.20/16 → TGW\n10.30/16 → TGW\n10.40/16 → Mongo peer")
                peer_mongo = VPCPeering("Peering → MongoDB")
                rt_core >> tgw

        # ── Application OU (Spokes) ───────────────────────────────────────
        with Cluster("Application OU"):

            with Cluster("IQA Account\n[10.10.0.0/16]  — Spoke"):
                iqa_iam = IAM("Account IAM\n(IQA-scoped roles only)")
                tgw_att_iqa = TransitGatewayAttachment("TGW Attachment\n(RAM shared TGW)")
                rt_iqa = RouteTable("IQA RT\n0.0.0.0/0 → IGW\n10.0.0.0/8 → TGW")
                with Cluster("Public Subnet"):
                    igw  = InternetGateway("IGW")
                    nat  = NATGateway("NAT")
                    lb   = ELB("Load Balancer")
                with Cluster("Private Subnet"):
                    eks_iqa = EKS("EKS Cluster")
                    rds_iqa = RDS("RDS")
                    s3_app  = S3("App")
                    s3_logs = S3("Logs")
                    s3_art  = S3("Artifacts")

            with Cluster("Sandbox Account\n[10.20.0.0/16]  — Spoke"):
                sb_iam = IAM("Account IAM\n(Sandbox-scoped roles only)")
                tgw_att_sb = TransitGatewayAttachment("TGW Attachment\n(RAM shared TGW)")
                rt_sb = RouteTable("Sandbox RT\n0.0.0.0/0 → IGW\n10.0.0.0/8 → TGW")
                with Cluster("Public Subnet "):
                    igw_sb = InternetGateway("IGW")
                    nat_sb = NATGateway("NAT")
                    lb_sb  = ELB("Load Balancer")
                with Cluster("Private Subnet "):
                    eks_sb     = EKS("EKS Cluster")
                    rds_sb     = RDS("RDS")
                    s3_app_sb  = S3("App")
                    s3_logs_sb = S3("Logs")
                    s3_art_sb  = S3("Artifacts")

        # ── Platform OU ───────────────────────────────────────────────────
        with Cluster("Platform OU"):

            with Cluster("Observability & CI Account\n[10.30.0.0/16]  — Spoke"):
                obs_iam = IAM("Account IAM\n(read-only cross-acct roles)")
                tgw_att_obs = TransitGatewayAttachment("TGW Attachment\n(RAM shared TGW)")
                rt_obs = RouteTable("Obs RT\n10.0.0.0/8 → TGW")
                with Cluster("EKS Cluster"):
                    otel    = Custom("OpenTelemetry\nCollector", OTEL_ICON)
                    signoz  = Custom("SigNoz", SIGNOZ_ICON)
                    jenkins = Jenkins("Jenkins Workers")

        # ── External: MongoDB Atlas ───────────────────────────────────────
        with Cluster("MongoDB Atlas\n(Third-Party Managed VPC)"):
            mongodb = RDS("MongoDB")

        # ── Internal VPC wiring ───────────────────────────────────────────
        igw >> lb >> eks_iqa
        nat >> igw
        rt_iqa >> nat
        eks_iqa >> rds_iqa
        eks_iqa >> [s3_app, s3_logs, s3_art]

        igw_sb >> lb_sb >> eks_sb
        nat_sb >> igw_sb
        rt_sb >> nat_sb
        eks_sb >> rds_sb
        eks_sb >> [s3_app_sb, s3_logs_sb, s3_art_sb]

        rt_obs >> otel

        # ── TGW shared via RAM to spoke accounts ──────────────────────────
        tgw >> Edge(**ram_share) >> tgw_att_iqa
        tgw >> Edge(**ram_share) >> tgw_att_sb
        tgw >> Edge(**ram_share) >> tgw_att_obs

        # ── Spoke route tables → TGW attachments ─────────────────────────
        rt_iqa >> Edge(**tgw_attach) >> tgw_att_iqa
        rt_sb  >> Edge(**tgw_attach) >> tgw_att_sb
        rt_obs >> Edge(**tgw_attach) >> tgw_att_obs

        # ── IQA ↔ Sandbox blocked at TGW RT ──────────────────────────────
        tgw_att_iqa >> Edge(**tgw_blocked) >> tgw_att_sb

        # ── Core Network → MongoDB ────────────────────────────────────────
        rt_core >> Edge(**peer_edge) >> peer_mongo >> mongodb

        # ── IPA reachable from all spokes via TGW ─────────────────────────
        tgw >> Edge(**tgw_attach) >> ipa

        # ── Observability data flows ──────────────────────────────────────
        eks_iqa >> Edge(**data_flow) >> otel
        eks_sb  >> Edge(**data_flow) >> otel
        otel >> signoz

        # ── Jenkins deploys across accounts ───────────────────────────────
        jenkins >> Edge(**deploy_flow) >> eks_iqa
        jenkins >> Edge(**deploy_flow) >> eks_sb

        # ── Cross-account IAM trust (Obs reads from App accounts) ─────────
        obs_iam >> Edge(**trust_edge) >> iqa_iam
        obs_iam >> Edge(**trust_edge) >> sb_iam


if __name__ == "__main__":
    print("Generating multi-account diagram...")
    create_multi_account_diagram()
    print("  multi_account_overview.png")
    print("Done.")
