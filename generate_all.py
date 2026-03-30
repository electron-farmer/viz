from main import create_infra_diagram
from multi_account import create_multi_account_diagram
from aws_org import create_aws_org_diagram
from exec_network import create_exec_network_diagram
from exec_multi_account import create_exec_multi_account_diagram
from exec_org import create_exec_org_diagram

if __name__ == "__main__":
    print("Generating all diagrams...")

    create_infra_diagram()
    print("  diagrams/infra_overview.png")

    create_multi_account_diagram()
    print("  diagrams/multi_account_overview.png")

    create_aws_org_diagram()
    print("  diagrams/aws_org.png")

    create_exec_network_diagram()
    print("  diagrams/exec_network.png")

    create_exec_multi_account_diagram()
    print("  diagrams/exec_multi_account.png")

    create_exec_org_diagram()
    print("  diagrams/exec_org.png")

    print("\nDone. All diagrams written to diagrams/")
