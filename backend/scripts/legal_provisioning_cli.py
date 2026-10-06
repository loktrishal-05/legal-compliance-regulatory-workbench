"""Explicit, audited operator commands for legal bootstrap and legacy mapping (no HTTP endpoint).

  python -m scripts.legal_provisioning_cli bootstrap --operator NAME --organization ORG --workspace WS --admin-user UUID
  python -m scripts.legal_provisioning_cli map-legacy --operator NAME --workspace UUID --document UUID --classification internal
"""
import argparse
from uuid import UUID


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    boot = sub.add_parser("bootstrap")
    boot.add_argument("--operator", required=True)
    boot.add_argument("--organization", required=True)
    boot.add_argument("--workspace", required=True)
    boot.add_argument("--admin-user", required=True, type=UUID)
    boot.add_argument("--admin-clearance", default="internal")
    legacy = sub.add_parser("map-legacy")
    legacy.add_argument("--operator", required=True)
    legacy.add_argument("--workspace", required=True, type=UUID)
    legacy.add_argument("--document", required=True, type=UUID)
    legacy.add_argument("--classification", required=True)
    legacy.add_argument("--matter", type=UUID)
    args = parser.parse_args(argv)

    from app.db.session import SessionLocal  # settings/DB only after arguments validate
    from app.services import legal_provisioning as prov
    with SessionLocal() as db:
        if args.command == "bootstrap":
            result = prov.bootstrap_workspace(db, operator_label=args.operator, organization_name=args.organization,
                                              workspace_name=args.workspace, admin_user_id=args.admin_user,
                                              admin_clearance=args.admin_clearance)
            message = f"workspace {result.id} organization {result.organization_id}"
        else:
            result = prov.map_legacy_document(db, operator_label=args.operator, workspace_id=args.workspace,
                                              document_id=args.document, classification=args.classification,
                                              matter_id=args.matter)
            message = f"document {result.document_id} -> workspace {result.workspace_id}"
        db.commit()
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
