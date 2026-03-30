from diagrams import Diagram, Cluster, Edge
from diagrams.aws.management import OrganizationsAccount, OrganizationsOrganizationalUnit, ControlTower
from diagrams.aws.network import TransitGateway

# Edge styles
governs  = {"style": "solid",  "color": "#2C5F8A", "penwidth": "2"}
scp_edge      = {"style": "dashed", "color": "#C0392B", "penwidth": "1.5"}
scp_edge_full = {"style": "dashed", "color": "#C0392B", "penwidth": "1.5", "label": "Service Control Policies\n& Guardrails\nPermission boundaries\nenforced on all accounts", "decorate": "true"}


def create_exec_org_diagram():
    graph_attrs = {
        "fontsize": "20",
        "fontname": "Segoe UI",
        "labelloc": "t",
        "splines": "ortho",
        "bgcolor": "white",
        "pad": "0.4",
        "ranksep": "0.8",
        "nodesep": "0.5",
    }
    node_attrs = {
        "fontsize": "13",
        "fontname": "Segoe UI",
        "labelloc": "t",
        "width": "2.0",
    }
    ca = {"fontsize": "13", "fontname": "Segoe UI"}
    aa = {"fontsize": "13", "fontname": "Segoe UI", "margin": "4"}

    with Diagram(
        "AWS Account Governance",
        show=False,
        filename="diagrams/exec_org",
        direction="LR",
        graph_attr=graph_attrs,
        node_attr=node_attrs,
    ):
        # ── Root governance ───────────────────────────────────────────────
        with Cluster("Management OU\nRoot governance & policy enforcement", graph_attr=ca):
            with Cluster("Management Account\nBilling · Root · Audit", graph_attr=aa):
                mgmt = OrganizationsOrganizationalUnit("")
            with Cluster("Control Tower\nPolicy Enforcement & Guardrails", graph_attr=aa):
                ct = ControlTower("")
        mgmt >> Edge(**governs) >> ct

        # ── Networking OU ─────────────────────────────────────────────────
        with Cluster("Networking OU\nCentralised connectivity, routing & shared services", graph_attr=ca):
            with Cluster("Core Network Account\nExisting network today", graph_attr=aa):
                core = TransitGateway("")

        # ── Application OU ────────────────────────────────────────────────
        with Cluster("Application OU\nIsolated workload environments", graph_attr=ca):
            with Cluster("IQA Account\nIntegration & QA workloads", graph_attr=aa):
                iqa  = OrganizationsAccount("")
            with Cluster("Sandbox Account\nDevelopment & testing", graph_attr=aa):
                sand = OrganizationsAccount("")

        # ── Platform OU ───────────────────────────────────────────────────
        with Cluster("Platform OU\nShared engineering services", graph_attr=ca):
            with Cluster("Observability & CI Account\nMonitoring · Alerting · Deployments", graph_attr=aa):
                obs  = OrganizationsAccount("")

        # ── Control Tower governs all accounts ────────────────────────────
        ct >> Edge(**scp_edge) >> core
        ct >> Edge(**scp_edge) >> iqa
        ct >> Edge(**scp_edge) >> sand
        ct >> Edge(**scp_edge_full) >> obs


if __name__ == "__main__":
    print("Generating exec org diagram...")
    create_exec_org_diagram()
    print("  diagrams/exec_org.png")
    print("Done.")
