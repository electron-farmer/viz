from pathlib import Path
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import EKS
from diagrams.aws.database import RDS
from diagrams.aws.network import (
    ELB, NATGateway, InternetGateway,
    RouteTable, TransitGateway, TransitGatewayAttachment, VPCPeering,
)
from diagrams.aws.security import SecretsManager
from diagrams.aws.storage import S3
from diagrams.custom import Custom
from diagrams.k8s.compute import Pod
from diagrams.onprem.ci import Jenkins

_ICONS = Path(__file__).parent / "icons"
OTEL_ICON   = str(_ICONS / "opentelemetry.png")
SIGNOZ_ICON = str(_ICONS / "signoz.png")
IPA_ICON    = str(_ICONS / "freeipa.png")

# Edge style helpers
tgw_attach  = {"style": "solid",  "color": "royalblue"}
data_flow   = {"style": "dashed", "color": "gray", "fontsize": "15"}
deploy_flow = {"style": "dashed", "color": "green", "label": "deploy", "fontsize": "15"}
peer_edge   = {"style": "dashed", "color": "darkorange", "label": "VPC Peering", "fontsize": "15"}


def create_infra_diagram():
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
        "fontsize": "15",
        "fontname": "Segoe UI",
        "labelloc": "t",
        "width": "2.0",
    }
    ca = {"fontsize": "15", "fontname": "Segoe UI"}
    aa = {"fontsize": "15", "fontname": "Segoe UI", "margin": "4"}

    with Diagram(
        "Infrastructure Overview — Hub & Spoke (Transit Gateway)",
        show=False,
        filename="diagrams/infra_overview",
        direction="LR",
        graph_attr=graph_attrs,
        node_attr=node_attrs,
    ):
        # ── External: MongoDB (third-party managed VPC) ──────────────────
        with Cluster("MongoDB Atlas\n(Third-Party Managed VPC)", graph_attr=ca):
            with Cluster("MongoDB", graph_attr=aa):
                mongodb = RDS("")

        # ── Core Network (Hub) ────────────────────────────────────────────
        with Cluster("Core Network  [10.0.0.0/16]  — HUB", graph_attr=ca):
            with Cluster("IPA\nIdentity Server", graph_attr=aa):
                ipa = Custom("", IPA_ICON)

            with Cluster("Transit Gateway", graph_attr=aa):
                tgw = TransitGateway("")

            with Cluster(
                "TGW Route Table\n"
                "IQA → Core, Obs\n"
                "Sandbox → Core, Obs\n"
                "Obs → IQA, Sandbox, Core\n"
                "Core → all\n"
                "IQA ↛ Sandbox (blocked)",
                graph_attr=aa,
            ):
                tgw_rt = RouteTable("")

            with Cluster(
                "Core RT\n"
                "10.10.0.0/16 → TGW\n"
                "10.20.0.0/16 → TGW\n"
                "10.30.0.0/16 → TGW\n"
                "10.40.0.0/16 → MongoDB peer",
                graph_attr=aa,
            ):
                rt_core = RouteTable("")

            with Cluster("Peering → MongoDB", graph_attr=aa):
                peer_core_mongo = VPCPeering("")

        # ── IQA VPC (Spoke) ───────────────────────────────────────────────
        with Cluster("IQA VPC  [10.10.0.0/16]  — Spoke", graph_attr=ca):
            with Cluster("TGW Attachment", graph_attr=aa):
                tgw_att_iqa = TransitGatewayAttachment("")
            with Cluster(
                "IQA RT\n"
                "0.0.0.0/0 → IGW\n"
                "10.0.0.0/8 → TGW\n"
                "(no route to Sandbox)",
                graph_attr=aa,
            ):
                rt_iqa = RouteTable("")
            with Cluster("Public Subnet", graph_attr=ca):
                with Cluster("Internet Gateway", graph_attr=aa):
                    igw = InternetGateway("")
                with Cluster("NAT Gateway", graph_attr=aa):
                    nat = NATGateway("")
                with Cluster("Load Balancer\n(Ingress)", graph_attr=aa):
                    lb = ELB("")
            with Cluster("Private Subnet", graph_attr=ca):
                with Cluster("EKS Cluster", graph_attr=aa):
                    with Cluster("EKS Control Plane", graph_attr=aa):
                        eks_iqa = EKS("")
                    with Cluster("Nginx", graph_attr=aa):
                        nginx_iqa = Pod("")
                    with Cluster("ArgoCD", graph_attr=aa):
                        argocd_iqa = Pod("")
                    with Cluster("OTEL Collector", graph_attr=aa):
                        otel_collector_iqa = Pod("")
                    with Cluster("AuthZ", graph_attr=aa):
                        authz_iqa = Pod("")
                    with Cluster("UtilService", graph_attr=aa):
                        utilservice_iqa = Pod("")
                    with Cluster("WebService", graph_attr=aa):
                        webservice_iqa = Pod("")
                    with Cluster("Cert Manager", graph_attr=aa):
                        cert_manager_iqa = Pod("")
                    with Cluster("External Secrets", graph_attr=aa):
                        external_secrets_iqa = Pod("")
                    with Cluster("Linkerd", graph_attr=aa):
                        linkerd_iqa = Pod("")
                with Cluster("RDS Instance", graph_attr=aa):
                    rds_iqa = RDS("")
                with Cluster("App Bucket", graph_attr=aa):
                    s3_app = S3("")
                with Cluster("Secrets Bucket", graph_attr=aa):
                    s3_secrets = S3("")
                with Cluster("Artifacts Bucket", graph_attr=aa):
                    s3_art = S3("")
                with Cluster("AWS Secrets Manager", graph_attr=aa):
                    secrets_iqa = SecretsManager("")

        # ── Sandbox VPC (Spoke) ───────────────────────────────────────────
        with Cluster("Sandbox VPC  [10.20.0.0/16]  — Spoke", graph_attr=ca):
            with Cluster("TGW Attachment", graph_attr=aa):
                tgw_att_sb = TransitGatewayAttachment("")
            with Cluster(
                "Sandbox RT\n"
                "0.0.0.0/0 → IGW\n"
                "10.0.0.0/8 → TGW\n"
                "(no route to IQA)",
                graph_attr=aa,
            ):
                rt_sb = RouteTable("")
            with Cluster("Public Subnet", graph_attr=ca):
                with Cluster("Internet Gateway", graph_attr=aa):
                    igw_sb = InternetGateway("")
                with Cluster("NAT Gateway", graph_attr=aa):
                    nat_sb = NATGateway("")
                with Cluster("Load Balancer\n(Ingress)", graph_attr=aa):
                    lb_sb = ELB("")
            with Cluster("Private Subnet", graph_attr=ca):
                with Cluster("EKS Cluster", graph_attr=aa):
                    with Cluster("EKS Control Plane", graph_attr=aa):
                        eks_sb = EKS("")
                    with Cluster("Nginx", graph_attr=aa):
                        nginx_sb = Pod("")
                    with Cluster("ArgoCD", graph_attr=aa):
                        argocd_sb = Pod("")
                    with Cluster("OTEL Collector", graph_attr=aa):
                        otel_collector_sb = Pod("")
                    with Cluster("AuthZ", graph_attr=aa):
                        authz_sb = Pod("")
                    with Cluster("UtilService", graph_attr=aa):
                        utilservice_sb = Pod("")
                    with Cluster("WebService", graph_attr=aa):
                        webservice_sb = Pod("")
                    with Cluster("Cert Manager", graph_attr=aa):
                        cert_manager_sb = Pod("")
                    with Cluster("External Secrets", graph_attr=aa):
                        external_secrets_sb = Pod("")
                    with Cluster("Linkerd", graph_attr=aa):
                        linkerd_sb = Pod("")
                with Cluster("RDS Instance", graph_attr=aa):
                    rds_sb = RDS("")
                with Cluster("App Bucket", graph_attr=aa):
                    s3_app_sb = S3("")
                with Cluster("Secrets Bucket", graph_attr=aa):
                    s3_secrets_sb = S3("")
                with Cluster("Artifacts Bucket", graph_attr=aa):
                    s3_art_sb = S3("")
                with Cluster("AWS Secrets Manager", graph_attr=aa):
                    secrets_sb = SecretsManager("")

        # ── Observability & CI VPC (Spoke) ────────────────────────────────
        with Cluster("Observability & CI VPC  [10.30.0.0/16]  — Spoke", graph_attr=ca):
            with Cluster("TGW Attachment", graph_attr=aa):
                tgw_att_obs = TransitGatewayAttachment("")
            with Cluster(
                "Obs RT\n"
                "10.0.0.0/8 → TGW",
                graph_attr=aa,
            ):
                rt_obs = RouteTable("")
            with Cluster("EKS Cluster", graph_attr=ca):
                with Cluster("OpenTelemetry\nCollector", graph_attr=aa):
                    otel = Custom("", OTEL_ICON)
                with Cluster("SigNoz", graph_attr=aa):
                    signoz = Custom("", SIGNOZ_ICON)
                with Cluster("Jenkins Workers", graph_attr=aa):
                    jenkins = Jenkins("")
            with Cluster("AWS Secrets Manager", graph_attr=aa):
                secrets_obs = SecretsManager("")

        # ── Internal VPC wiring ───────────────────────────────────────────
        igw >> lb >> nginx_iqa >> webservice_iqa
        nat >> igw
        eks_iqa >> argocd_iqa
        argocd_iqa >> [webservice_iqa, authz_iqa, utilservice_iqa]
        linkerd_iqa >> [webservice_iqa, authz_iqa, utilservice_iqa]
        external_secrets_iqa >> [webservice_iqa, authz_iqa, utilservice_iqa]
        cert_manager_iqa >> nginx_iqa
        [webservice_iqa, authz_iqa, utilservice_iqa] >> otel_collector_iqa
        webservice_iqa >> rds_iqa
        webservice_iqa >> [s3_app, s3_secrets, s3_art]
        external_secrets_iqa >> secrets_iqa
        rt_iqa >> nat

        igw_sb >> lb_sb >> nginx_sb >> webservice_sb
        nat_sb >> igw_sb
        eks_sb >> argocd_sb
        argocd_sb >> [webservice_sb, authz_sb, utilservice_sb]
        linkerd_sb >> [webservice_sb, authz_sb, utilservice_sb]
        external_secrets_sb >> [webservice_sb, authz_sb, utilservice_sb]
        cert_manager_sb >> nginx_sb
        [webservice_sb, authz_sb, utilservice_sb] >> otel_collector_sb
        webservice_sb >> rds_sb
        webservice_sb >> [s3_app_sb, s3_secrets_sb, s3_art_sb]
        external_secrets_sb >> secrets_sb
        rt_sb >> nat_sb

        # ── TGW attachments (spokes → hub) ────────────────────────────────
        tgw_att_iqa >> Edge(**tgw_attach) >> tgw
        tgw_att_sb  >> Edge(**tgw_attach) >> tgw
        tgw_att_obs >> Edge(**tgw_attach) >> tgw
        tgw_rt      >> Edge(**tgw_attach) >> tgw
        rt_core     >> Edge(**tgw_attach) >> tgw

        # Route tables point traffic to TGW attachment
        rt_iqa >> Edge(**tgw_attach) >> tgw_att_iqa
        rt_sb  >> Edge(**tgw_attach) >> tgw_att_sb
        rt_obs >> Edge(**tgw_attach) >> tgw_att_obs

        # ── Core Network → MongoDB (peering, not TGW) ─────────────────────
        rt_core >> Edge(**peer_edge) >> peer_core_mongo >> mongodb

        # ── Observability data flows (through TGW) ────────────────────────
        otel_collector_iqa >> Edge(**data_flow, label="traces/metrics/logs") >> otel
        otel_collector_sb  >> Edge(**data_flow, label="traces/metrics/logs") >> otel
        otel >> signoz

        # ── Jenkins deploys (through TGW) ─────────────────────────────────
        jenkins >> Edge(**deploy_flow) >> argocd_iqa
        jenkins >> Edge(**deploy_flow) >> argocd_sb
        jenkins >> secrets_obs

        # ── IPA reachable from spokes via TGW ─────────────────────────────
        tgw >> Edge(**tgw_attach) >> ipa


if __name__ == "__main__":
    print("Generating diagrams...")
    create_infra_diagram()
    print("  infra_overview.png")
    print("Done.")
