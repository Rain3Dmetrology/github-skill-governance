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
import time
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Sequence
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
GITHUB_ACTIONS_BOT_LOGIN = "github-actions[bot]"
GITHUB_ACTIONS_BOT_ID = 41898282
ENVIRONMENT_NAME = "c-authorization"
REQUIRED_CHECK_NAME = "governance-baseline"
REQUIRED_CHECK_APP_ID = 15368
REQUIRED_CHECK_WORKFLOW_ID = 345690067
REQUIRED_CHECK_WORKFLOW_PATH = ".github/workflows/governance-baseline.yml"
MAX_RUN_AGE_SECONDS = 600
WAIT_TIMER_MINUTES = 1
VERIFY_ATTEMPTS = 6
VERIFY_RETRY_SECONDS = 2
MAX_PULL_REQUEST_FILES = 100
PROTECTED_CONTROL_PLANE_PREFIXES = (".github/", "scripts/")
SCHEMA_VERSION = "c-authorization/v1"
OPERATION_TYPE = "merge-exact-pr"
MERGE_METHOD = "squash"
EVENT = "workflow_dispatch"
API_ROOT = "https://api.github.com"
API_VERSION = "2026-03-10"
MERGE_COMMIT_QUERY = """
query BrokerMergeCommit($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    databaseId
    nameWithOwner
    pullRequest(number: $number) {
      number
      state
      merged
      mergedAt
      baseRefName
      baseRefOid
      headRefOid
      baseRepository { databaseId nameWithOwner }
      headRepository { databaseId nameWithOwner }
      mergeCommit { oid parents(first: 2) { nodes { oid } } }
    }
  }
}
""".strip()

SHA_RE = re.compile(r"[0-9a-f]{40}\Z")
CHECK_DETAILS_RE = re.compile(
    rf"https://github\.com/{re.escape(REPOSITORY)}/actions/runs/(\d+)/job/(\d+)\Z"
)


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

    def graphql(self, query: str, variables: dict[str, object]) -> object:
        return self._request(
            "POST", "graphql", {"query": query, "variables": variables}
        )

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
                "workflow_id": REQUIRED_CHECK_WORKFLOW_ID,
                "workflow_path": REQUIRED_CHECK_WORKFLOW_PATH,
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
    _exact_keys(
        required_check,
        {"app_id", "name", "workflow_id", "workflow_path"},
    )
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
    records = [
        _mapping(item, code="approval_history_invalid") for item in history
    ]
    timer_records: list[Mapping[str, Any]] = []
    reviewer_records: list[Mapping[str, Any]] = []
    for record in records:
        user = _mapping(record.get("user"), code="approval_history_invalid")
        if (
            user.get("id") == GITHUB_ACTIONS_BOT_ID
            and user.get("login") == GITHUB_ACTIONS_BOT_LOGIN
        ):
            timer_records.append(record)
        else:
            reviewer_records.append(record)

    if len(timer_records) != 1 or len(reviewer_records) != 1:
        raise BrokerFailure(
            "approval_history_ambiguous",
            "Exactly one wait-timer record and one reviewer approval are required.",
        )

    timer_record = timer_records[0]
    timer_user = _mapping(
        timer_record.get("user"), code="wait_timer_history_invalid"
    )
    if (
        timer_record.get("state") != "approved"
        or timer_record.get("comment") != f"{WAIT_TIMER_MINUTES} minute wait timer"
        or timer_user.get("type") != "Bot"
    ):
        raise BrokerFailure(
            "wait_timer_history_invalid",
            "The GitHub wait-timer approval record is invalid.",
        )
    timer_environments = _list(
        timer_record.get("environments"), code="wait_timer_history_invalid"
    )
    if len(timer_environments) != 1:
        raise BrokerFailure(
            "wait_timer_history_invalid",
            "The wait-timer record must apply to exactly one Environment.",
        )
    timer_environment = _mapping(
        timer_environments[0], code="wait_timer_history_invalid"
    )
    if timer_environment.get("name") != ENVIRONMENT_NAME:
        raise BrokerFailure(
            "wait_timer_history_invalid",
            "The wait-timer Environment does not match.",
        )
    timer_environment_id = _required_int(
        timer_environment, "id", "wait_timer_history_invalid"
    )
    if timer_environment_id <= 0:
        raise BrokerFailure(
            "wait_timer_history_invalid",
            "The wait-timer Environment ID is invalid.",
        )

    approval = reviewer_records[0]
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
    if environment_id <= 0 or environment_id != timer_environment_id:
        raise BrokerFailure(
            "approval_environment_mismatch",
            "The reviewer and wait-timer Environment IDs do not match.",
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
) -> tuple[str, int]:
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
    head_ref = head.get("ref")
    if not isinstance(head_ref, str) or not head_ref:
        raise BrokerFailure(
            "pull_request_evidence_invalid",
            "The pull request head branch cannot be proven.",
        )
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
    changed_files = _required_int(
        pull,
        "changed_files",
        "pull_request_evidence_invalid",
    )
    if changed_files <= 0 or changed_files > MAX_PULL_REQUEST_FILES:
        raise BrokerFailure(
            "pull_request_file_count_rejected",
            "The pull request file count is outside the closed Broker limit.",
        )
    return head_ref, changed_files


