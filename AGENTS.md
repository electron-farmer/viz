# AGENTS.md

## Project Overview

This project generates AWS infrastructure architecture diagrams using the [`diagrams`](https://diagrams.mingrammer.com/) Python library. It produces PNG outputs that visually document Hub & Spoke network topologies across single-VPC and multi-account AWS environments.

## Repository Structure

```
viz/
├── main.py               # Single-account Hub & Spoke (Transit Gateway) diagram
├── multi_account.py      # Multi-account Hub & Spoke (AWS Organizations) diagram
├── icons/                # Custom PNG icons (OpenTelemetry, SigNoz, FreeIPA)
├── diagrams/             # Generated PNG outputs
│   ├── infra_overview.png
│   ├── multi_account_overview.png
│   ├── serverless_infra.png
│   └── web_app_infra.png
├── pyproject.toml        # Project metadata and dependencies (managed with uv)
└── uv.lock               # Locked dependency versions
```

## Running the Diagrams

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Install dependencies
uv sync

# Generate single-account diagram
uv run python main.py

# Generate multi-account diagram
uv run python multi_account.py
```

Generated PNGs are saved to the `diagrams/` folder.

## Architecture Patterns

**`main.py` — Single-Account Hub & Spoke**
Models a Transit Gateway-based network with the following VPCs:
- **Core Network (Hub)** `10.0.0.0/16` — Transit Gateway, IPA Identity Server, VPC Peering to MongoDB Atlas
- **IQA VPC (Spoke)** `10.10.0.0/16` — EKS, RDS, S3; internet-facing via IGW + NAT
- **Sandbox VPC (Spoke)** `10.20.0.0/16` — mirrors IQA; traffic to IQA is blocked at the TGW route table
- **Observability & CI VPC (Spoke)** `10.30.0.0/16` — OpenTelemetry, SigNoz, Jenkins

**`multi_account.py` — Multi-Account Hub & Spoke**
Extends the single-account model to a full AWS Organizations structure:
- **Management Account** — Billing root + Control Tower guardrails/SCPs
- **Networking OU** — Core Network Account owns the Transit Gateway, shared via AWS RAM
- **Application OU** — Separate IQA and Sandbox accounts; cross-account IAM isolation enforced
- **Platform OU** — Observability & CI account with read-only cross-account IAM trust

## Key Conventions

- **Edge styles**: solid blue = TGW attachment, dashed gray = data flow, dashed green = deploy, dashed red = blocked route, dashed orange = VPC peering, dotted gold = IAM trust, dashed purple = RAM share
- **Output filenames** are set via the `filename=` parameter in each `Diagram()` call — no extension needed
- **Custom icons** live in `icons/` and are referenced by relative path from the script's working directory; run scripts from the project root
- `show=False` prevents the diagram from auto-opening after generation

## Adding a New Diagram

1. Create a new `.py` file (e.g., `serverless.py`)
2. Import node types from `diagrams.aws.*` or other providers
3. Define a function that wraps the diagram in a `with Diagram(...)` block
4. Call the function in `if __name__ == "__main__"`
5. Save the output PNG to `diagrams/`

## Dependencies

| Package    | Purpose                              |
|------------|--------------------------------------|
| `diagrams` | Infrastructure-as-code diagram library |

Requires Python ≥ 3.14. Graphviz must also be installed on the system (`brew install graphviz` / `apt install graphviz`).
