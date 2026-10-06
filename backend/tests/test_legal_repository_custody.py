"""Offline custody regression: no app settings import, services or model execution."""
import ast
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[2]
PROJECT = "legal-compliance-regulatory-workbench"


def load_yaml(path):
    # BaseLoader preserves GitHub's `on` key instead of YAML 1.1's boolean coercion.
    return yaml.load((ROOT / path).read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


def setting_defaults():
    tree = ast.parse((ROOT / "backend/app/core/config.py").read_text(encoding="utf-8"))
    settings = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Settings")
    result = {}
    for node in settings.body:
        if not isinstance(node, ast.AnnAssign):
            continue
        value = node.value
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "Field":
            value = next((kw.value for kw in value.keywords if kw.arg == "default"), None)
        if isinstance(value, (ast.Constant, ast.List)):
            result[node.target.id] = ast.literal_eval(value)
    return result


class LegalCustodyTests(unittest.TestCase):
    def test_compose_resources_do_not_share_old_project_or_ports(self):
        compose = load_yaml("infra/docker-compose.yml")
        self.assertEqual(compose.get("name"), PROJECT)
        postgres = compose["services"]["postgres"]
        self.assertEqual(postgres["environment"]["POSTGRES_DB"], "legal_compliance_workbench")
        self.assertEqual(postgres["ports"], ["127.0.0.1:55432:5432"])
        self.assertEqual(compose["services"]["qdrant"]["ports"],
                         ["127.0.0.1:16333:6333", "127.0.0.1:16334:6334"])
        for path, name in (("infra/docker-compose.auth-test.yml", PROJECT + "-auth-test"),
                           ("infra/docker-compose.ui-api-test.yml", PROJECT + "-ui-api-test")):
            profile = load_yaml(path)
            self.assertEqual(profile.get("name"), name)
            self.assertEqual(profile["networks"]["default"]["internal"], "true")
            self.assertNotIn("ports", profile["services"]["postgres"])

    def test_native_defaults_and_template_agree_on_isolated_endpoints(self):
        defaults = setting_defaults()
        template = dict(line.split("=", 1) for line in (ROOT / ".env.example").read_text().splitlines()
                        if line and not line.startswith("#"))
        for field, key in (("database_url", "DATABASE_URL"), ("qdrant_url", "QDRANT_URL"),
                           ("qdrant_collection", "QDRANT_COLLECTION"), ("model_base_url", "MODEL_BASE_URL")):
            self.assertEqual(defaults[field], template[key])
        database = urlsplit(defaults["database_url"])
        self.assertEqual((database.hostname, database.port, database.path),
                         ("127.0.0.1", 55432, "/legal_compliance_workbench"))
        self.assertEqual(urlsplit(defaults["qdrant_url"]).port, 16333)
        self.assertEqual(defaults["qdrant_collection"], "legal_knowledge_chunks_v1")
        self.assertEqual(urlsplit(defaults["model_base_url"]).port, 21434)
        self.assertEqual(defaults["cors_origins"], json.loads(template["WORKBENCH_CORS_ORIGINS"]))
        self.assertEqual({urlsplit(origin).port for origin in defaults["cors_origins"]}, {15173})

    def test_backend_requires_explicit_dedicated_model_endpoint(self):
        services = load_yaml("infra/docker-compose.backend.yml")["services"]
        self.assertEqual(services["backend"]["ports"], ["127.0.0.1:18000:8000"])
        for name in ("backend", "speech"):
            self.assertEqual(services[name]["image"], "legal-compliance-workbench-backend:py311-cpu")
        env = services["backend"]["environment"]
        self.assertTrue(env["MODEL_BASE_URL"].startswith("${BACKEND_MODEL_BASE_URL:?"))
        self.assertTrue(env["MODEL_ALLOWED_HOSTS"].startswith("${BACKEND_MODEL_ALLOWED_HOSTS:?"))

    def test_ci_cannot_use_old_runners_or_live_inference(self):
        ci = load_yaml(".github/workflows/regression.yml")
        self.assertEqual(set(ci["on"]), {"workflow_dispatch"})
        self.assertEqual(set(ci["jobs"]), {"backend", "frontend"})
        for job in ci["jobs"].values():
            self.assertEqual(job["runs-on"], "ubuntu-latest")
            self.assertEqual(job["if"], "github.repository == 'loktrishal-05/legal-compliance-regulatory-workbench'")
            self.assertNotIn("environment", job)
            for step in job["steps"]:
                self.assertNotIn("--execute", step.get("run", ""))
        self.assertEqual(ci["jobs"]["backend"]["env"]["WORKBENCH_LIVE_REGRESSION"], "0")

    def test_compose_backup_rejects_foreign_database_before_commands(self):
        from scripts.backup import compose_command
        from sqlalchemy.engine import make_url
        for target in ("postgresql://postgres@127.0.0.1:5432/sovereign_workbench",
                       "postgresql://postgres@127.0.0.1:55432/another_application",
                       "postgresql://postgres@foreign.internal:55432/legal_compliance_workbench",
                       "postgresql://postgres@127.0.0.1/legal_compliance_workbench",
                       "postgresql://postgres@127.0.0.1:55432/legal_compliance_workbench?options=-csearch_path=foreign"):
            with self.subTest(target=target), self.assertRaises(ValueError):
                compose_command(make_url(target))
        command = compose_command(make_url("postgresql://postgres@127.0.0.1:55432/legal_compliance_workbench"))
        self.assertEqual(command[command.index("--project-name") + 1], PROJECT)
        self.assertEqual(command[command.index("-d") + 1], "legal_compliance_workbench")

    def test_compose_backup_rejects_foreign_qdrant_before_any_io(self):
        from scripts import backup
        config = SimpleNamespace(database_url="postgresql://postgres@127.0.0.1:55432/legal_compliance_workbench",
                                 qdrant_url="http://127.0.0.1:6333", data_root=ROOT / "data", model_root=ROOT / "models")
        with patch.dict(sys.modules, {"app.core.config": SimpleNamespace(settings=config)}), \
                patch.object(backup, "validate_destination", return_value=ROOT / "never-created"), \
                patch("app.core.locality.require_private_resolution") as network, \
                patch.object(backup.subprocess, "run") as process:
            with self.assertRaisesRegex(ValueError, "isolated Qdrant"):
                backup.create(ROOT / "never-created", quiesced=True, compose=True)
            network.assert_not_called()
            process.assert_not_called()


if __name__ == "__main__":
    unittest.main()
