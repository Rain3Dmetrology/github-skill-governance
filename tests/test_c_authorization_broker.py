from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
import os
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "c_authorization_broker.py"
SPEC = importlib.util.spec_from_file_location("c_authorization_broker", SCRIPT)
assert SPEC and SPEC.loader
broker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = broker
SPEC.loader.exec_module(broker)

BASE_SHA = "1" * 40
HEAD_SHA = "2" * 40
MERGE_SHA = "3" * 40
RUN_ID = 987654321
PR_NUMBER = 42
NOW = datetime(2026, 8, 31, 0, 5, tzinfo=timezone.utc)


def build_manifest(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "run_id": RUN_ID,
        "run_attempt": 1,
        "workflow_ref": broker.EXPECTED_WORKFLOW_REF,
        "workflow_sha": BASE_SHA,
        "pr_number": PR_NUMBER,
        "expected_base_sha": BASE_SHA,
        "expected_head_sha": HEAD_SHA,
    }
    values.update(overrides)
    return broker.build_manifest(**values)


class FakeGitHubClient:
    def __init__(
        self,
        manifest: dict[str, object],
        *,
        approval: dict[str, object] | None = None,
        approval_history: list[dict[str, object]] | None = None,
        run_overrides: dict[str, object] | None = None,
        run_created_at: str = "2026-08-31T00:00:00Z",
        repository_id: int = broker.REPOSITORY_ID,
        branch_sha: str = BASE_SHA,
        pr_head_sha: str = HEAD_SHA,
        check_head_sha: str = HEAD_SHA,
        check_app_id: int = broker.REQUIRED_CHECK_APP_ID,
        ambiguous_merge: bool = False,
        reconcile_as_merged: bool = False,
        environment_reviewer_id: int = broker.REVIEWER_ID,
        environment_wait_timer: int = broker.WAIT_TIMER_MINUTES,
        environment_can_admins_bypass: bool | None = False,
        deployment_policy_name: str = broker.DEFAULT_BRANCH,
        deployment_policy_type: str = "branch",
        deployment_policy_count: int = 1,
        mergeable: bool | None = True,
        merge_response_sha: str = MERGE_SHA,
        merge_parent_sha: str = BASE_SHA,
        post_merge_branch_sha: str = MERGE_SHA,
        pr_draft: bool = False,
        check_conclusion: str = "success",
    ) -> None:
        self.manifest = manifest
        digest = broker.request_digest(manifest)
        self.approval = approval if approval is not None else self.approval_payload(
            comment=f"APPROVE-C1 {digest}"
        )
        self.approval_history = approval_history
        self.run_overrides = run_overrides or {}
        self.run_created_at = run_created_at
        self.repository_id = repository_id
        self.branch_sha = branch_sha
        self.pr_head_sha = pr_head_sha
        self.check_head_sha = check_head_sha
        self.check_app_id = check_app_id
        self.ambiguous_merge = ambiguous_merge
        self.reconcile_as_merged = reconcile_as_merged
        self.environment_reviewer_id = environment_reviewer_id
        self.environment_wait_timer = environment_wait_timer
        self.environment_can_admins_bypass = environment_can_admins_bypass
        self.deployment_policy_name = deployment_policy_name
        self.deployment_policy_type = deployment_policy_type
        self.deployment_policy_count = deployment_policy_count
        self.mergeable = mergeable
        self.merge_response_sha = merge_response_sha
        self.merge_parent_sha = merge_parent_sha
        self.post_merge_branch_sha = post_merge_branch_sha
        self.pr_draft = pr_draft
        self.check_conclusion = check_conclusion
        self.merged = False
        self.get_calls: list[str] = []
        self.put_calls: list[tuple[str, dict[str, object]]] = []

    @staticmethod
    def approval_payload(
        *,
        reviewer_id: int = broker.REVIEWER_ID,
        reviewer_login: str = broker.REVIEWER_LOGIN,
        environment: str = broker.ENVIRONMENT_NAME,
        comment: str,
        state: str = "approved",
    ) -> dict[str, object]:
        return {
            "comment": comment,
            "environments": [{"id": 24680, "name": environment}],
            "state": state,
            "user": {"id": reviewer_id, "login": reviewer_login},
        }

    @staticmethod
    def wait_timer_approval_payload(
        *,
        bot_id: int = broker.GITHUB_ACTIONS_BOT_ID,
        bot_login: str = broker.GITHUB_ACTIONS_BOT_LOGIN,
        comment: str = f"{broker.WAIT_TIMER_MINUTES} minute wait timer",
        environment: str = broker.ENVIRONMENT_NAME,
        environment_id: int = 24680,
        state: str = "approved",
        user_type: str = "Bot",
    ) -> dict[str, object]:
        return {
            "comment": comment,
            "environments": [{"id": environment_id, "name": environment}],
            "state": state,
            "user": {"id": bot_id, "login": bot_login, "type": user_type},
        }

    def get(self, endpoint: str) -> object:
        self.get_calls.append(endpoint)
        if endpoint.endswith(f"/actions/runs/{RUN_ID}"):
            payload: dict[str, object] = {
                "id": RUN_ID,
                "event": "workflow_dispatch",
                "run_attempt": 1,
                "created_at": self.run_created_at,
                "head_branch": broker.DEFAULT_BRANCH,
                "head_sha": BASE_SHA,
                "path": broker.WORKFLOW_PATH,
                "repository": {
                    "id": self.repository_id,
                    "full_name": broker.REPOSITORY,
                },
            }
            payload.update(self.run_overrides)
            return payload
        if endpoint.endswith(f"/actions/runs/{RUN_ID}/approvals"):
            if self.approval_history is not None:
                return copy.deepcopy(self.approval_history)
            return [
                self.wait_timer_approval_payload(),
                copy.deepcopy(self.approval),
            ]
        if endpoint == f"repos/{broker.REPOSITORY}":
            return {
                "id": self.repository_id,
                "full_name": broker.REPOSITORY,
                "default_branch": broker.DEFAULT_BRANCH,
            }
        if endpoint == (
            f"repos/{broker.REPOSITORY}/environments/{broker.ENVIRONMENT_NAME}"
        ):
            rules: list[dict[str, object]] = [
                {
                    "id": 13579,
                    "type": "required_reviewers",
                    "prevent_self_review": False,
                    "reviewers": [
                        {
                            "type": "User",
                            "reviewer": {
                                "id": self.environment_reviewer_id,
                                "login": broker.REVIEWER_LOGIN,
                            },
                        }
                    ],
                },
                {"id": 97531, "type": "branch_policy"},
            ]
            if self.environment_wait_timer:
                rules.append(
                    {
                        "id": 86420,
                        "type": "wait_timer",
                        "wait_timer": self.environment_wait_timer,
                    }
                )
            environment_payload: dict[str, object] = {
                "id": 24680,
                "name": broker.ENVIRONMENT_NAME,
                "protection_rules": rules,
                "deployment_branch_policy": {
                    "protected_branches": False,
                    "custom_branch_policies": True,
                },
            }
            if self.environment_can_admins_bypass is not None:
                environment_payload["can_admins_bypass"] = (
                    self.environment_can_admins_bypass
                )
            return environment_payload
        if endpoint == (
            f"repos/{broker.REPOSITORY}/environments/{broker.ENVIRONMENT_NAME}"
            "/deployment-branch-policies?per_page=100"
        ):
            policies = [
                {
                    "id": 24681 + index,
                    "name": self.deployment_policy_name,
                    "type": self.deployment_policy_type,
                }
                for index in range(self.deployment_policy_count)
            ]
            return {
                "total_count": self.deployment_policy_count,
                "branch_policies": policies,
            }
        if endpoint == f"repos/{broker.REPOSITORY}/branches/{broker.DEFAULT_BRANCH}":
            effect_merged = self.merged or (
                self.ambiguous_merge and self.reconcile_as_merged and bool(self.put_calls)
            )
            current = self.post_merge_branch_sha if effect_merged else self.branch_sha
            return {"name": broker.DEFAULT_BRANCH, "commit": {"sha": current}}
        if endpoint == f"repos/{broker.REPOSITORY}/pulls/{PR_NUMBER}":
            is_merged = self.merged or (
                self.ambiguous_merge and self.reconcile_as_merged and bool(self.put_calls)
            )
            return {
                "number": PR_NUMBER,
                "state": "closed" if is_merged else "open",
                "draft": self.pr_draft,
                "mergeable": self.mergeable,
                "merged": is_merged,
                "merged_at": "2026-08-31T00:05:10Z" if is_merged else None,
                "merge_commit_sha": MERGE_SHA if is_merged else None,
                "base": {
                    "ref": broker.DEFAULT_BRANCH,
                    "sha": BASE_SHA,
                    "repo": {"id": self.repository_id, "full_name": broker.REPOSITORY},
                },
                "head": {
                    "sha": self.pr_head_sha,
                    "repo": {"id": self.repository_id, "full_name": broker.REPOSITORY},
                },
            }
        if endpoint.startswith(
            f"repos/{broker.REPOSITORY}/commits/{HEAD_SHA}/check-runs?"
        ):
            return {
                "total_count": 1,
                "check_runs": [
                    {
                        "name": broker.REQUIRED_CHECK_NAME,
                        "head_sha": self.check_head_sha,
                        "status": "completed",
                        "conclusion": self.check_conclusion,
                        "app": {"id": self.check_app_id},
                        "pull_requests": [],
                    }
                ],
            }
        if endpoint == f"repos/{broker.REPOSITORY}/commits/{MERGE_SHA}":
            return {
                "sha": MERGE_SHA,
                "parents": [{"sha": self.merge_parent_sha}],
            }
        raise AssertionError(f"unexpected GET endpoint: {endpoint}")

    def put(self, endpoint: str, body: dict[str, object]) -> object:
        self.put_calls.append((endpoint, copy.deepcopy(body)))
        if self.ambiguous_merge:
            raise broker.ApiAmbiguousFailure()
        self.merged = True
        return {
            "sha": self.merge_response_sha,
            "merged": True,
            "message": "Pull Request successfully merged",
        }