def _is_protected_control_plane_path(path: str) -> bool:
    return path.startswith(PROTECTED_CONTROL_PLANE_PREFIXES)


def _validate_pull_request_files(payload: object, *, expected_count: int) -> None:
    files = _list(payload, code="pull_request_files_invalid")
    if len(files) != expected_count:
        raise BrokerFailure(
            "pull_request_files_incomplete",
            "The complete pull request file list cannot be proven.",
        )
    observed: set[str] = set()
    for item in files:
        file_payload = _mapping(item, code="pull_request_files_invalid")
        filename = _required_str(
            file_payload,
            "filename",
            "pull_request_files_invalid",
        )
        paths = [filename]
        previous_filename = file_payload.get("previous_filename")
        if previous_filename is not None:
            if not isinstance(previous_filename, str):
                raise BrokerFailure(
                    "pull_request_files_invalid",
                    "A previous pull request filename is invalid.",
                )
            paths.append(previous_filename)
        if filename in observed:
            raise BrokerFailure(
                "pull_request_files_invalid",
                "The pull request file list contains duplicate paths.",
            )
        observed.add(filename)
        if any(_is_protected_control_plane_path(path) for path in paths):
            raise BrokerFailure(
                "protected_control_plane_change",
                "The Broker cannot merge a change to its protected control plane.",
            )


