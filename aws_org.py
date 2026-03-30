from diagrams import Diagram, Cluster, Edge
from diagrams.aws.management import (
    Organizations, OrganizationsAccount, OrganizationsOrganizationalUnit, ControlTower,
)
from diagrams.aws.security import IAM
from diagrams.aws.network import TransitGateway

# Edge styles
governs  = {"style": "solid",  "color": "steelblue", "label": "governs"}
scp      = {"style": "dashed", "color": "firebrick",  "label": "SCPs / guardrails"}
org_link = {"style": "solid",  "color": "dimgray"}
ram      = {"style": "dashed", "color": "purple",     "label": "RAM share"}
trust    = {"style": "dotted", "color": "goldenrod",  "label": "cross-account\nIAM trust"}


def create_aws_org_diagram():
    graph_attrs = {
        "fontsize": "16",
        "pad": "1.2",
        "splines": "ortho",
        "ranksep": "1.5",
        "nodesep": "1.0",
    }

    with Diagram(
        "AWS Organizations — Account & OU Structure",
        show=False,
        filename="diagrams/aws_org",
        direction="TB",
        graph_attr=graph_attrs,
    ):
        # ── Root ─────────────────────────────────────────────────────────
        mgmt = OrganizationsAccount("Management Account\n(Billing & Org root)")
        ct   = ControlTower("Control Tower\n(guardrails & SCPs)")
        mgmt >> Edge(**governs) >> ct

        # ── Networking OU ─────────────────────────────────────────────────
        with Cluster("Networking OU"):
            net_acct = OrganizationsAccount("Core Network Account\n[10.0.0.0/16]\nHub — Transit Gateway")
            tgw      = TransitGateway("Transit Gateway\n(RAM shared to spokes)")
            net_acct >> Edge(**org_link) >> tgw

        # ── Application OU ────────────────────────────────────────────────
        with Cluster("Application OU"):
            iqa_acct = OrganizationsAccount("IQA Account\n[10.10.0.0/16]\nSpoke — EKS / RDS / S3")
            sb_acct  = OrganizationsAccount("Sandbox Account\n[10.20.0.0/16]\nSpoke — EKS / RDS / S3")
            iqa_iam  = IAM("IAM\n(IQA-scoped roles)")
            sb_iam   = IAM("IAM\n(Sandbox-scoped roles)")
            iqa_acct >> Edge(**org_link) >> iqa_iam
            sb_acct  >> Edge(**org_link) >> sb_iam

        # ── Platform OU ───────────────────────────────────────────────────
        with Cluster("Platform OU"):
            obs_acct = OrganizationsAccount("Observability & CI Account\n[10.30.0.0/16]\nSpoke — OTel / SigNoz / Jenkins")
            obs_iam  = IAM("IAM\n(read-only cross-acct roles)")
            obs_acct >> Edge(**org_link) >> obs_iam

        # ── Control Tower governs all accounts ────────────────────────────
        ct >> Edge(**scp) >> net_acct
        ct >> Edge(**scp) >> iqa_acct
        ct >> Edge(**scp) >> sb_acct
        ct >> Edge(**scp) >> obs_acct

        # ── TGW shared to spoke accounts via RAM ──────────────────────────
        tgw >> Edge(**ram) >> iqa_acct
        tgw >> Edge(**ram) >> sb_acct
        tgw >> Edge(**ram) >> obs_acct

        # ── Cross-account IAM trust ───────────────────────────────────────
        obs_iam >> Edge(**trust) >> iqa_iam
        obs_iam >> Edge(**trust) >> sb_iam


if __name__ == "__main__":
    print("Generating AWS Organizations diagram...")
    create_aws_org_diagram()
    print("  diagrams/aws_org.png")
    print("Done.")
