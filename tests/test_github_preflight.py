from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "github_preflight.py"
FIXTURE = ROOT / "tests" / "fixtures" / "preflight" / "happy"
READ_ONLY_FIXTURE = ROOT / "tests" / "fixtures" / "preflight" / "read_only"
SPEC = importlib.util.spec_from_file_location("github_preflight", SCRIPT)
assert SPEC and SPEC.loader
github_preflight = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = github_preflight
SPEC.loader.exec_module(github_preflight)


class GithubPreflightTests(unittest.TestCase):
    def base_args(self, fixture: Path = FIXTURE) -> list[str]:
        return [
            "--owner",
            "Rain3Dmetrology",
            "--repo",
            "github-skill-governance",
            "--expected-account",
            "Rain3Dmetrology",
            "--expected-repository-id",
            "123456789",
            "--expected-default-branch",
            "main",
            "--expected-target-sha",
            "1111111111111111111111111111111111111111",
            "--operation-class",
            "R",
            "--required-permission",
            "read",
            "--fixture-dir",
            str(fixture),
        ]

    def invoke(self, args: list[str]) -> tuple[int, dict]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = github_preflight.main(args)
        return result, json.loads(output.getvalue())

    def test_happy_offline_preflight_is_explicitly_not_live(self) -> None:
        result, payload = self.invoke(self.base_args())
        self.assertEqual(result, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(
            payload["evidence"],
            {
                "authorization_verified": False,
                "credential_transport": "offline-fixture",
                "credential_type": "opaque-not-inspected",
                "live_verified": False,
                "mode": "offline_fixture",
                "purpose": "identity-and-permission-evidence-only",
            },
        )
        self.assertEqual(payload["observed"]["permission"], "admin")
        self.assertNotIn("token", json.dumps(payload).lower())

    def test_repository_id_mismatch_fails_closed(self) -> None:
        args = self.base_args()
        args[args.index("123456789")] = "987654321"
        result, payload = self.invoke(args)
        self.assertEqual(result, 1)
        self.assertEqual(payload["errors"][0]["code"], "repository_id_mismatch")

    def test_target_sha_mismatch_fails_closed(self) -> None:
        args = self.base_args()
        args[args.index("1111111111111111111111111111111111111111")] = "2" * 40
        result, payload = self.invoke(args)
        self.assertEqual(result, 1)
        self.assertEqual(payload["errors"][0]["code"], "target_sha_mismatch")

    def test_account_mismatch_fails_closed(self) -> None:
        args = self.base_args()
        args[args.index("Rain3Dmetrology", args.index("--expected-account"))] = "DifferentAccount"
        result, payload = self.invoke(args)
        self.assertEqual(result, 1)
        self.assertEqual(payload["errors"][0]["code"], "account_mismatch")

    def test_permission_mismatch_fails_closed(self) -> None:
        args = self.base_args(READ_ONLY_FIXTURE)
        args[args.index("read", args.index("--required-permission"))] = "write"
        result, payload = self.invoke(args)
        self.assertEqual(result, 1)
        self.assertIn("permission_insufficient", [item["code"] for item in payload["errors"]])

    def test_offline_fixture_cannot_prove_c_class_preflight(self) -> None:
        args = self.base_args()
        args[args.index("R", args.index("--operation-class"))] = "C"
        args[args.index("read", args.index("--required-permission"))] = "write"
        result, payload = self.invoke(args)
        self.assertEqual(result, 1)
        codes = [item["code"] for item in payload["errors"]]
        self.assertIn("offline_evidence_forbidden", codes)
        self.assertFalse(payload["evidence"]["authorization_verified"])
        self.assertEqual(
            payload["evidence"]["purpose"],
            "identity-and-permission-evidence-only",
        )

    def test_missing_arguments_exit_one_with_json(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as raised:
            github_preflight.main([])
        self.assertEqual(raised.exception.code, 1)
        self.assertEqual(json.loads(output.getvalue())["errors"][0]["code"], "invalid_arguments")

    def test_malicious_owner_is_rejected_before_subprocess(self) -> None:
        args = self.base_args()
        args[args.index("Rain3Dmetrology")] = "owner;whoami"
        with mock.patch.object(github_preflight.subprocess, "run") as run:
            result, payload = self.invoke(args)
        self.assertEqual(result, 1)
        self.assertEqual(payload["errors"][0]["code"], "invalid_owner")
        run.assert_not_called()

    def test_gh_api_uses_argument_array_and_never_a_shell(self) -> None:
        response = subprocess.CompletedProcess(args=[], returncode=0, stdout="{}", stderr="")
        with mock.patch.object(github_preflight.subprocess, "run", return_value=response) as run:
            github_preflight.GhApiClient("github.com").get("repos/acme/demo;whoami")
        command = run.call_args.args[0]
        self.assertIsInstance(command, list)
        self.assertEqual(command[-1], "repos/acme/demo;whoami")
        self.assertIs(run.call_args.kwargs["shell"], False)

    def test_live_collection_uses_only_four_get_endpoints(self) -> None:
        args = github_preflight.parser().parse_args(self.base_args()[:-2])
        payloads = [
            {"login": "Rain3Dmetrology"},
            {
                "id": 123456789,
                "full_name": "Rain3Dmetrology/github-skill-governance",
                "default_branch": "main",
            },
            {"commit": {"sha": "1" * 40}},
            {"permission": "admin", "user": {"login": "Rain3Dmetrology"}},
        ]
        completed = [
            subprocess.CompletedProcess(args=[], returncode=0, stdout=json.dumps(item), stderr="")
            for item in payloads
        ]
        with mock.patch.object(github_preflight.subprocess, "run", side_effect=completed) as run:
            result, payload = self.invoke(self.base_args()[:-2])
        self.assertEqual(result, 0)
        self.assertTrue(payload["evidence"]["live_verified"])
        self.assertFalse(payload["evidence"]["authorization_verified"])
        self.assertEqual(payload["evidence"]["credential_transport"], "gh-cli-active-auth")
        self.assertEqual(payload["evidence"]["credential_type"], "opaque-not-inspected")
        self.assertEqual(run.call_count, 4)
        for call in run.call_args_list:
            self.assertNotIn("-X", call.args[0])
            self.assertFalse(call.kwargs["shell"])

    def test_live_c_preflight_never_claims_authorization(self) -> None:
        args = self.base_args()[:-2]
        args[args.index("R", args.index("--operation-class"))] = "C"
        args[args.index("read", args.index("--required-permission"))] = "write"
        payloads = [
            {"login": "Rain3Dmetrology"},
            {
                "id": 123456789,
                "full_name": "Rain3Dmetrology/github-skill-governance",
                "default_branch": "main",
            },
            {"commit": {"sha": "1" * 40}},
            {"permission": "admin", "user": {"login": "Rain3Dmetrology"}},
        ]
        completed = [
            subprocess.CompletedProcess(args=[], returncode=0, stdout=json.dumps(item), stderr="")
            for item in payloads
        ]
        with mock.patch.object(github_preflight.subprocess, "run", side_effect=completed):
            result, payload = self.invoke(args)
        self.assertEqual(result, 0)
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["evidence"]["authorization_verified"])
        self.assertEqual(
            payload["evidence"]["purpose"],
            "identity-and-permission-evidence-only",
        )


if __name__ == "__main__":
    unittest.main()
