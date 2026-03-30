from diagrams import Diagram, Cluster, Edge
from diagrams.aws.management import OrganizationsAccount, ControlTower
from diagrams.aws.network import TransitGateway
from diagrams.aws.compute import EKS
from diagrams.aws.devtools import Codebuild
from diagrams.onprem.monitoring import Grafana

# Edge styles
governs  = {"style": "solid",  "color": "#2C5F8A", "penwidth": "2"}
scp_edge = {"style": "dashed", "color": "#C0392B", "penwidth": "1.5", "label": "SCPs & Guardrails"}


def create_exec_org_diagram():
    graph_attrs = {
        "fontsize": "22",
        "fontname": "Helvetica",
        "pad": "1.5",
        "splines": "ortho",
        "ranksep": "1.6",
        "nodesep": "1.2",
        "bgcolor": "white",
    }
    node_attrs = {
        "fontsize": "18",
        "fontname": "Helvetica",
    }

    with Diagram(
        "AWS Account Governance",
        show=False,
        filename="diagrams/exec_org",
        direction="TB",
        graph_attr=graph_attrs,
        node_attr=node_attrs,
    ):
        # ── Root governance ───────────────────────────────────────────────
        mgmt = OrganizationsAccount("Management Account\nBilling · Root · Audit")
        ct   = ControlTower("AWS Control Tower\nPolicy Enforcement")
        mgmt >> Edge(**governs) >> ct

        # ── Networking OU ─────────────────────────────────────────────────
        with Cluster("Networking OU\nCentralised connectivity & routing"):
            core = TransitGateway(
                "Core Network\nTransit Gateway Hub\nShared with all accounts"
            )

        # ── Application OU ────────────────────────────────────────────────
        with Cluster("Application OU\nIsolated workload environments"):
            iqa  = OrganizationsAccount("IQA Environment\nIntegration & QA workloads")
            sand = OrganizationsAccount("Sandbox Environment\nDevelopment & testing")

        # ── Platform OU ───────────────────────────────────────────────────
        with Cluster("Platform OU\nShared engineering services"):
            obs  = OrganizationsAccount("Observability & CI\nMonitoring · Alerting · Deployments")

        # ── Control Tower governs all accounts ────────────────────────────
        ct >> Edge(**scp_edge) >> core
        ct >> Edge(**scp_edge) >> iqa
        ct >> Edge(**scp_edge) >> sand
        ct >> Edge(**scp_edge) >> obs

        # ── Core network shared to application accounts ───────────────────
        core >> Edge(
            style="dashed", color="#7D3C98", penwidth="1.5",
            label="Shared network (RAM)"
        ) >> iqa
        core >> Edge(
            style="dashed", color="#7D3C98", penwidth="1.5",
        ) >> sand
        core >> Edge(
            style="dashed", color="#7D3C98", penwidth="1.5",
        ) >> obs


if __name__ == "__main__":
    print("Generating exec org diagram...")
    create_exec_org_diagram()
    print("  diagrams/exec_org.png")
    print("Done.")
