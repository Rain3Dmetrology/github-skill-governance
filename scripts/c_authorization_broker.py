#!/usr/bin/env python3
"""Single-use broker for one exact, Environment-approved squash merge.

This module deliberately exposes one allowlisted C-class operation. It reads
only the job-scoped ``GITHUB_TOKEN``, uses the Python standard library, never
invokes a shell, and never retries a mutation whose effect is uncertain.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence
from urllib import error, parse, request


EXIT_OK = 0
EXIT_FAILED = 1
EXIT_RECOVERY_REQUIRED = 2

REPOSITORY = "Rain3Dmetrology/github-skill-governance"
REPOSITORY_ID = 1350230486
DEFAULT_BRANCH = "main"
WORKFLOW_PATH = ".github/workflows/c-merge-exact-pr.yml"
EXPECTED_WORKFLOW_REF = f"{REPOSITORY}/{WORKFLOW_PATH}@refs/heads/{DEFAULT_BRANCH}"
REVIEWER_LOGIN = "Rain3Dmetrology"
REVIEWER_ID = 79391663
ENVIRONMENT_NAME = "c-authorization"
REQUIRED_CHECK_NAME = "governance-baseline"
REQUIRED_CHECK_APP_ID = 15368
MAX_RUN_AGE_SECONDS = 600
WAIT_TIMER_MINUTES = 1
SCHEMA_VERSION = "c-authorization/v1"
OPERATION_TYPE = "merge-exact-pr"
MERGE_METHOD = "squash"
EVENT = "workflow_dispatch"
API_ROOT = "https://api.github.com"
API_VERSION = "2026-03-10"

SHA_RE = re.compile(r"[0-9a-f]{40}\Z")


class BrokerFailure(RuntimeError):
    """Fail-closed error with a fixed, safe-to-print message."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.safe_message = message

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.safe_message}


class ApiAmbiguousFailure(RuntimeError):
    """The merge request may have reached GitHub; reconciliation is required."""

    def __init__(self) -> None:
        super().__init__("A mutation response was ambiguous.")


class BrokerArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise BrokerFailure(
            "invalid_arguments",
            "One or more command-line arguments are missing or invalid.",
        )


class GitHubApiClient:
    """Minimal GitHub client with one-shot mutation semantics and safe errors."""

    def __init__(self, token: str) -> None:
        if not isinstance(token, str) or not token:
            raise BrokerFailure(
                "token_unavailable",
                "The job-scoped GITHUB_TOKEN is unavailable.",
            )
        self._token = token

    @classmethod
    def from_environment(cls) -> "GitHubApiClient":
        return cls(os.environ.get("GITHUB_TOKEN", ""))

    def get(self, endpoint: str) -> object:
        return self._request("GET", endpoint)

    def put(self, endpoint: str, body: dict[str, object]) -> object:
        return self._request("PUT", endpoint, body)

    def _request(
        self,
        method: str,
        endpoint: str,
        body: dict[str, object] | None = None,
    ) -> object:
        encoded = None
        if body is not None:
            encoded = json.dumps(
                body, ensure_ascii=False, separators=(",", ":"), sort_keys=True
            ).encode("utf-8")
        api_request = request.Request(
            f"{API_ROOT}/{endpoint}",
            data=encoded,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
                "User-Agent": "github-skill-governance-c-authorization-broker",
                "X-GitHub-Api-Version": API_VERSION,
            },
            method=method,
        )
        try:
            with request.urlopen(api_request, timeout=30) as response:
                raw = response.read()
        except error.HTTPError as exc:
            if method == "PUT" and (exc.code >= 500 or exc.code in {408, 425, 429}):
                raise ApiAmbiguousFailure() from None
            raise BrokerFailure(
                "github_api_rejected",
                "GitHub rejected an API request before a committed effect was reported.",
            ) from None
        except (error.URLError, TimeoutError, OSError):
            if method == "PUT":
                raise ApiAmbiguousFailure() from None
            raise BrokerFailure(
                "github_api_unavailable",
                "A required read-only GitHub API request could not be completed.",
            ) from None

        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError, UnicodeError):
            if method == "PUT":
                raise ApiAmbiguousFailure() from None
            raise BrokerFailure(
                "invalid_api_response",
                "GitHub returned a response with an unexpected JSON representation.",
            ) from None


