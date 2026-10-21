"""Ensure Modal's CLI can discover the app variable in the deployment module.

This is an offline structural regression test, not a live Modal deployment.
"""
import ast
from pathlib import Path
import unittest


class ModalDeployContractTests(unittest.TestCase):
    def test_modal_cli_discovers_app(self):
        file = Path(__file__).resolve().parents[1] / "modal_deploy.py"
        parsed = ast.parse(file.read_text(encoding="utf-8"))
        defined = {
            target.id
            for statement in parsed.body
            if isinstance(statement, ast.Assign)
            for target in statement.targets
            if isinstance(target, ast.Name)
        }
        self.assertIn("app", defined, "Modal CLI expects a top-level 'app'")

        functions = [
            node
            for node in parsed.body
            if isinstance(node, ast.FunctionDef) and node.name == "fastapi_app"
        ]
        self.assertEqual(len(functions), 1)
        decorators = functions[0].decorator_list
        self.assertTrue(
            any(
                isinstance(d, ast.Call)
                and isinstance(d.func, ast.Attribute)
                and isinstance(d.func.value, ast.Name)
                and d.func.value.id == "app"
                and d.func.attr == "function"
                for d in decorators
            ),
            "Modal endpoint must be declared on 'app'",
        )


if __name__ == "__main__":
    unittest.main()