def _validate_required_check(
    payload: object,
    *,
    client: object,
    expected_head_ref: str,
    expected_head_sha: str,
) -> None:
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
    details_url = check.get("details_url")
    details_match = (
        CHECK_DETAILS_RE.fullmatch(details_url) if isinstance(details_url, str) else None
    )
    if details_match is None:
        raise BrokerFailure(
            "required_check_source_mismatch",
            "The required check is not linked to the canonical GitHub Actions job.",
        )
    run_id = int(details_match.group(1))
    job_id = int(details_match.group(2))
    if check.get("id") != job_id:
        raise BrokerFailure(
            "required_check_source_mismatch",
            "The required check job identity does not match its source URL.",
        )
    job = _mapping(
        client.get(f"repos/{REPOSITORY}/actions/jobs/{job_id}"),
        code="required_check_source_mismatch",
    )
    if (
        job.get("id") != job_id
        or job.get("name") != REQUIRED_CHECK_NAME
        or job.get("head_sha") != expected_head_sha
        or job.get("status") != "completed"
        or job.get("conclusion") != "success"
        or job.get("workflow_name") != REQUIRED_CHECK_NAME
        or job.get("run_url")
        != f"{API_ROOT}/repos/{REPOSITORY}/actions/runs/{run_id}"
    ):
        raise BrokerFailure(
            "required_check_source_mismatch",
            "The required check job does not match the canonical workflow contract.",
        )
    workflow_run = _mapping(
        client.get(f"repos/{REPOSITORY}/actions/runs/{run_id}"),
        code="required_check_source_mismatch",
    )
    if (
        workflow_run.get("id") != run_id
        or workflow_run.get("event") != "pull_request"
        or workflow_run.get("workflow_id") != REQUIRED_CHECK_WORKFLOW_ID
        or workflow_run.get("path") != REQUIRED_CHECK_WORKFLOW_PATH
        or workflow_run.get("head_branch") != expected_head_ref
        or workflow_run.get("head_sha") != expected_head_sha
        or workflow_run.get("status") != "completed"
        or workflow_run.get("conclusion") != "success"
    ):
        raise BrokerFailure(
            "required_check_source_mismatch",
            "The required check did not originate from the canonical pull-request workflow.",
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


def _validate_merge_commit_association(
    payload: object,
    *,
    pr_number: int,
    expected_base_sha: str,
    expected_head_sha: str,
    expected_merged_at: str,
) -> None:
    associations = _list(payload, code="merge_commit_association_invalid")
    matches = 0
    for item in associations:
        pull = _mapping(item, code="merge_commit_association_invalid")
        base = _mapping(pull.get("base"), code="merge_commit_association_invalid")
        head = _mapping(pull.get("head"), code="merge_commit_association_invalid")
        base_repo = _mapping(
            base.get("repo"), code="merge_commit_association_invalid"
        )
        head_repo = _mapping(
            head.get("repo"), code="merge_commit_association_invalid"
        )
        if (
            pull.get("number") == pr_number
            and pull.get("state") == "closed"
            and pull.get("merged_at") == expected_merged_at
            and base.get("ref") == DEFAULT_BRANCH
            and base.get("sha") == expected_base_sha
            and head.get("sha") == expected_head_sha
            and base_repo.get("id") == REPOSITORY_ID
            and base_repo.get("full_name") == REPOSITORY
            and head_repo.get("id") == REPOSITORY_ID
            and head_repo.get("full_name") == REPOSITORY
        ):
            matches += 1
    if matches != 1:
        raise BrokerFailure(
            "merge_commit_association_invalid",
            "The main commit is not uniquely associated with the authorized pull request.",
        )


def _read_main_sha(client: object) -> str:
    branch = _mapping(
        client.get(f"repos/{REPOSITORY}/branches/{DEFAULT_BRANCH}"),
        code="branch_evidence_invalid",
    )
    if branch.get("name") != DEFAULT_BRANCH:
        raise BrokerFailure("base_ref_mismatch", "The base branch is not main.")
    branch_commit = _mapping(branch.get("commit"), code="branch_evidence_invalid")
    branch_sha = branch_commit.get("sha")
    if not isinstance(branch_sha, str) or not SHA_RE.fullmatch(branch_sha):
        raise BrokerFailure(
            "branch_evidence_invalid", "The main branch commit is invalid."
        )
    return branch_sha


def _read_graphql_merge_sha(
    client: object,
    *,
    pr_number: int,
    expected_base_sha: str,
    expected_head_sha: str,
    expected_merged_at: str,
) -> str:
    owner, name = REPOSITORY.split("/", 1)
    payload = _mapping(
        client.graphql(
            MERGE_COMMIT_QUERY,
            {"owner": owner, "name": name, "number": pr_number},
        ),
        code="graphql_merge_evidence_invalid",
    )
    if payload.get("errors") not in (None, []):
        raise BrokerFailure(
            "graphql_merge_evidence_invalid",
            "GitHub GraphQL did not return exact merge evidence.",
        )
    data = _mapping(payload.get("data"), code="graphql_merge_evidence_invalid")
    repository = _mapping(
        data.get("repository"), code="graphql_merge_evidence_invalid"
    )
    pull = _mapping(
        repository.get("pullRequest"), code="graphql_merge_evidence_invalid"
    )
    base_repo = _mapping(
        pull.get("baseRepository"), code="graphql_merge_evidence_invalid"
    )
    head_repo = _mapping(
        pull.get("headRepository"), code="graphql_merge_evidence_invalid"
    )
    merge_commit = _mapping(
        pull.get("mergeCommit"), code="graphql_merge_evidence_invalid"
    )
    parents = _mapping(
        merge_commit.get("parents"), code="graphql_merge_evidence_invalid"
    )
    parent_nodes = _list(
        parents.get("nodes"), code="graphql_merge_evidence_invalid"
    )
    exact_identity = (
        repository.get("databaseId") == REPOSITORY_ID
        and repository.get("nameWithOwner") == REPOSITORY
        and pull.get("number") == pr_number
        and pull.get("state") == "MERGED"
        and pull.get("merged") is True
        and pull.get("mergedAt") == expected_merged_at
        and pull.get("baseRefName") == DEFAULT_BRANCH
        and pull.get("baseRefOid") == expected_base_sha
        and pull.get("headRefOid") == expected_head_sha
        and base_repo.get("databaseId") == REPOSITORY_ID
        and base_repo.get("nameWithOwner") == REPOSITORY
        and head_repo.get("databaseId") == REPOSITORY_ID
        and head_repo.get("nameWithOwner") == REPOSITORY
        and len(parent_nodes) == 1
        and isinstance(parent_nodes[0], dict)
        and parent_nodes[0].get("oid") == expected_base_sha
    )
    merge_sha = merge_commit.get("oid")
    if (
        not exact_identity
        or not isinstance(merge_sha, str)
        or not SHA_RE.fullmatch(merge_sha)
    ):
        raise BrokerFailure(
            "graphql_merge_evidence_invalid",
            "GitHub GraphQL did not return exact merge evidence.",
        )
    return merge_sha


def _validate_merge_commit_on_main(payload: object, *, merge_sha: str) -> None:
    comparison = _mapping(payload, code="merge_commit_ancestry_invalid")
    base_commit = _mapping(
        comparison.get("base_commit"), code="merge_commit_ancestry_invalid"
    )
    merge_base = _mapping(
        comparison.get("merge_base_commit"), code="merge_commit_ancestry_invalid"
    )
    if (
        comparison.get("status") not in {"ahead", "identical"}
        or comparison.get("behind_by") != 0
        or base_commit.get("sha") != merge_sha
        or merge_base.get("sha") != merge_sha
    ):
        raise BrokerFailure(
            "merge_commit_not_on_main",
            "The exact merge commit is not in the current main branch history.",
        )


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
        and base.get("sha") == expected_base_sha
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
        merged_at = pull.get("merged_at")
        if pull.get("state") != "closed" or not isinstance(merged_at, str):
            raise BrokerFailure(
                "effect_evidence_invalid", "The merge effect cannot be proven from readback."
            )
        if merge_sha is None:
            merge_sha = _read_graphql_merge_sha(
                client,
                pr_number=pr_number,
                expected_base_sha=expected_base_sha,
                expected_head_sha=expected_head_sha,
                expected_merged_at=merged_at,
            )
            _validate_merge_commit_association(
                client.get(
                    f"repos/{REPOSITORY}/commits/{merge_sha}/pulls?per_page=100"
                ),
                pr_number=pr_number,
                expected_base_sha=expected_base_sha,
                expected_head_sha=expected_head_sha,
                expected_merged_at=merged_at,
            )
        elif not isinstance(merge_sha, str) or not SHA_RE.fullmatch(merge_sha):
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
        main_sha = _read_main_sha(client)
        _validate_merge_commit_on_main(
            client.get(
                f"repos/{REPOSITORY}/compare/{merge_sha}...{DEFAULT_BRANCH}?per_page=1"
            ),
            merge_sha=merge_sha,
        )
        if _read_main_sha(client) != main_sha:
            raise BrokerFailure(
                "main_changed_during_verification",
                "The main branch changed during effect verification.",
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


def _verify_after_mutation(
    manifest: Mapping[str, object],
    client: object,
    *,
    sleep: Callable[[float], None],
) -> dict[str, object]:
    """Bound eventual-consistency reads without ever retrying the mutation."""

    verification: dict[str, object] = {}
    for attempt in range(VERIFY_ATTEMPTS):
        verification = verify(manifest, client)
        if verification.get("state") == "VERIFIED_COMMITTED":
            return verification
        if attempt + 1 < VERIFY_ATTEMPTS:
            sleep(VERIFY_RETRY_SECONDS)
    return verification


def _recovery_failure(
    *,
    digest: str,
    code: str,
    message: str,
    reported_merge_sha: object,
    verification: Mapping[str, object],
) -> dict[str, object]:
    """Return closed reconciliation evidence for a possibly committed mutation."""

    verification_errors = verification.get("errors")
    if not isinstance(verification_errors, list):
        verification_errors = []
    safe_reported_sha = (
        reported_merge_sha
        if isinstance(reported_merge_sha, str) and SHA_RE.fullmatch(reported_merge_sha)
        else None
    )
    return {
        "errors": [BrokerFailure(code, message).as_dict()],
        "ok": False,
        "phase": "consume",
        "recovery": {
            "reported_merge_sha": safe_reported_sha,
            "verification_errors": verification_errors,
            "verification_state": verification.get("state"),
        },
        "request_digest": digest,
        "state": "RECOVERY_REQUIRED",
    }


def _no_effect_after_attempt(
    *,
    digest: str,
    failure: BrokerFailure,
) -> dict[str, object]:
    """Report a consumed mutation attempt whose no-effect state is proven."""

    return {
        "errors": [failure.as_dict()],
        "ok": False,
        "phase": "consume",
        "request_digest": digest,
        "state": "REJECTED_NO_EFFECT",
    }


def _consume(
    manifest: Mapping[str, object],
    client: object,
    *,
    clock: Callable[[], datetime],
    mutation_state: dict[str, bool],
    sleep: Callable[[float], None],
) -> dict[str, object]:
    canonical = validate_manifest(manifest)
    digest = request_digest(canonical)
    run = _mapping(canonical["run"], code="manifest_shape_mismatch")
    operation = _mapping(canonical["operation"], code="manifest_shape_mismatch")
    run_endpoint = f"repos/{REPOSITORY}/actions/runs/{run['id']}"

    _validate_run(client.get(run_endpoint), canonical, clock())
    approval_environment_id = _validate_approval(
        client.get(f"{run_endpoint}/approvals"), digest
    )

    # Everything capable of drifting is read again after approval validation.
    _validate_run(client.get(run_endpoint), canonical, clock())
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
    expected_head_ref, changed_file_count = _validate_open_pull_request(
        client.get(f"repos/{REPOSITORY}/pulls/{operation['pull_request_number']}"),
        pr_number=operation["pull_request_number"],
        expected_base_sha=operation["expected_base_sha"],
        expected_head_sha=operation["expected_head_sha"],
    )
    _validate_pull_request_files(
        client.get(
            f"repos/{REPOSITORY}/pulls/{operation['pull_request_number']}"
            "/files?per_page=100"
        ),
        expected_count=changed_file_count,
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
        client=client,
        expected_head_ref=expected_head_ref,
        expected_head_sha=operation["expected_head_sha"],
    )

    # Refresh time and base immediately before the only mutation attempt. The
    # REST merge API has no atomic expected-base precondition, so the residual
    # race remains explicitly documented and is detected again after effect.
    _validate_run(client.get(run_endpoint), canonical, clock())
    _validate_branch(
        client.get(f"repos/{REPOSITORY}/branches/{DEFAULT_BRANCH}"),
        operation["expected_base_sha"],
    )

    merge_endpoint = (
        f"repos/{REPOSITORY}/pulls/{operation['pull_request_number']}/merge"
    )
    merge_body = {
        "merge_method": MERGE_METHOD,
        "sha": operation["expected_head_sha"],
    }
    mutation_state["attempted"] = True
    explicit_failure: BrokerFailure | None = None
    try:
        response = client.put(merge_endpoint, merge_body)
    except BrokerFailure as exc:
        # A typed API rejection still occurred after the mutation boundary.
        # Reconcile it before reporting that no effect happened.
        explicit_failure = exc
        response = {"merged": False, "sha": None}
    except Exception:
        response = None

    response_is_mapping = isinstance(response, dict)
    response_reports_commit = response_is_mapping and response.get("merged") is True
    response_reports_rejection = response_is_mapping and response.get("merged") is False
    reported_merge_sha = response.get("sha") if response_is_mapping else None
    verification = (
        verify(canonical, client)
        if response_reports_rejection
        else _verify_after_mutation(canonical, client, sleep=sleep)
    )

    if not response_reports_commit:
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
        if (
            response_reports_rejection
            and verification.get("state") == "VERIFIED_NOT_COMMITTED"
        ):
            return _no_effect_after_attempt(
                digest=digest,
                failure=explicit_failure
                or BrokerFailure(
                    "github_merge_rejected",
                    "GitHub explicitly rejected the merge and readback proves no effect.",
                ),
            )
        return _recovery_failure(
            digest=digest,
            code="effect_ambiguous",
            message="The merge effect is not provable; do not retry the mutation.",
            reported_merge_sha=reported_merge_sha,
            verification=verification,
        )

    if verification.get("state") != "VERIFIED_COMMITTED":
        return _recovery_failure(
            digest=digest,
            code="effect_verification_failed",
            message="GitHub reported a merge but readback could not prove the exact effect.",
            reported_merge_sha=reported_merge_sha,
            verification=verification,
        )
    receipt = dict(verification["receipt"])
    if (
        not isinstance(reported_merge_sha, str)
        or not SHA_RE.fullmatch(reported_merge_sha)
        or reported_merge_sha != receipt.get("merge_commit_sha")
    ):
        return _recovery_failure(
            digest=digest,
            code="merge_response_mismatch",
            message="The merge response SHA does not match the verified merge commit.",
            reported_merge_sha=reported_merge_sha,
            verification=verification,
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
    clock: Callable[[], datetime] | None = None,
    sleep: Callable[[float], None] | None = None,
) -> dict[str, object]:
    """Validate one approval and perform at most one exact merge API request."""

    digest: str | None = None
    canonical: Mapping[str, object] | None = None
    mutation_state = {"attempted": False}
    try:
        canonical = validate_manifest(manifest)
        digest = request_digest(canonical)
        if now is not None and clock is not None:
            raise BrokerFailure(
                "clock_configuration_invalid",
                "A fixed time and a clock cannot be supplied together.",
            )
        effective_clock = clock or (
            (lambda: now) if now is not None else (lambda: datetime.now(timezone.utc))
        )
        effective_sleep = sleep or time.sleep
        return _consume(
            canonical,
            client,
            clock=effective_clock,
            mutation_state=mutation_state,
            sleep=effective_sleep,
        )
    except BrokerFailure as exc:
        if mutation_state["attempted"] and canonical is not None and digest is not None:
            verification = _verify_after_mutation(
                canonical,
                client,
                sleep=sleep or time.sleep,
            )
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
            return _recovery_failure(
                digest=digest,
                code="broker_failure_after_mutation",
                message=(
                    "The broker failed after attempting the mutation; do not retry it."
                ),
                reported_merge_sha=None,
                verification=verification,
            )
        return _safe_failure("consume", "ABORTED_PRE_EFFECT", exc, digest)
    except Exception:
        if mutation_state["attempted"] and canonical is not None and digest is not None:
            verification = _verify_after_mutation(
                canonical,
                client,
                sleep=sleep or time.sleep,
            )
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
            return _recovery_failure(
                digest=digest,
                code="broker_internal_failure_after_mutation",
                message=(
                    "The broker failed after attempting the mutation; do not retry it."
                ),
                reported_merge_sha=None,
                verification=verification,
            )
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
