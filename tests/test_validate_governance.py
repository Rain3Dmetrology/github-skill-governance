from __future__ import annotations

import base64
import importlib.util
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_governance", REPO_ROOT / "scripts" / "validate_governance.py"
)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


class GovernanceValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = json.loads(
            (REPO_ROOT / "tests/fixtures/validator/cases.json").read_text(encoding="utf-8")
        )
        completed = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "ls-files", "-z"],
            check=True,
            stdout=subprocess.PIPE,
        )
        cls.tracked = [item for item in completed.stdout.decode("utf-8").split("\0") if item]

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(REPO_ROOT / "tests" / ".validator-work", ignore_errors=True)

    def copy_repo(self) -> tuple[Path, list[str]]:
        # Keep fixture writes inside tests: some restricted Windows sandboxes
        # deny the private ACL that tempfile.TemporaryDirectory creates.
        workspace = REPO_ROOT / "tests" / ".validator-work" / self._testMethodName
        if workspace.exists():
            shutil.rmtree(workspace)
        root = workspace / "repo"
        root.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, workspace, True)
        tracked = list(self.tracked)
        # Files created by this branch but not yet in the index are part of the
        # candidate tree under test.
        for required in (
            "scripts/validate_governance.py",
            "tests/test_validate_governance.py",
            "tests/fixtures/validator/cases.json",
            ".github/governance/repo-policy.schema.json",
            validator.BROKER_SCHEMA_PATH,
            validator.BROKER_CLI_PATH,
            validator.BROKER_ENVIRONMENT_PATH,
            validator.BROKER_WORKFLOW_PATH,
            ".github/CODEOWNERS",
            validator.MAIN_RULESET_PATH,
            validator.TAG_RULESET_PATH,
        ):
            if (REPO_ROOT / required).is_file() and required not in tracked:
                tracked.append(required)
        for relative in tracked:
            source = REPO_ROOT / relative
            if source.is_file():
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        return root, tracked

    @staticmethod
    def codes(result: dict[str, object]) -> set[str]:
        return {error["code"] for error in result["errors"]}  # type: ignore[index]

    def test_current_repository_passes(self) -> None:
        result = validator.validate_repository(REPO_ROOT)
        self.assertTrue(result["ok"], json.dumps(result, indent=2, ensure_ascii=False))

    def test_unknown_policy_field_fails_closed(self) -> None:
        root, tracked = self.copy_repo()
        policy = root / validator.POLICY_PATH
        text = policy.read_text(encoding="utf-8")
        policy.write_text(
            text.replace(
                "schema_version: 2",
                f"schema_version: 2\n{self.cases['unknown_policy_field']}: true",
                1,
            ),
            encoding="utf-8",
        )
        result = validator.validate_repository(root, tracked)
        self.assertFalse(result["ok"])
        self.assertIn("policy-field-unknown", self.codes(result))

    def test_unpinned_external_action_is_rejected(self) -> None:
        root, tracked = self.copy_repo()
        workflow = root / ".github/workflows/negative.yml"
        workflow.parent.mkdir(parents=True, exist_ok=True)
        workflow.write_text(
            "name: negative\n"
            "on: pull_request\n"
            "permissions:\n  contents: read\n"
            "jobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n"
            f"      - uses: {self.cases['unpinned_action']}\n",
            encoding="utf-8",
        )
        tracked.append(".github/workflows/negative.yml")
        result = validator.validate_repository(root, tracked)
        self.assertFalse(result["ok"])
        self.assertIn("workflow-action-pin", self.codes(result))

    def test_only_frozen_checkout_sha_is_allowed(self) -> None:
        root, tracked = self.copy_repo()
        workflow = root / ".github/workflows/positive.yml"
        workflow.parent.mkdir(parents=True, exist_ok=True)
        workflow.write_text(
            "name: positive\n"
            "on: pull_request\n"
            "permissions:\n  contents: read\n"
            "jobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n"
            f"      - uses: actions/checkout@{self.cases['checkout_sha']}\n"
            "        with:\n"
            "          persist-credentials: false\n",
            encoding="utf-8",
        )
        tracked.append(".github/workflows/positive.yml")
        result = validator.validate_repository(root, tracked)
        self.assertNotIn("workflow-action-pin", self.codes(result))
        self.assertNotIn("workflow-checkout-credentials", self.codes(result))

    def test_checkout_credentials_must_not_persist(self) -> None:
        root, tracked = self.copy_repo()
        workflow = root / ".github/workflows/credentials.yml"
        workflow.parent.mkdir(parents=True, exist_ok=True)
        workflow.write_text(
            "name: credentials\n"
            "on: pull_request\n"
            "permissions:\n  contents: read\n"
            "jobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n"
            f"      - uses: actions/checkout@{self.cases['checkout_sha']}\n",
            encoding="utf-8",
        )
        tracked.append(".github/workflows/credentials.yml")
        result = validator.validate_repository(root, tracked)
        self.assertFalse(result["ok"])
        self.assertIn("workflow-checkout-credentials", self.codes(result))

    def test_secret_signature_and_sensitive_filename_are_rejected(self) -> None:
        root, tracked = self.copy_repo()
        secret_file = root / "credentials.json"
        secret_file.write_text(
            json.dumps({"token": base64.b64decode(self.cases["encoded_fake_github_token"]).decode("ascii")}),
            encoding="utf-8",
        )
        tracked.append("credentials.json")
        result = validator.validate_repository(root, tracked)
        self.assertFalse(result["ok"])
        self.assertTrue({"sensitive-filename", "secret-signature"}.issubset(self.codes(result)))

    def test_release_command_and_write_permission_are_rejected(self) -> None:
        root, tracked = self.copy_repo()
        workflow = root / ".github/workflows/release.yml"
        workflow.parent.mkdir(parents=True, exist_ok=True)
        workflow.write_text(
            "name: release\n"
            "on: workflow_dispatch\n"
            "permissions:\n  contents: write\n"
            "jobs:\n  publish:\n    runs-on: ubuntu-latest\n    steps:\n"
            "      - run: gh release create v1.0.0\n",
            encoding="utf-8",
        )
        tracked.append(".github/workflows/release.yml")
        result = validator.validate_repository(root, tracked)
        self.assertFalse(result["ok"])
        self.assertTrue({"release-command", "workflow-permissions"}.issubset(self.codes(result)))

    def test_new_or_unknown_permission_scope_fails_closed(self) -> None:
        root, tracked = self.copy_repo()
        workflow = root / ".github/workflows/permission-scope.yml"
        workflow.parent.mkdir(parents=True, exist_ok=True)
        workflow.write_text(
            "name: permission-scope\n"
            "on: pull_request\n"
            "permissions:\n"
            "  contents: read\n"
            "  attestations: write\n"
            "jobs:\n"
            "  check:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - run: true\n",
            encoding="utf-8",
        )
        tracked.append(".github/workflows/permission-scope.yml")
        result = validator.validate_repository(root, tracked)
        self.assertFalse(result["ok"])
        self.assertIn("workflow-permissions", self.codes(result))

    def test_local_action_and_manifest_are_rejected(self) -> None:
        root, tracked = self.copy_repo()
        workflow = root / ".github/workflows/local-action.yml"
        action = root / ".github/actions/local/action.yml"
        workflow.parent.mkdir(parents=True, exist_ok=True)
        action.parent.mkdir(parents=True, exist_ok=True)
        workflow.write_text(
            "name: local-action\n"
            "on: pull_request\n"
            "permissions:\n  contents: read\n"
            "jobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n"
            "      - uses: ./.github/actions/local\n",
            encoding="utf-8",
        )
        action.write_text(
            "name: local\nruns:\n  using: composite\n  steps:\n"
            "    - shell: bash\n      run: true\n",
            encoding="utf-8",
        )
        tracked.extend([".github/workflows/local-action.yml", ".github/actions/local/action.yml"])
        result = validator.validate_repository(root, tracked)
        self.assertFalse(result["ok"])
        self.assertIn("local-action-forbidden", self.codes(result))

    def test_enforced_policy_cannot_keep_activation_ready_state(self) -> None:
        root, tracked = self.copy_repo()
        policy = root / validator.POLICY_PATH
        policy.write_text(
            policy.read_text(encoding="utf-8").replace(
                "current_state: enforced",
                "current_state: ready-for-remote-activation",
                1,
            ),
            encoding="utf-8",
        )
        result = validator.validate_repository(root, tracked)
        self.assertFalse(result["ok"])
        self.assertTrue({"policy-invariant", "schema-validation"}.issubset(self.codes(result)))

    def test_activation_approved_requires_observed_app_id(self) -> None:
        root, tracked = self.copy_repo()
        policy = root / validator.POLICY_PATH
        policy.write_text(
            policy.read_text(encoding="utf-8").replace(
                "required_check_integration_id: 15368",
                "required_check_integration_id: null",
                1,
            ),
            encoding="utf-8",
        )
        result = validator.validate_repository(root, tracked)
        self.assertFalse(result["ok"])
        self.assertTrue({"policy-state", "schema-validation"}.issubset(self.codes(result)))

    def test_tag_ruleset_must_cover_every_tag(self) -> None:
        root, tracked = self.copy_repo()
        ruleset = root / validator.TAG_RULESET_PATH
        ruleset.write_text(
            ruleset.read_text(encoding="utf-8").replace('"~ALL"', '"refs/tags/v*"', 1),
            encoding="utf-8",
        )
        result = validator.validate_repository(root, tracked)
        self.assertFalse(result["ok"])
        self.assertIn("ruleset-tag-state", self.codes(result))

    def test_broker_manifest_contract_drift_fails_closed(self) -> None:
        root, tracked = self.copy_repo()
        schema_path = root / validator.BROKER_SCHEMA_PATH
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        schema["properties"]["authorization"]["properties"]["max_run_age_seconds"]["const"] = 3600
        schema_path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
        result = validator.validate_repository(root, tracked)
        self.assertFalse(result["ok"])
        self.assertIn("broker-schema-invariant", self.codes(result))

    def test_broker_environment_drift_fails_closed(self) -> None:
        root, tracked = self.copy_repo()
        environment_path = root / validator.BROKER_ENVIRONMENT_PATH
        environment = json.loads(environment_path.read_text(encoding="utf-8"))
        environment["environment"]["apiPayload"]["prevent_self_review"] = True
        environment_path.write_text(json.dumps(environment, indent=2) + "\n", encoding="utf-8")
        result = validator.validate_repository(root, tracked)
        self.assertFalse(result["ok"])
        self.assertIn("broker-environment-desired-state", self.codes(result))

    def test_broker_cli_contract_drift_fails_closed(self) -> None:
        root, tracked = self.copy_repo()
        contract_path = root / validator.BROKER_CLI_PATH
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract["commands"]["consume"]["mutation"] = "generic-api"
        contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
        result = validator.validate_repository(root, tracked)
        self.assertFalse(result["ok"])
        self.assertIn("broker-cli-contract", self.codes(result))

    def test_broker_workflow_is_required_and_canonical(self) -> None:
        self.assertTrue((REPO_ROOT / validator.BROKER_WORKFLOW_PATH).is_file())
        root, tracked = self.copy_repo()
        workflow = root / validator.BROKER_WORKFLOW_PATH
        workflow.write_text(
            workflow.read_text(encoding="utf-8").replace(
                "permissions: {}",
                "permissions: write-all",
                1,
            ),
            encoding="utf-8",
        )
        result = validator.validate_repository(root, tracked)
        self.assertFalse(result["ok"])
        self.assertIn("broker-workflow-canonical", self.codes(result))

    def test_broker_workflow_cannot_be_removed(self) -> None:
        root, tracked = self.copy_repo()
        workflow = root / validator.BROKER_WORKFLOW_PATH
        workflow.unlink()
        tracked.remove(validator.BROKER_WORKFLOW_PATH)
        result = validator.validate_repository(root, tracked)
        self.assertFalse(result["ok"])
        self.assertTrue(
            {"broker-workflow-missing", "workflow-inventory"}.issubset(
                self.codes(result)
            )
        )

    def test_broker_workflow_permission_or_route_drift_fails_closed(self) -> None:
        rewrites = {
            "ungated-consume": (
                "    environment:\n      name: c-authorization",
                "",
            ),
            "extra-write": (
                "      pull-requests: read",
                "      pull-requests: write",
            ),
            "generic-input": (
                "      expected_head_sha:",
                "      endpoint:\n        description: Generic endpoint\n        required: true\n        type: string\n      expected_head_sha:",
            ),
            "second-operation": (
                "--expected-head-sha \"$BROKER_EXPECTED_HEAD_SHA\"",
                "--expected-head-sha \"$BROKER_EXPECTED_HEAD_SHA\" --operation arbitrary",
            ),
            "secret-injection": (
                "          GITHUB_TOKEN: ${{ github.token }}",
                "          GITHUB_TOKEN: ${{ secrets.ADMIN_TOKEN }}",
            ),
            "variable-injection": (
                "          BROKER_PR_NUMBER: ${{ inputs.pr_number }}",
                "          BROKER_PR_NUMBER: ${{ vars.PR_NUMBER }}",
            ),
        }
        for name, (old, new) in rewrites.items():
            with self.subTest(name=name):
                root, tracked = self.copy_repo()
                workflow = root / validator.BROKER_WORKFLOW_PATH
                text = workflow.read_text(encoding="utf-8")
                self.assertIn(old, text)
                workflow.write_text(text.replace(old, new, 1), encoding="utf-8")
                result = validator.validate_repository(root, tracked)
                self.assertFalse(result["ok"])
                self.assertIn("broker-workflow-canonical", self.codes(result))

    def test_yaml_equivalent_workflow_rewrites_fail_closed(self) -> None:
        rewrites = {
            "quoted-permissions": (
                "permissions:\n  contents: read",
                '"permissions": write-all',
            ),
            "quoted-uses": (
                "        uses: actions/checkout@" + validator.CHECKOUT_SHA,
                '        "uses": actions/setup-python@v5',
            ),
            "quoted-release-trigger": (
                "  workflow_dispatch:",
                '  "release":',
            ),
        }
        for name, (old, new) in rewrites.items():
            with self.subTest(name=name):
                root, tracked = self.copy_repo()
                workflow = root / validator.WORKFLOW_PATH
                workflow.write_text(
                    workflow.read_text(encoding="utf-8").replace(old, new, 1),
                    encoding="utf-8",
                )
                result = validator.validate_repository(root, tracked)
                self.assertFalse(result["ok"])
                self.assertIn("workflow-canonical", self.codes(result))

    def test_extensionless_shebang_release_executor_is_rejected(self) -> None:
        root, tracked = self.copy_repo()
        executor = root / "release-task"
        executor.write_text(
            "#!/bin/sh\n" + "gh release " + "create release-1\n",
            encoding="utf-8",
        )
        tracked.append("release-task")
        result = validator.validate_repository(root, tracked)
        self.assertFalse(result["ok"])
        self.assertIn("release-command", self.codes(result))

    def test_cli_json_and_exit_code_are_stable(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts/validate_governance.py"), "--root", str(REPO_ROOT)],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(payload["schema_version"], 1)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["errors"], [])


if __name__ == "__main__":
    unittest.main()
