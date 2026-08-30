#!/usr/bin/env python3
"""Read-only, fail-closed GitHub repository preflight.

The script deliberately shells out to ``gh api`` with an argument array. It
never reads, accepts, or prints a token. It reports only the credential
transport (active ``gh`` authentication versus an offline fixture) and marks
the credential type as opaque instead of guessing PAT, OAuth, or GitHub App
from scopes or prefixes. It proves identity, target, and observed permission;
it never claims to verify or grant human authorization. Offline fixtures exist
only for unit tests and are rejected for W/C operations.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import quote


EXIT_OK = 0
EXIT_FAILED = 1

HOST = "github.com"
PERMISSION_RANK = {
    "none": 0,
    "read": 1,
    "triage": 2,
    "write": 3,
    "maintain": 4,
    "admin": 5,
}
PERMISSION_ALIASES = {"pull": "read", "push": "write"}
OPERATION_PERMISSION_FLOOR = {"R": "read", "W": "write", "C": "write"}

ACCOUNT_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?\Z")
REPOSITORY_RE = re.compile(r"[A-Za-z0-9._-]{1,100}\Z")
INVALID_BRANCH_CHAR_RE = re.compile(r"[\x00-\x20\x7f~^:?*\[]")
SHA_RE = re.compile(r"[0-9a-fA-F]{40}\Z")


@dataclass(frozen=True)
class Finding:
    code: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


class PreflightFailure(RuntimeError):
    """A safe-to-report failure that contains no command output or secrets."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.finding = Finding(code, message)


class JsonArgumentParser(argparse.ArgumentParser):
    """Make invalid/missing CLI input return the same JSON contract and exit 1."""

    def error(self, message: str) -> None:  # pragma: no cover - exercised via SystemExit
        del message
        emit(
            {
                "errors": [
                    Finding(
                        "invalid_arguments",
                        "One or more required command-line arguments are missing or invalid.",
                    ).as_dict()
                ],
                "ok": False,
            }
        )
        raise SystemExit(EXIT_FAILED)


class GhApiClient:
    """Minimal read-only wrapper around ``gh api``."""

    def __init__(self, host: str) -> None:
        self.host = host

    def get(self, endpoint: str) -> Mapping[str, Any]:
        command = ["gh", "api", "--hostname", self.host, endpoint]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                check=False,
                shell=False,
                text=True,
                timeout=30,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise PreflightFailure(
                "gh_api_unavailable",
                f"GitHub CLI request could not be completed ({type(exc).__name__}).",
            ) from None

        if completed.returncode != 0:
            raise PreflightFailure(
                "gh_api_failed",
                "GitHub CLI returned a non-zero status for a read-only API request.",
            )

        try:
            payload = json.loads(completed.stdout)
        except (json.JSONDecodeError, TypeError):
            raise PreflightFailure(
                "invalid_api_response",
                "GitHub CLI returned a response that is not valid JSON.",
            ) from None
        if not isinstance(payload, dict):
            raise PreflightFailure(
                "invalid_api_response",
                "GitHub CLI returned a JSON value with an unexpected shape.",
            )
        return payload


class FixtureClient:
    """Fixed-file offline provider for deterministic R-class tests."""

    FILES = {
        "user": "user.json",
        "repository": "repository.json",
        "default_branch": "default_branch.json",
        "permission": "permission.json",
    }

    def __init__(self, directory: Path) -> None:
        self.directory = directory.resolve()

    def get(self, name: str) -> Mapping[str, Any]:
        filename = self.FILES[name]
        path = self.directory / filename
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise PreflightFailure(
                "fixture_missing", f"Required offline fixture is missing: {filename}."
            ) from None
        except (OSError, json.JSONDecodeError, UnicodeError):
            raise PreflightFailure(
                "fixture_invalid", f"Offline fixture is unreadable or invalid: {filename}."
            ) from None
        if not isinstance(payload, dict):
            raise PreflightFailure(
                "fixture_invalid", f"Offline fixture has an unexpected shape: {filename}."
            )
        return payload