def canonical_manifest(manifest: Mapping[str, object]) -> str:
    return json.dumps(
        manifest,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def request_digest(manifest: Mapping[str, object]) -> str:
    encoded = canonical_manifest(manifest).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _positive_int(value: object, *, code: str, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise BrokerFailure(code, f"The {label} must be a positive integer.")
    return value


def _sha(value: object, *, code: str, label: str) -> str:
    if not isinstance(value, str) or not SHA_RE.fullmatch(value):
        raise BrokerFailure(code, f"The {label} must be a lowercase 40-character SHA.")
    return value


def build_manifest(
    *,
    run_id: int,
    run_attempt: int,
    workflow_ref: str,
    workflow_sha: str,
    pr_number: int,
    expected_base_sha: str,
    expected_head_sha: str,
) -> dict[str, object]:
    """Build the sole canonical request type; no arbitrary mutation is accepted."""

    run_id = _positive_int(run_id, code="invalid_run_id", label="run ID")
    pr_number = _positive_int(
        pr_number, code="invalid_pull_request_number", label="pull request number"
    )
    if isinstance(run_attempt, bool) or run_attempt != 1:
        raise BrokerFailure(
            "run_attempt_rejected",
            "Only the first workflow run attempt can consume C authorization.",
        )
    if workflow_ref != EXPECTED_WORKFLOW_REF:
        raise BrokerFailure(
            "workflow_ref_mismatch",
            "The workflow ref is not the allowlisted main-branch workflow.",
        )
    workflow_sha = _sha(
        workflow_sha, code="invalid_workflow_sha", label="workflow SHA"
    )
    expected_base_sha = _sha(
        expected_base_sha, code="invalid_base_sha", label="expected base SHA"
    )
    expected_head_sha = _sha(
        expected_head_sha, code="invalid_head_sha", label="expected head SHA"
    )
    if workflow_sha != expected_base_sha:
        raise BrokerFailure(
            "workflow_base_sha_mismatch",
            "The reviewed workflow revision must equal the expected base revision.",
        )

    return {
        "authorization": {
            "environment": ENVIRONMENT_NAME,
            "max_run_age_seconds": MAX_RUN_AGE_SECONDS,
            "reviewer": {"id": REVIEWER_ID, "login": REVIEWER_LOGIN},
        },
        "operation": {
            "base_ref": f"refs/heads/{DEFAULT_BRANCH}",
            "expected_base_sha": expected_base_sha,
            "expected_head_sha": expected_head_sha,
            "merge_method": MERGE_METHOD,
            "pull_request_number": pr_number,
            "required_check": {
                "app_id": REQUIRED_CHECK_APP_ID,
                "name": REQUIRED_CHECK_NAME,
            },
            "type": OPERATION_TYPE,
        },
        "repository": {
            "default_branch": DEFAULT_BRANCH,
            "full_name": REPOSITORY,
            "id": REPOSITORY_ID,
        },
        "run": {"attempt": 1, "event": EVENT, "id": run_id},
        "schema_version": SCHEMA_VERSION,
        "workflow": {
            "path": WORKFLOW_PATH,
            "ref": EXPECTED_WORKFLOW_REF,
            "sha": workflow_sha,
        },
    }


def _mapping(value: object, *, code: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise BrokerFailure(code, "A required GitHub or manifest object is invalid.")
    return value


def _list(value: object, *, code: str) -> list[Any]:
    if not isinstance(value, list):
        raise BrokerFailure(code, "A required GitHub list is invalid.")
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str]) -> None:
    if set(value) != expected:
        raise BrokerFailure(
            "manifest_shape_mismatch",
            "The authorization manifest has missing or unknown fields.",
        )


def validate_manifest(manifest: Mapping[str, object]) -> dict[str, object]:
    """Reject altered manifests, unknown fields, and non-canonical value types."""

    root = _mapping(manifest, code="manifest_shape_mismatch")
    _exact_keys(
        root,
        {"authorization", "operation", "repository", "run", "schema_version", "workflow"},
    )
    if root["schema_version"] != SCHEMA_VERSION:
        raise BrokerFailure(
            "manifest_version_mismatch", "The authorization manifest version is unsupported."
        )

    repository = _mapping(root["repository"], code="manifest_shape_mismatch")
    run = _mapping(root["run"], code="manifest_shape_mismatch")
    workflow = _mapping(root["workflow"], code="manifest_shape_mismatch")
    operation = _mapping(root["operation"], code="manifest_shape_mismatch")
    required_check = _mapping(
        operation.get("required_check"), code="manifest_shape_mismatch"
    )
    authorization = _mapping(root["authorization"], code="manifest_shape_mismatch")
    reviewer = _mapping(authorization.get("reviewer"), code="manifest_shape_mismatch")

    _exact_keys(repository, {"default_branch", "full_name", "id"})
    _exact_keys(run, {"attempt", "event", "id"})
    _exact_keys(workflow, {"path", "ref", "sha"})
    _exact_keys(
        operation,
        {
            "base_ref",
            "expected_base_sha",
            "expected_head_sha",
            "merge_method",
            "pull_request_number",
            "required_check",
            "type",
        },
    )
    _exact_keys(required_check, {"app_id", "name"})
    _exact_keys(authorization, {"environment", "max_run_age_seconds", "reviewer"})
    _exact_keys(reviewer, {"id", "login"})

    rebuilt = build_manifest(
        run_id=_positive_int(run.get("id"), code="invalid_run_id", label="run ID"),
        run_attempt=run.get("attempt"),
        workflow_ref=workflow.get("ref"),
        workflow_sha=workflow.get("sha"),
        pr_number=_positive_int(
            operation.get("pull_request_number"),
            code="invalid_pull_request_number",
            label="pull request number",
        ),
        expected_base_sha=operation.get("expected_base_sha"),
        expected_head_sha=operation.get("expected_head_sha"),
    )
    if root != rebuilt:
        raise BrokerFailure(
            "manifest_value_mismatch",
            "The authorization manifest does not match the fixed C route contract.",
        )
    return rebuilt


def _safe_failure(
    phase: str,
    state: str,
    failure: BrokerFailure,
    digest: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "errors": [failure.as_dict()],
        "ok": False,
        "phase": phase,
        "state": state,
    }
    if digest is not None:
        payload["request_digest"] = digest
    return payload


def _required_int(payload: Mapping[str, Any], key: str, code: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise BrokerFailure(code, "GitHub evidence is missing a required integer field.")
    return value


def _required_str(payload: Mapping[str, Any], key: str, code: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise BrokerFailure(code, "GitHub evidence is missing a required string field.")
    return value


def _parse_github_time(value: object) -> datetime:
    if not isinstance(value, str):
        raise BrokerFailure("run_time_invalid", "The workflow run timestamp is invalid.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise BrokerFailure("run_time_invalid", "The workflow run timestamp is invalid.") from None
    if parsed.tzinfo is None:
        raise BrokerFailure("run_time_invalid", "The workflow run timestamp is invalid.")
    return parsed.astimezone(timezone.utc)


def _validate_run(
    payload: object,
    manifest: Mapping[str, object],
    now: datetime,
) -> None:
    run_payload = _mapping(payload, code="run_evidence_invalid")
    run = _mapping(manifest["run"], code="manifest_shape_mismatch")
    workflow = _mapping(manifest["workflow"], code="manifest_shape_mismatch")
    repository = _mapping(manifest["repository"], code="manifest_shape_mismatch")

    if _required_int(run_payload, "id", "run_id_mismatch") != run["id"]:
        raise BrokerFailure("run_id_mismatch", "The workflow run ID does not match.")
    if _required_int(run_payload, "run_attempt", "run_attempt_rejected") != 1:
        raise BrokerFailure(
            "run_attempt_rejected",
            "Only the first workflow run attempt can consume C authorization.",
        )
    if _required_str(run_payload, "event", "run_event_mismatch") != EVENT:
        raise BrokerFailure(
            "run_event_mismatch", "The workflow run was not started by workflow_dispatch."
        )
    if _required_str(run_payload, "head_branch", "run_branch_mismatch") != DEFAULT_BRANCH:
        raise BrokerFailure("run_branch_mismatch", "The workflow run branch is not main.")
    if _required_str(run_payload, "head_sha", "run_sha_mismatch") != workflow["sha"]:
        raise BrokerFailure("run_sha_mismatch", "The workflow run SHA does not match.")
    if _required_str(
        run_payload, "path", "workflow_path_mismatch"
    ) != WORKFLOW_PATH:
        raise BrokerFailure("workflow_path_mismatch", "The workflow path does not match.")

    run_repository = _mapping(
        run_payload.get("repository"), code="repository_evidence_invalid"
    )
    if _required_int(run_repository, "id", "repository_id_mismatch") != repository["id"]:
        raise BrokerFailure("repository_id_mismatch", "The repository ID does not match.")
    if _required_str(
        run_repository, "full_name", "repository_name_mismatch"
    ) != repository["full_name"]:
        raise BrokerFailure("repository_name_mismatch", "The repository name does not match.")

    created_at = _parse_github_time(run_payload.get("created_at"))
    if now.tzinfo is None:
        raise BrokerFailure("clock_invalid", "The broker clock must include a timezone.")
    age = (now.astimezone(timezone.utc) - created_at).total_seconds()
    if age < 0:
        raise BrokerFailure("run_time_invalid", "The workflow run timestamp is in the future.")
    if age > MAX_RUN_AGE_SECONDS:
        raise BrokerFailure(
            "run_expired", "The workflow run is older than the authorization time limit."
        )


def _validate_approval(payload: object, digest: str) -> int:
    history = _list(payload, code="approval_history_invalid")
    if len(history) != 1:
        raise BrokerFailure(
            "approval_history_ambiguous",
            "Exactly one Environment approval record is required.",
        )
    approval = _mapping(history[0], code="approval_history_invalid")
    if approval.get("state") != "approved":
        raise BrokerFailure("approval_missing", "The Environment approval is not approved.")
    if approval.get("comment") != f"APPROVE-C1 {digest}":
        raise BrokerFailure(
            "approval_comment_mismatch",
            "The Environment approval comment does not match this request digest.",
        )
    user = _mapping(approval.get("user"), code="approval_reviewer_mismatch")
    if (
        _required_int(user, "id", "approval_reviewer_mismatch") != REVIEWER_ID
        or _required_str(user, "login", "approval_reviewer_mismatch") != REVIEWER_LOGIN
    ):
        raise BrokerFailure(
            "approval_reviewer_mismatch", "The Environment reviewer does not match."
        )
    environments = _list(
        approval.get("environments"), code="approval_environment_mismatch"
    )
    if len(environments) != 1:
        raise BrokerFailure(
            "approval_environment_mismatch",
            "The approval must apply to exactly one Environment.",
        )
    environment = _mapping(environments[0], code="approval_environment_mismatch")
    if environment.get("name") != ENVIRONMENT_NAME:
        raise BrokerFailure(
            "approval_environment_mismatch", "The approved Environment does not match."
        )
    environment_id = _required_int(
        environment, "id", "approval_environment_mismatch"
    )
    if environment_id <= 0:
        raise BrokerFailure(
            "approval_environment_mismatch", "The approved Environment ID is invalid."
        )
    return environment_id


def _validate_repository(payload: object) -> None:
    repository = _mapping(payload, code="repository_evidence_invalid")
    if _required_int(repository, "id", "repository_id_mismatch") != REPOSITORY_ID:
        raise BrokerFailure("repository_id_mismatch", "The repository ID does not match.")
    if _required_str(repository, "full_name", "repository_name_mismatch") != REPOSITORY:
        raise BrokerFailure("repository_name_mismatch", "The repository name does not match.")
    if _required_str(
        repository, "default_branch", "default_branch_mismatch"
    ) != DEFAULT_BRANCH:
        raise BrokerFailure("default_branch_mismatch", "The default branch is not main.")


def _validate_environment(payload: object, approval_environment_id: int) -> None:
    environment = _mapping(payload, code="environment_evidence_invalid")
    if _required_int(environment, "id", "approval_environment_mismatch") != approval_environment_id:
        raise BrokerFailure(
            "approval_environment_mismatch",
            "The approved Environment ID does not match the current Environment.",
        )
    if _required_str(
        environment, "name", "environment_configuration_mismatch"
    ) != ENVIRONMENT_NAME:
        raise BrokerFailure(
            "environment_configuration_mismatch",
            "The protected Environment name does not match.",
        )
    if environment.get("can_admins_bypass") is not False:
        raise BrokerFailure(
            "environment_configuration_mismatch",
            "The Environment reports that administrator bypass is enabled.",
        )

    branch_policy = _mapping(
        environment.get("deployment_branch_policy"),
        code="environment_configuration_mismatch",
    )
    if branch_policy != {
        "protected_branches": False,
        "custom_branch_policies": True,
    }:
        raise BrokerFailure(
            "environment_configuration_mismatch",
            "The Environment deployment branch policy has drifted.",
        )

    rules = _list(
        environment.get("protection_rules"), code="environment_configuration_mismatch"
    )
    known_types = {"branch_policy", "required_reviewers", "wait_timer"}
    if any(
        not isinstance(rule, dict) or rule.get("type") not in known_types for rule in rules
    ):
        raise BrokerFailure(
            "environment_configuration_mismatch",
            "The Environment has an unexpected protection rule.",
        )
    wait_rules = [rule for rule in rules if rule.get("type") == "wait_timer"]
    if (
        len(wait_rules) != 1
        or wait_rules[0].get("wait_timer") != WAIT_TIMER_MINUTES
    ):
        raise BrokerFailure(
            "environment_configuration_mismatch", "The Environment wait timer has drifted."
        )
    branch_rules = [rule for rule in rules if rule.get("type") == "branch_policy"]
    reviewer_rules = [rule for rule in rules if rule.get("type") == "required_reviewers"]
    if len(branch_rules) != 1 or len(reviewer_rules) != 1:
        raise BrokerFailure(
            "environment_configuration_mismatch",
            "The Environment protection-rule set has drifted.",
        )
    reviewer_rule = reviewer_rules[0]
    if reviewer_rule.get("prevent_self_review") is not False:
        raise BrokerFailure(
            "environment_configuration_mismatch",
            "The Environment self-review policy has drifted.",
        )
    reviewers = _list(
        reviewer_rule.get("reviewers"), code="environment_configuration_mismatch"
    )
    if len(reviewers) != 1:
        raise BrokerFailure(
            "environment_configuration_mismatch",
            "The Environment must have exactly one required reviewer.",
        )
    reviewer_entry = _mapping(reviewers[0], code="environment_configuration_mismatch")
    reviewer = _mapping(
        reviewer_entry.get("reviewer"), code="environment_configuration_mismatch"
    )
    if (
        reviewer_entry.get("type") != "User"
        or _required_int(reviewer, "id", "environment_configuration_mismatch")
        != REVIEWER_ID
        or _required_str(reviewer, "login", "environment_configuration_mismatch")
        != REVIEWER_LOGIN
    ):
        raise BrokerFailure(
            "environment_configuration_mismatch",
            "The Environment required reviewer has drifted.",
        )


def _validate_deployment_branch_policies(payload: object) -> None:
    policies_payload = _mapping(payload, code="deployment_branch_policy_invalid")
    if _required_int(
        policies_payload, "total_count", "deployment_branch_policy_mismatch"
    ) != 1:
        raise BrokerFailure(
            "deployment_branch_policy_mismatch",
            "Exactly one deployment branch policy is required.",
        )
    policies = _list(
        policies_payload.get("branch_policies"),
        code="deployment_branch_policy_invalid",
    )
    if len(policies) != 1:
        raise BrokerFailure(
            "deployment_branch_policy_mismatch",
            "Exactly one deployment branch policy is required.",
        )
    policy = _mapping(policies[0], code="deployment_branch_policy_invalid")
    if (
        _required_int(policy, "id", "deployment_branch_policy_invalid") <= 0
        or policy.get("name") != DEFAULT_BRANCH
        or policy.get("type") != "branch"
    ):
        raise BrokerFailure(
            "deployment_branch_policy_mismatch",
            "The deployment branch policy must match only the main branch.",
        )


def _validate_branch(payload: object, expected_base_sha: str) -> None:
    branch = _mapping(payload, code="branch_evidence_invalid")
    if _required_str(branch, "name", "base_ref_mismatch") != DEFAULT_BRANCH:
        raise BrokerFailure("base_ref_mismatch", "The base branch is not main.")
    commit = _mapping(branch.get("commit"), code="branch_evidence_invalid")
    if _required_str(commit, "sha", "base_sha_mismatch") != expected_base_sha:
        raise BrokerFailure("base_sha_mismatch", "The main branch SHA has changed.")


def _validate_open_pull_request(
    payload: object,
    *,
    pr_number: int,
    expected_base_sha: str,
    expected_head_sha: str,
) -> None:
    pull = _mapping(payload, code="pull_request_evidence_invalid")
    if _required_int(pull, "number", "pull_request_mismatch") != pr_number:
        raise BrokerFailure("pull_request_mismatch", "The pull request number does not match.")
    if pull.get("state") != "open" or pull.get("merged") is not False:
        raise BrokerFailure(
            "replay_or_state_mismatch",
            "The pull request is not an unmerged open pull request.",
        )
    if pull.get("draft") is not False:
        raise BrokerFailure("pull_request_is_draft", "The pull request is still a draft.")
    if pull.get("mergeable") is not True:
        raise BrokerFailure(
            "pull_request_not_mergeable",
            "GitHub has not proven that the pull request is mergeable.",
        )
    base = _mapping(pull.get("base"), code="pull_request_evidence_invalid")
    head = _mapping(pull.get("head"), code="pull_request_evidence_invalid")
    base_repo = _mapping(base.get("repo"), code="pull_request_evidence_invalid")
    head_repo = _mapping(head.get("repo"), code="pull_request_evidence_invalid")
    if base.get("ref") != DEFAULT_BRANCH:
        raise BrokerFailure("base_ref_mismatch", "The pull request base is not main.")
    if base.get("sha") != expected_base_sha:
        raise BrokerFailure("base_sha_mismatch", "The pull request base SHA has changed.")
    if head.get("sha") != expected_head_sha:
        raise BrokerFailure("head_sha_mismatch", "The pull request head SHA has changed.")
    if (
        base_repo.get("id") != REPOSITORY_ID
        or base_repo.get("full_name") != REPOSITORY
        or head_repo.get("id") != REPOSITORY_ID
        or head_repo.get("full_name") != REPOSITORY
    ):
        raise BrokerFailure(
            "pull_request_repository_mismatch",
            "The pull request is not fully contained in the target repository.",
        )


def _validate_required_check(payload: object, *, expected_head_sha: str) -> None:
    checks = _mapping(payload, code="check_evidence_invalid")
    runs = _list(checks.get("check_runs"), code="check_evidence_invalid")
    matching: list[Mapping[str, Any]] = []
    for item in runs:
        if not isinstance(item, dict):
            continue
        app = item.get("app")
        if (
            item.get("name") == REQUIRED_CHECK_NAME
            and item.get("head_sha") == expected_head_sha
            and isinstance(app, dict)
            and app.get("id") == REQUIRED_CHECK_APP_ID
        ):
            matching.append(item)
    if len(matching) != 1:
        raise BrokerFailure(
            "required_check_missing",
            "The exact required check and GitHub App identity were not found.",
        )
    check = matching[0]
    if check.get("status") != "completed" or check.get("conclusion") != "success":
        raise BrokerFailure(
            "required_check_not_successful", "The exact required check is not successful."
        )


def _receipt(
    manifest: Mapping[str, object],
    *,
    merge_commit_sha: str | None,
    reconciled: bool,
) -> dict[str, object]:
    operation = _mapping(manifest["operation"], code="manifest_shape_mismatch")
    run = _mapping(manifest["run"], code="manifest_shape_mismatch")
    return {
        "expected_base_sha": operation["expected_base_sha"],
        "expected_head_sha": operation["expected_head_sha"],
        "merge_commit_sha": merge_commit_sha,
        "operation": OPERATION_TYPE,
        "pull_request_number": operation["pull_request_number"],
        "reconciled": reconciled,
        "repository_id": REPOSITORY_ID,
        "run_attempt": run["attempt"],
        "run_id": run["id"],
    }


def _verify_exact_effect(
    manifest: Mapping[str, object], client: object
) -> tuple[str, str | None]:
    operation = _mapping(manifest["operation"], code="manifest_shape_mismatch")
    pr_number = operation["pull_request_number"]
    expected_base_sha = operation["expected_base_sha"]
    expected_head_sha = operation["expected_head_sha"]

    repository = client.get(f"repos/{REPOSITORY}")
    _validate_repository(repository)
    pull = _mapping(
        client.get(f"repos/{REPOSITORY}/pulls/{pr_number}"),
        code="pull_request_evidence_invalid",
    )
    if pull.get("number") != pr_number:
        raise BrokerFailure("pull_request_mismatch", "The pull request number does not match.")
    base = _mapping(pull.get("base"), code="pull_request_evidence_invalid")
    head = _mapping(pull.get("head"), code="pull_request_evidence_invalid")
    base_repo = _mapping(base.get("repo"), code="pull_request_evidence_invalid")
    head_repo = _mapping(head.get("repo"), code="pull_request_evidence_invalid")
    exact_identity = (
        base.get("ref") == DEFAULT_BRANCH
        and head.get("sha") == expected_head_sha
        and base_repo.get("id") == REPOSITORY_ID
        and base_repo.get("full_name") == REPOSITORY
        and head_repo.get("id") == REPOSITORY_ID
        and head_repo.get("full_name") == REPOSITORY
    )
    if not exact_identity:
        raise BrokerFailure(
            "effect_identity_mismatch", "The pull request effect identity does not match."
        )
    if pull.get("merged") is True:
        merge_sha = pull.get("merge_commit_sha")
        if (
            pull.get("state") != "closed"
            or not isinstance(pull.get("merged_at"), str)
            or not isinstance(merge_sha, str)
            or not SHA_RE.fullmatch(merge_sha)
        ):
            raise BrokerFailure(
                "effect_evidence_invalid", "The merge effect cannot be proven from readback."
            )
        merge_commit = _mapping(
            client.get(f"repos/{REPOSITORY}/commits/{merge_sha}"),
            code="merge_commit_evidence_invalid",
        )
        if merge_commit.get("sha") != merge_sha:
            raise BrokerFailure(
                "merge_commit_evidence_invalid",
                "The merge commit identity cannot be proven from readback.",
            )
        parents = _list(
            merge_commit.get("parents"), code="merge_commit_evidence_invalid"
        )
        if (
            len(parents) != 1
            or not isinstance(parents[0], dict)
            or parents[0].get("sha") != expected_base_sha
        ):
            raise BrokerFailure(
                "merge_base_not_exact",
                "The squash merge was not created from the authorized base commit.",
            )
        branch = _mapping(
            client.get(f"repos/{REPOSITORY}/branches/{DEFAULT_BRANCH}"),
            code="branch_evidence_invalid",
        )
        if branch.get("name") != DEFAULT_BRANCH:
            raise BrokerFailure("base_ref_mismatch", "The base branch is not main.")
        branch_commit = _mapping(branch.get("commit"), code="branch_evidence_invalid")
        if branch_commit.get("sha") != merge_sha:
            raise BrokerFailure(
                "merge_commit_not_main_tip",
                "The exact merge commit is not the current main branch tip.",
            )
        return "VERIFIED_COMMITTED", merge_sha
    if pull.get("merged") is not False or pull.get("state") != "open":
        raise BrokerFailure(
            "effect_evidence_invalid", "The pull request effect cannot be proven from readback."
        )
    branch = client.get(f"repos/{REPOSITORY}/branches/{DEFAULT_BRANCH}")
    _validate_branch(branch, expected_base_sha)
    return "VERIFIED_NOT_COMMITTED", None


def verify(manifest: Mapping[str, object], client: object) -> dict[str, object]:
    """Read-only effect verification; this function has no mutation path."""

    digest: str | None = None
    try:
        canonical = validate_manifest(manifest)
        digest = request_digest(canonical)
        state, merge_sha = _verify_exact_effect(canonical, client)
        committed = state == "VERIFIED_COMMITTED"
        return {
            "errors": [] if committed else [
                {
                    "code": "effect_not_committed",
                    "message": "Readback proves that the exact pull request is not merged.",
                }
            ],
            "ok": committed,
            "phase": "verify",
            "receipt": _receipt(
                canonical, merge_commit_sha=merge_sha, reconciled=False
            ),
            "request_digest": digest,
            "state": state,
        }
    except BrokerFailure as exc:
        return _safe_failure("verify", "RECOVERY_REQUIRED", exc, digest)
    except Exception:
        return _safe_failure(
            "verify",
            "RECOVERY_REQUIRED",
            BrokerFailure(
                "verification_unavailable",
                "Read-only effect verification could not be completed.",
            ),
            digest,
        )


def _consume(
    manifest: Mapping[str, object], client: object, now: datetime
) -> dict[str, object]:
    canonical = validate_manifest(manifest)
    digest = request_digest(canonical)
    run = _mapping(canonical["run"], code="manifest_shape_mismatch")
    operation = _mapping(canonical["operation"], code="manifest_shape_mismatch")
    run_endpoint = f"repos/{REPOSITORY}/actions/runs/{run['id']}"

    _validate_run(client.get(run_endpoint), canonical, now)
    approval_environment_id = _validate_approval(
        client.get(f"{run_endpoint}/approvals"), digest
    )

    # Everything capable of drifting is read again after approval validation.
    _validate_run(client.get(run_endpoint), canonical, now)
    _validate_repository(client.get(f"repos/{REPOSITORY}"))
    _validate_environment(
        client.get(f"repos/{REPOSITORY}/environments/{ENVIRONMENT_NAME}"),
        approval_environment_id,
    )
    _validate_deployment_branch_policies(
        client.get(
            f"repos/{REPOSITORY}/environments/{ENVIRONMENT_NAME}"
            "/deployment-branch-policies?per_page=100"
        )
    )
    _validate_branch(
        client.get(f"repos/{REPOSITORY}/branches/{DEFAULT_BRANCH}"),
        operation["expected_base_sha"],
    )
    _validate_open_pull_request(
        client.get(f"repos/{REPOSITORY}/pulls/{operation['pull_request_number']}"),
        pr_number=operation["pull_request_number"],
        expected_base_sha=operation["expected_base_sha"],
        expected_head_sha=operation["expected_head_sha"],
    )
    query = parse.urlencode(
        {
            "check_name": REQUIRED_CHECK_NAME,
            "filter": "latest",
            "per_page": 100,
        }
    )
    _validate_required_check(
        client.get(
            f"repos/{REPOSITORY}/commits/{operation['expected_head_sha']}/check-runs?{query}"
        ),
        expected_head_sha=operation["expected_head_sha"],
    )

    merge_endpoint = (
        f"repos/{REPOSITORY}/pulls/{operation['pull_request_number']}/merge"
    )
    merge_body = {
        "merge_method": MERGE_METHOD,
        "sha": operation["expected_head_sha"],
    }
    try:
        response = client.put(merge_endpoint, merge_body)
    except BrokerFailure:
        raise
    except Exception:
        response = None
        response_ambiguous = True
    else:
        response_ambiguous = not isinstance(response, dict) or response.get("merged") is not True

    if response_ambiguous:
        verification = verify(canonical, client)
        if verification.get("state") == "VERIFIED_COMMITTED":
            receipt = dict(verification["receipt"])
            receipt["reconciled"] = True
            return {
                "errors": [],
                "ok": True,
                "phase": "consume",
                "receipt": receipt,
                "request_digest": digest,
                "state": "COMMITTED",
            }
        return _safe_failure(
            "consume",
            "RECOVERY_REQUIRED",
            BrokerFailure(
                "effect_ambiguous",
                "The merge effect is not provable; do not retry the mutation.",
            ),
            digest,
        )

    reported_merge_sha = response.get("sha")
    verification = verify(canonical, client)
    if verification.get("state") != "VERIFIED_COMMITTED":
        return _safe_failure(
            "consume",
            "RECOVERY_REQUIRED",
            BrokerFailure(
                "effect_verification_failed",
                "GitHub reported a merge but readback could not prove the exact effect.",
            ),
            digest,
        )
    receipt = dict(verification["receipt"])
    if (
        not isinstance(reported_merge_sha, str)
        or not SHA_RE.fullmatch(reported_merge_sha)
        or reported_merge_sha != receipt.get("merge_commit_sha")
    ):
        return _safe_failure(
            "consume",
            "RECOVERY_REQUIRED",
            BrokerFailure(
                "merge_response_mismatch",
                "The merge response SHA does not match the verified merge commit.",
            ),
            digest,
        )
    receipt["reconciled"] = False
    return {
        "errors": [],
        "ok": True,
        "phase": "consume",
        "receipt": receipt,
        "request_digest": digest,
        "state": "COMMITTED",
    }


def consume(
    manifest: Mapping[str, object],
    client: object,
    *,
    now: datetime | None = None,
) -> dict[str, object]:
    """Validate one approval and perform at most one exact merge API request."""

    digest: str | None = None
    try:
        canonical = validate_manifest(manifest)
        digest = request_digest(canonical)
        return _consume(canonical, client, now or datetime.now(timezone.utc))
    except BrokerFailure as exc:
        return _safe_failure("consume", "ABORTED_PRE_EFFECT", exc, digest)
    except Exception:
        return _safe_failure(
            "consume",
            "ABORTED_PRE_EFFECT",
            BrokerFailure(
                "broker_internal_failure",
                "The broker failed closed before a committed effect was reported.",
            ),
            digest,
        )


def parser() -> argparse.ArgumentParser:
    result = BrokerArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="phase", required=True)
    for name in ("prepare", "consume", "verify"):
        phase = subparsers.add_parser(name)
        phase.add_argument("--run-id", type=int, required=True)
        phase.add_argument("--run-attempt", type=int, required=True)
        phase.add_argument("--workflow-ref", required=True)
        phase.add_argument("--workflow-sha", required=True)
        phase.add_argument("--pr-number", type=int, required=True)
        phase.add_argument("--expected-base-sha", required=True)
        phase.add_argument("--expected-head-sha", required=True)
    return result


def _manifest_from_args(args: argparse.Namespace) -> dict[str, object]:
    return build_manifest(
        run_id=args.run_id,
        run_attempt=args.run_attempt,
        workflow_ref=args.workflow_ref,
        workflow_sha=args.workflow_sha,
        pr_number=args.pr_number,
        expected_base_sha=args.expected_base_sha,
        expected_head_sha=args.expected_head_sha,
    )


def emit(payload: Mapping[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _exit_for(payload: Mapping[str, object]) -> int:
    if payload.get("state") == "RECOVERY_REQUIRED":
        return EXIT_RECOVERY_REQUIRED
    return EXIT_OK if payload.get("ok") is True else EXIT_FAILED


def main(argv: Sequence[str] | None = None) -> int:
    phase = "unknown"
    try:
        args = parser().parse_args(argv)
        phase = args.phase
        manifest = _manifest_from_args(args)
        digest = request_digest(manifest)
        if phase == "prepare":
            payload: dict[str, object] = {
                "approval_comment": f"APPROVE-C1 {digest}",
                "canonical_manifest": canonical_manifest(manifest),
                "errors": [],
                "manifest": manifest,
                "ok": True,
                "phase": "prepare",
                "request_digest": digest,
                "state": "PREPARED",
            }
        else:
            client = GitHubApiClient.from_environment()
            payload = (
                consume(manifest, client)
                if phase == "consume"
                else verify(manifest, client)
            )
    except BrokerFailure as exc:
        payload = _safe_failure(phase, "ABORTED_PRE_EFFECT", exc)
    except Exception:
        payload = _safe_failure(
            phase,
            "ABORTED_PRE_EFFECT",
            BrokerFailure(
                "broker_internal_failure",
                "The broker failed closed before a committed effect was reported.",
            ),
        )
    emit(payload)
    return _exit_for(payload)


if __name__ == "__main__":
    sys.exit(main())
