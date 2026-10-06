"""Identity contract without loading private settings, native DLLs or services."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ProductIdentityTests(unittest.TestCase):
    def test_process_health_identifies_only_the_legal_backend(self):
        tree = ast.parse((ROOT / "backend/app/api/routes/health.py").read_text(encoding="utf-8"))
        health = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "health")
        health.decorator_list = []
        namespace = {}
        exec(compile(ast.Module(body=[health], type_ignores=[]), "<health-contract>", "exec"), namespace)
        self.assertEqual(namespace["health"](), {
            "status": "ok", "service": "legal-compliance-regulatory-workbench-backend"})

    def test_openapi_product_title_matches_the_master_report(self):
        tree = ast.parse((ROOT / "backend/app/main.py").read_text(encoding="utf-8"))
        app = next(node for node in tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == "app" for target in node.targets))
        title = next(value.value for value in app.value.keywords if value.arg == "title")
        self.assertEqual(ast.literal_eval(title), "Legal & Regulatory Assurance Platform")


if __name__ == "__main__":
    unittest.main()