def parser() -> argparse.ArgumentParser:
    result = JsonArgumentParser(description=__doc__)
    result.add_argument("--host", default=HOST)
    result.add_argument("--owner", required=True)
    result.add_argument("--repo", required=True)
    result.add_argument("--expected-account", required=True)
    result.add_argument("--expected-repository-id", required=True, type=int)
    result.add_argument("--expected-default-branch", required=True)
    result.add_argument("--expected-target-sha", required=True)
    result.add_argument("--operation-class", required=True, choices=("R", "W", "C"))
    result.add_argument(
        "--required-permission", required=True, choices=tuple(PERMISSION_RANK)
    )
    result.add_argument(
        "--fixture-dir",
        type=Path,
        help="Offline test evidence. Accepted only for R-class operations.",
    )
    return result


def emit(payload: Mapping[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def safe_request(args: argparse.Namespace) -> dict[str, Any]:
    """Return only non-secret request metadata."""

    return {
        "expected_account": args.expected_account,
        "expected_default_branch": args.expected_default_branch,
        "expected_repository_id": args.expected_repository_id,
        "expected_target_sha": args.expected_target_sha.lower(),
        "host": args.host,
        "operation_class": args.operation_class,
        "repository": f"{args.owner}/{args.repo}",
        "required_permission": args.required_permission,
    }


def evidence_metadata(fixture_mode: bool, *, live_verified: bool = False) -> dict[str, Any]:
    """Describe evidence provenance without inspecting authentication secrets."""

    return {
        "authorization_verified": False,
        "credential_transport": "offline-fixture" if fixture_mode else "gh-cli-active-auth",
        "credential_type": "opaque-not-inspected",
        "live_verified": live_verified,
        "mode": "offline_fixture" if fixture_mode else "live",
        "purpose": "identity-and-permission-evidence-only",
    }


def validate_inputs(args: argparse.Namespace) -> list[Finding]:
    findings: list[Finding] = []
    if args.host != HOST:
        findings.append(Finding("unsupported_host", "The host must be github.com."))
    for label, value in (("owner", args.owner), ("expected_account", args.expected_account)):
        if not ACCOUNT_RE.fullmatch(value):
            findings.append(Finding(f"invalid_{label}", f"The {label} identifier is invalid."))
    if not REPOSITORY_RE.fullmatch(args.repo) or args.repo in {".", ".."}:
        findings.append(Finding("invalid_repo", "The repository name is invalid."))
    if args.expected_repository_id <= 0:
        findings.append(
            Finding("invalid_repository_id", "The expected repository ID must be positive.")
        )
    if not valid_branch(args.expected_default_branch):
        findings.append(
            Finding("invalid_default_branch", "The expected default branch is invalid.")
        )
    if not SHA_RE.fullmatch(args.expected_target_sha):
        findings.append(
            Finding("invalid_target_sha", "The expected target SHA must be 40 hexadecimal characters.")
        )
    floor = OPERATION_PERMISSION_FLOOR[args.operation_class]
    if PERMISSION_RANK[args.required_permission] < PERMISSION_RANK[floor]:
        findings.append(
            Finding(
                "required_permission_below_operation_floor",
                f"{args.operation_class}-class operations require at least {floor} permission.",
            )
        )
    if args.fixture_dir is not None and args.operation_class != "R":
        findings.append(
            Finding(
                "offline_evidence_forbidden",
                "Offline fixtures cannot provide live identity and permission evidence for W- or C-class operations.",
            )
        )
    return findings


def valid_branch(value: str) -> bool:
    """Conservative subset of Git's refname rules for a branch name."""

    return not (
        not value
        or len(value) > 255
        or value == "@"
        or value.startswith(("/", "."))
        or value.endswith(("/", ".", ".lock"))
        or ".." in value
        or "//" in value
        or "@{" in value
        or "\\" in value
        or INVALID_BRANCH_CHAR_RE.search(value)
    )


def required_value(
    payload: Mapping[str, Any], key: str, expected_type: type, source: str
) -> Any:
    value = payload.get(key)
    if isinstance(value, bool) and expected_type is int:
        value = None
    if not isinstance(value, expected_type):
        raise PreflightFailure(
            "evidence_field_missing",
            f"Required field {source}.{key} is missing or has the wrong type.",
        )
    return value


def normalize_permission(value: str) -> str:
    return PERMISSION_ALIASES.get(value, value)


def compare_evidence(
    args: argparse.Namespace,
    user: Mapping[str, Any],
    repository: Mapping[str, Any],
    branch: Mapping[str, Any],
    permission: Mapping[str, Any],
) -> tuple[dict[str, Any], list[Finding]]:
    account = required_value(user, "login", str, "user")
    full_name = required_value(repository, "full_name", str, "repository")
    repository_id = required_value(repository, "id", int, "repository")
    default_branch = required_value(repository, "default_branch", str, "repository")

    commit = required_value(branch, "commit", dict, "default_branch")
    target_sha = required_value(commit, "sha", str, "default_branch.commit")
    observed_permission_raw = required_value(permission, "permission", str, "permission")
    observed_permission = normalize_permission(observed_permission_raw)
    if observed_permission not in PERMISSION_RANK:
        raise PreflightFailure(
            "unknown_permission", "GitHub returned an unrecognized collaborator permission."
        )

    permission_user = permission.get("user")
    permission_account = None
    if isinstance(permission_user, dict):
        permission_account = permission_user.get("login")
    if not isinstance(permission_account, str):
        raise PreflightFailure(
            "evidence_field_missing",
            "Required field permission.user.login is missing or has the wrong type.",
        )

    observed = {
        "account": account,
        "default_branch": default_branch,
        "permission": observed_permission,
        "permission_account": permission_account,
        "repository_full_name": full_name,
        "repository_id": repository_id,
        "target_sha": target_sha.lower(),
    }
    findings: list[Finding] = []
    expected_full_name = f"{args.owner}/{args.repo}"
    if account != args.expected_account:
        findings.append(Finding("account_mismatch", "Authenticated GitHub account does not match."))
    if permission_account != account:
        findings.append(
            Finding(
                "permission_account_mismatch",
                "Collaborator permission evidence belongs to a different account.",
            )
        )
    if full_name != expected_full_name:
        findings.append(Finding("repository_name_mismatch", "Repository full_name does not match."))
    if repository_id != args.expected_repository_id:
        findings.append(Finding("repository_id_mismatch", "Repository ID does not match."))
    if default_branch != args.expected_default_branch:
        findings.append(Finding("default_branch_mismatch", "Default branch does not match."))
    if target_sha.lower() != args.expected_target_sha.lower():
        findings.append(Finding("target_sha_mismatch", "Default-branch target SHA does not match."))
    if PERMISSION_RANK[observed_permission] < PERMISSION_RANK[args.required_permission]:
        findings.append(
            Finding("permission_insufficient", "Observed collaborator permission is insufficient.")
        )
    return observed, findings


def collect_live(args: argparse.Namespace) -> tuple[Mapping[str, Any], ...]:
    client = GhApiClient(args.host)
    owner = quote(args.owner, safe="")
    repo = quote(args.repo, safe="")
    branch = quote(args.expected_default_branch, safe="")

    user = client.get("user")
    login = required_value(user, "login", str, "user")
    login_path = quote(login, safe="")
    repository = client.get(f"repos/{owner}/{repo}")
    default_branch = client.get(f"repos/{owner}/{repo}/branches/{branch}")
    permission = client.get(f"repos/{owner}/{repo}/collaborators/{login_path}/permission")
    return user, repository, default_branch, permission


def collect_fixture(args: argparse.Namespace) -> tuple[Mapping[str, Any], ...]:
    client = FixtureClient(args.fixture_dir)
    return (
        client.get("user"),
        client.get("repository"),
        client.get("default_branch"),
        client.get("permission"),
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    request = safe_request(args)
    findings = validate_inputs(args)
    if findings:
        emit(
            {
                "errors": [item.as_dict() for item in findings],
                "evidence": evidence_metadata(args.fixture_dir is not None),
                "ok": False,
                "request": request,
            }
        )
        return EXIT_FAILED

    fixture_mode = args.fixture_dir is not None
    try:
        evidence = collect_fixture(args) if fixture_mode else collect_live(args)
        observed, comparison_findings = compare_evidence(args, *evidence)
    except PreflightFailure as exc:
        emit(
            {
                "errors": [exc.finding.as_dict()],
                "evidence": evidence_metadata(fixture_mode),
                "ok": False,
                "request": request,
            }
        )
        return EXIT_FAILED

    payload = {
        "errors": [item.as_dict() for item in comparison_findings],
        "evidence": evidence_metadata(fixture_mode, live_verified=not fixture_mode),
        "observed": observed,
        "ok": not comparison_findings,
        "request": request,
    }
    emit(payload)
    return EXIT_OK if payload["ok"] else EXIT_FAILED


if __name__ == "__main__":
    sys.exit(main())