class AuthorizationBrokerTests(unittest.TestCase):
    def test_machine_manifest_schema_matches_runtime_contract(self) -> None:
        schema = json.loads(
            (ROOT / ".github/governance/c-authorization-broker.schema.json").read_text(
                encoding="utf-8"
            )
        )
        manifest = build_manifest()

        self.assertEqual(set(schema["required"]), set(manifest))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            schema["properties"]["schema_version"]["const"], broker.SCHEMA_VERSION
        )
        self.assertEqual(
            schema["properties"]["repository"]["properties"]["id"]["const"],
            broker.REPOSITORY_ID,
        )
        self.assertEqual(
            schema["properties"]["workflow"]["properties"]["path"]["const"],
            broker.WORKFLOW_PATH,
        )
        self.assertEqual(
            schema["properties"]["authorization"]["properties"][
                "max_run_age_seconds"
            ]["const"],
            broker.MAX_RUN_AGE_SECONDS,
        )
        for field, value in manifest.items():
            rule = schema["properties"][field]
            if isinstance(value, dict):
                self.assertFalse(rule["additionalProperties"], field)
                self.assertEqual(set(rule["required"]), set(value), field)

    def test_machine_cli_contract_matches_runtime_outputs_and_exit_codes(self) -> None:
        contract = json.loads(
            (ROOT / ".github/governance/c-authorization-broker-cli.json").read_text(
                encoding="utf-8"
            )
        )
        manifest = build_manifest()
        digest = broker.request_digest(manifest)
        prepared = {
            "approval_comment": f"APPROVE-C1 {digest}",
            "canonical_manifest": broker.canonical_manifest(manifest),
            "errors": [],
            "manifest": manifest,
            "ok": True,
            "phase": "prepare",
            "request_digest": digest,
            "state": "PREPARED",
        }
        consumed = broker.consume(manifest, FakeGitHubClient(manifest), now=NOW)
        recovery = {
            "errors": [{"code": "effect_ambiguous", "message": "safe"}],
            "ok": False,
            "phase": "consume",
            "request_digest": digest,
            "state": "RECOVERY_REQUIRED",
        }

        self.assertEqual(set(contract["prepareSuccessFields"]), set(prepared))
        self.assertEqual(set(contract["effectSuccessFields"]), set(consumed))
        self.assertEqual(set(contract["receiptFields"]), set(consumed["receipt"]))
        self.assertEqual(set(contract["exitCodes"]), {"0", "1", "2"})
        self.assertEqual(broker._exit_for(prepared), broker.EXIT_OK)
        self.assertEqual(broker._exit_for(recovery), broker.EXIT_RECOVERY_REQUIRED)
        self.assertEqual(
            contract["credentialInput"],
            {
                "environmentVariable": "GITHUB_TOKEN",
                "commandLineAllowed": False,
                "fileInputAllowed": False,
            },
        )

    def test_prepare_is_canonical_and_binds_every_c_authorization_field(self) -> None:
        manifest = build_manifest()
        reverse_order = {
            key: manifest[key]
            for key in reversed(tuple(manifest))
        }
        digest = broker.request_digest(manifest)

        self.assertEqual(digest, broker.request_digest(reverse_order))
        self.assertRegex(digest, r"\Asha256:[0-9a-f]{64}\Z")
        self.assertEqual(
            broker.canonical_manifest(manifest),
            json.dumps(manifest, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
        )
        self.assertEqual(manifest["repository"]["id"], broker.REPOSITORY_ID)
        self.assertEqual(
            manifest["operation"]["required_check"]["app_id"],
            broker.REQUIRED_CHECK_APP_ID,
        )
        self.assertEqual(manifest["authorization"]["reviewer"]["id"], broker.REVIEWER_ID)

        variants = (
            build_manifest(run_id=RUN_ID + 1),
            build_manifest(pr_number=PR_NUMBER + 1),
            build_manifest(expected_head_sha="4" * 40),
        )
        self.assertTrue(all(broker.request_digest(item) != digest for item in variants))

        altered = copy.deepcopy(manifest)
        altered["unexpected"] = True
        with self.assertRaises(broker.BrokerFailure) as raised:
            broker.validate_manifest(altered)
        self.assertEqual(raised.exception.code, "manifest_shape_mismatch")

    def test_happy_consume_executes_one_exact_squash_merge_and_verifies(self) -> None:
        manifest = build_manifest()
        client = FakeGitHubClient(manifest)

        result = broker.consume(manifest, client, now=NOW)

        self.assertTrue(result["ok"])
        self.assertEqual(result["state"], "COMMITTED")
        self.assertFalse(result["receipt"]["reconciled"])
        self.assertEqual(result["receipt"]["merge_commit_sha"], MERGE_SHA)
        self.assertEqual(len(client.put_calls), 1)
        endpoint, body = client.put_calls[0]
        self.assertEqual(endpoint, f"repos/{broker.REPOSITORY}/pulls/{PR_NUMBER}/merge")
        self.assertEqual(body, {"merge_method": "squash", "sha": HEAD_SHA})
        approval_index = next(
            i for i, value in enumerate(client.get_calls) if value.endswith("/approvals")
        )
        self.assertGreater(
            sum(value.endswith(f"/actions/runs/{RUN_ID}") for value in client.get_calls),
            1,
        )
        self.assertTrue(
            any(
                value.endswith(f"/actions/runs/{RUN_ID}")
                for value in client.get_calls[approval_index + 1 :]
            )
        )

    def test_wrong_reviewer_comment_or_environment_fails_before_merge(self) -> None:
        manifest = build_manifest()
        valid_comment = f"APPROVE-C1 {broker.request_digest(manifest)}"
        scenarios = {
            "reviewer": FakeGitHubClient.approval_payload(
                reviewer_id=999, comment=valid_comment
            ),
            "comment": FakeGitHubClient.approval_payload(
                comment=f"APPROVE-C1 sha256:{'f' * 64}"
            ),
            "environment": FakeGitHubClient.approval_payload(
                environment="production", comment=valid_comment
            ),
            "environment_id": {
                **FakeGitHubClient.approval_payload(comment=valid_comment),
                "environments": [
                    {"id": 99999, "name": broker.ENVIRONMENT_NAME}
                ],
            },
        }
        for label, approval in scenarios.items():
            with self.subTest(label=label):
                client = FakeGitHubClient(manifest, approval=approval)
                result = broker.consume(manifest, client, now=NOW)
                self.assertFalse(result["ok"])
                self.assertEqual(result["state"], "ABORTED_PRE_EFFECT")
                self.assertEqual(client.put_calls, [])

    def test_approval_history_requires_one_timer_and_one_reviewer_record(self) -> None:
        manifest = build_manifest()
        digest = broker.request_digest(manifest)
        timer = FakeGitHubClient.wait_timer_approval_payload()
        approved = FakeGitHubClient.approval_payload(
            comment=f"APPROVE-C1 {digest}"
        )
        rejected = FakeGitHubClient.approval_payload(
            comment=f"APPROVE-C1 {digest}", state="rejected"
        )
        histories = (
            [],
            [approved],
            [timer],
            [timer, approved, approved],
            [timer, timer, approved],
            [timer, rejected],
        )
        for history in histories:
            with self.subTest(history=history):
                client = FakeGitHubClient(manifest, approval_history=history)
                result = broker.consume(manifest, client, now=NOW)
                self.assertEqual(result["state"], "ABORTED_PRE_EFFECT")
                self.assertEqual(client.put_calls, [])

    def test_wait_timer_history_is_bound_to_github_and_environment(self) -> None:
        manifest = build_manifest()
        digest = broker.request_digest(manifest)
        approved = FakeGitHubClient.approval_payload(
            comment=f"APPROVE-C1 {digest}"
        )
        invalid_timers = (
            FakeGitHubClient.wait_timer_approval_payload(bot_id=99999),
            FakeGitHubClient.wait_timer_approval_payload(bot_login="other[bot]"),
            FakeGitHubClient.wait_timer_approval_payload(comment="timer elapsed"),
            FakeGitHubClient.wait_timer_approval_payload(state="rejected"),
            FakeGitHubClient.wait_timer_approval_payload(user_type="User"),
            FakeGitHubClient.wait_timer_approval_payload(environment="production"),
            FakeGitHubClient.wait_timer_approval_payload(environment_id=99999),
        )
        for timer in invalid_timers:
            with self.subTest(timer=timer):
                client = FakeGitHubClient(
                    manifest, approval_history=[timer, approved]
                )
                result = broker.consume(manifest, client, now=NOW)
                self.assertEqual(result["state"], "ABORTED_PRE_EFFECT")
                self.assertEqual(client.put_calls, [])

    def test_workflow_run_identity_drift_fails_before_merge(self) -> None:
        manifest = build_manifest()
        scenarios = (
            {"event": "push"},
            {"run_attempt": 2},
            {"head_branch": "feature"},
            {"head_sha": "4" * 40},
            {"path": ".github/workflows/other.yml@main"},
        )
        for overrides in scenarios:
            with self.subTest(overrides=overrides):
                client = FakeGitHubClient(manifest, run_overrides=overrides)
                result = broker.consume(manifest, client, now=NOW)
                self.assertEqual(result["state"], "ABORTED_PRE_EFFECT")
                self.assertEqual(client.put_calls, [])

    def test_environment_configuration_drift_fails_before_merge(self) -> None:
        manifest = build_manifest()
        scenarios = {
            "reviewer": FakeGitHubClient(manifest, environment_reviewer_id=999),
            "missing_wait_timer": FakeGitHubClient(manifest, environment_wait_timer=0),
            "wait_timer": FakeGitHubClient(manifest, environment_wait_timer=5),
            "admin_bypass": FakeGitHubClient(
                manifest, environment_can_admins_bypass=True
            ),
            "admin_bypass_missing": FakeGitHubClient(
                manifest, environment_can_admins_bypass=None
            ),
        }
        for label, client in scenarios.items():
            with self.subTest(label=label):
                result = broker.consume(manifest, client, now=NOW)
                self.assertEqual(result["state"], "ABORTED_PRE_EFFECT")
                self.assertIn(
                    "environment_configuration_mismatch",
                    [item["code"] for item in result["errors"]],
                )
                self.assertEqual(client.put_calls, [])

    def test_deployment_branch_policy_drift_fails_before_merge(self) -> None:
        manifest = build_manifest()
        scenarios = {
            "missing": FakeGitHubClient(manifest, deployment_policy_count=0),
            "extra": FakeGitHubClient(manifest, deployment_policy_count=2),
            "wrong_name": FakeGitHubClient(
                manifest, deployment_policy_name="feature"
            ),
            "tag_not_branch": FakeGitHubClient(
                manifest, deployment_policy_type="tag"
            ),
        }
        for label, client in scenarios.items():
            with self.subTest(label=label):
                result = broker.consume(manifest, client, now=NOW)
                self.assertEqual(result["state"], "ABORTED_PRE_EFFECT")
                self.assertIn(
                    "deployment_branch_policy_mismatch",
                    [item["code"] for item in result["errors"]],
                )
                self.assertEqual(client.put_calls, [])

    def test_expired_run_and_replayed_attempt_fail_closed(self) -> None:
        manifest = build_manifest()
        expired = FakeGitHubClient(
            manifest, run_created_at="2026-08-30T23:54:59Z"
        )
        expired_result = broker.consume(manifest, expired, now=NOW)
        self.assertEqual(expired_result["state"], "ABORTED_PRE_EFFECT")
        self.assertIn("run_expired", [item["code"] for item in expired_result["errors"]])
        self.assertEqual(expired.put_calls, [])

        with self.assertRaises(broker.BrokerFailure) as raised:
            build_manifest(run_attempt=2)
        self.assertEqual(raised.exception.code, "run_attempt_rejected")

    def test_repository_sha_and_required_check_app_mismatches_fail_closed(self) -> None:
        manifest = build_manifest()
        scenarios = {
            "repository": FakeGitHubClient(manifest, repository_id=7),
            "base_sha": FakeGitHubClient(manifest, branch_sha="4" * 40),
            "head_sha": FakeGitHubClient(manifest, pr_head_sha="5" * 40),
            "check_head_sha": FakeGitHubClient(manifest, check_head_sha="6" * 40),
            "check_app": FakeGitHubClient(manifest, check_app_id=999),
        }
        expected_codes = {
            "repository": "repository_id_mismatch",
            "base_sha": "base_sha_mismatch",
            "head_sha": "head_sha_mismatch",
            "check_head_sha": "required_check_missing",
            "check_app": "required_check_missing",
        }
        for label, client in scenarios.items():
            with self.subTest(label=label):
                result = broker.consume(manifest, client, now=NOW)
                self.assertEqual(result["state"], "ABORTED_PRE_EFFECT")
                self.assertIn(
                    expected_codes[label], [item["code"] for item in result["errors"]]
                )
                self.assertEqual(client.put_calls, [])

    def test_pull_request_mergeability_null_or_false_fails_closed(self) -> None:
        manifest = build_manifest()
        for mergeable in (None, False):
            with self.subTest(mergeable=mergeable):
                client = FakeGitHubClient(manifest, mergeable=mergeable)
                result = broker.consume(manifest, client, now=NOW)
                self.assertEqual(result["state"], "ABORTED_PRE_EFFECT")
                self.assertIn(
                    "pull_request_not_mergeable",
                    [item["code"] for item in result["errors"]],
                )
                self.assertEqual(client.put_calls, [])

    def test_draft_or_unacceptable_required_check_fails_before_merge(self) -> None:
        manifest = build_manifest()
        scenarios = (
            FakeGitHubClient(manifest, pr_draft=True),
            FakeGitHubClient(manifest, check_conclusion="failure"),
        )
        for client in scenarios:
            with self.subTest(client=client):
                result = broker.consume(manifest, client, now=NOW)
                self.assertEqual(result["state"], "ABORTED_PRE_EFFECT")
                self.assertEqual(client.put_calls, [])

    def test_ambiguous_merge_reconciles_committed_effect_without_retry(self) -> None:
        manifest = build_manifest()
        client = FakeGitHubClient(
            manifest, ambiguous_merge=True, reconcile_as_merged=True
        )

        result = broker.consume(manifest, client, now=NOW)

        self.assertEqual(result["state"], "COMMITTED")
        self.assertTrue(result["receipt"]["reconciled"])
        self.assertEqual(result["receipt"]["merge_commit_sha"], MERGE_SHA)
        self.assertEqual(len(client.put_calls), 1)

    def test_ambiguous_merge_without_provable_effect_requires_recovery(self) -> None:
        manifest = build_manifest()
        client = FakeGitHubClient(manifest, ambiguous_merge=True)

        result = broker.consume(manifest, client, now=NOW)

        self.assertFalse(result["ok"])
        self.assertEqual(result["state"], "RECOVERY_REQUIRED")
        self.assertEqual(len(client.put_calls), 1)
        self.assertIn("effect_ambiguous", [item["code"] for item in result["errors"]])

    def test_success_response_sha_must_match_verified_merge_sha(self) -> None:
        manifest = build_manifest()
        client = FakeGitHubClient(manifest, merge_response_sha="4" * 40)

        result = broker.consume(manifest, client, now=NOW)

        self.assertEqual(result["state"], "RECOVERY_REQUIRED")
        self.assertEqual(len(client.put_calls), 1)
        self.assertIn(
            "merge_response_mismatch", [item["code"] for item in result["errors"]]
        )

    def test_verify_rejects_main_tip_that_is_not_exact_merge_commit(self) -> None:
        manifest = build_manifest()
        client = FakeGitHubClient(manifest, post_merge_branch_sha="5" * 40)
        client.merged = True

        result = broker.verify(manifest, client)

        self.assertEqual(result["state"], "RECOVERY_REQUIRED")
        self.assertIn(
            "merge_commit_not_main_tip", [item["code"] for item in result["errors"]]
        )
        self.assertEqual(client.put_calls, [])

    def test_verify_rejects_merge_created_from_a_different_base(self) -> None:
        manifest = build_manifest()
        client = FakeGitHubClient(manifest, merge_parent_sha="5" * 40)
        client.merged = True

        result = broker.verify(manifest, client)

        self.assertEqual(result["state"], "RECOVERY_REQUIRED")
        self.assertIn(
            "merge_base_not_exact", [item["code"] for item in result["errors"]]
        )
        self.assertEqual(client.put_calls, [])

    def test_verify_is_read_only_for_committed_and_uncommitted_states(self) -> None:
        manifest = build_manifest()
        committed = FakeGitHubClient(manifest)
        committed.merged = True
        committed_result = broker.verify(manifest, committed)
        self.assertEqual(committed_result["state"], "VERIFIED_COMMITTED")
        self.assertEqual(committed.put_calls, [])

        uncommitted = FakeGitHubClient(manifest)
        uncommitted_result = broker.verify(manifest, uncommitted)
        self.assertEqual(uncommitted_result["state"], "VERIFIED_NOT_COMMITTED")
        self.assertFalse(uncommitted_result["ok"])
        self.assertEqual(broker._exit_for(uncommitted_result), broker.EXIT_FAILED)
        self.assertEqual(uncommitted.put_calls, [])

    def test_workflow_sha_must_be_current_expected_base_sha(self) -> None:
        with self.assertRaises(broker.BrokerFailure) as raised:
            build_manifest(workflow_sha="6" * 40)
        self.assertEqual(raised.exception.code, "workflow_base_sha_mismatch")

    def test_cli_never_prints_token_or_raw_exception_and_uses_no_shell(self) -> None:
        secret = "github_" + "pat_" + "DO_NOT_LEAK_0123456789"

        class ExplodingClient:
            def get(self, endpoint: str) -> object:
                del endpoint
                raise RuntimeError(f"network failed with Authorization: Bearer {secret}")

            def put(self, endpoint: str, body: dict[str, object]) -> object:
                del endpoint, body
                raise AssertionError("not reached")

        args = [
            "consume",
            "--run-id",
            str(RUN_ID),
            "--run-attempt",
            "1",
            "--workflow-ref",
            broker.EXPECTED_WORKFLOW_REF,
            "--workflow-sha",
            BASE_SHA,
            "--pr-number",
            str(PR_NUMBER),
            "--expected-base-sha",
            BASE_SHA,
            "--expected-head-sha",
            HEAD_SHA,
        ]
        output = io.StringIO()
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": secret}, clear=False), mock.patch.object(
            broker.GitHubApiClient,
            "from_environment",
            return_value=ExplodingClient(),
        ), contextlib.redirect_stdout(output):
            exit_code = broker.main(args)

        rendered = output.getvalue()
        self.assertEqual(exit_code, broker.EXIT_FAILED)
        self.assertNotIn(secret, rendered)
        self.assertNotIn("Authorization", rendered)
        self.assertNotIn(str(ROOT), rendered)
        self.assertFalse(hasattr(broker, "subprocess"))


if __name__ == "__main__":
    unittest.main()
