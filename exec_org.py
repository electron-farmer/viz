from diagrams import Diagram, Cluster, Edge
from diagrams.aws.management import OrganizationsAccount, OrganizationsOrganizationalUnit, ControlTower
from diagrams.aws.network import TransitGateway

# Edge styles
governs  = {"style": "solid",  "color": "#2C5F8A", "penwidth": "2"}
scp_edge = {"style": "dashed", "color": "#C0392B", "penwidth": "1.5", "label": "SCPs & Guardrails"}


def create_exec_org_diagram():
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
        "fontsize": "11",
        "fontname": "Segoe UI",
        "fixedsize": "true",
        "width": "1.2",
        "height": "1.2",
    }
    with Diagram(
        "AWS Account Governance",
        show=False,
        filename="diagrams/exec_org",
        direction="LR",
        graph_attr=graph_attrs,
        node_attr=node_attrs,
    ):
        # ── Root governance ───────────────────────────────────────────────
        mgmt = OrganizationsOrganizationalUnit("Management Account\nBilling · Root · Audit")
        ct   = ControlTower("AWS Control Tower\nPolicy Enforcement")
        mgmt >> Edge(**governs) >> ct

        # ── Networking OU ─────────────────────────────────────────────────
        ca = {"margin": "12", "fontsize": "13", "fontname": "Segoe UI"}

        with Cluster("Networking OU", graph_attr=ca):
            core = TransitGateway("Transit Gateway\nCentral routing hub")

        # ── Application OU ────────────────────────────────────────────────
        with Cluster("Application OU\nIsolated workload environments", graph_attr=ca):
            iqa  = OrganizationsAccount("IQA Environment\nIntegration & QA workloads")
            sand = OrganizationsAccount("Sandbox Environment\nDevelopment & testing")

        # ── Platform OU ───────────────────────────────────────────────────
        with Cluster("Platform OU\nShared engineering services", graph_attr=ca):
            obs  = OrganizationsAccount("Observability & CI\nMonitoring · Alerting · Deployments")

        # ── Control Tower governs all accounts ────────────────────────────
        ct >> Edge(**scp_edge) >> core
        ct >> Edge(**scp_edge) >> iqa
        ct >> Edge(**scp_edge) >> sand
        ct >> Edge(**scp_edge) >> obs



if __name__ == "__main__":
    print("Generating exec org diagram...")
    create_exec_org_diagram()
    print("  diagrams/exec_org.png")
    print("Done.")
