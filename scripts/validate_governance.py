#!/usr/bin/env python3
"""Deterministic, fail-closed governance validation for this repository."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from urllib.parse import unquote


CHECKOUT_SHA = "3d3c42e5aac5ba805825da76410c181273ba90b1"
POLICY_PATH = ".github/governance/repo-policy.yaml"
POLICY_SCHEMA_PATH = ".github/governance/repo-policy.schema.json"
README_CONTRACT_PATH = ".github/governance/readme-contract.json"
OWNERS_PATH = ".github/governance/owners.yaml"
CLAIMS_PATH = "docs/claims.yaml"
CODEOWNERS_PATH = ".github/CODEOWNERS"
MAIN_RULESET_PATH = ".github/governance/rulesets/main.json"
TAG_RULESET_PATH = ".github/governance/rulesets/freeze-all-tags-until-p5.json"
WORKFLOW_PATH = ".github/workflows/governance-baseline.yml"
EXPECTED_BASELINE_WORKFLOW = """name: governance-baseline

on:
  pull_request:
    branches:
      - main
  push:
    branches:
      - main
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: governance-baseline-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

jobs:
  governance-baseline:
    name: governance-baseline
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Checkout exact revision
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
        with:
          persist-credentials: false

      - name: Run deterministic tests
        shell: bash
        run: python3 -m unittest discover -s tests -p 'test_*.py'

      - name: Validate governance contracts
        shell: bash
        run: python3 scripts/validate_governance.py --root .
"""


@dataclass(frozen=True, order=True)
class Finding:
    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


class StrictYamlError(ValueError):
    pass


def _yaml_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        raise StrictYamlError("empty scalar")
    if value == "[]":
        return []
    if value == "{}":
        return {}
    if value in {"null", "Null", "NULL", "~"}:
        return None
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if re.fullmatch(r"-?(?:0|[1-9][0-9]*)", value):
        return int(value)
    if value.startswith(("'", '"')):
        try:
            if value.startswith('"'):
                return json.loads(value)
            if not value.endswith("'"):
                raise StrictYamlError("unterminated single-quoted scalar")
            return value[1:-1].replace("''", "'")
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise StrictYamlError(f"invalid quoted scalar: {exc}") from exc
    if " #" in value:
        value = value.split(" #", 1)[0].rstrip()
    return value


def parse_strict_yaml(text: str) -> Any:
    """Parse the small block-style YAML subset used by governance files.

    Anchors, aliases, tags, flow collections (except [] and {}), block scalars,
    tabs, duplicate keys, and irregular indentation are deliberately rejected.
    """

    rows: list[tuple[int, int, str]] = []
    for number, raw in enumerate(text.splitlines(), 1):
        if "\t" in raw:
            raise StrictYamlError(f"line {number}: tabs are forbidden")
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if indent % 2:
            raise StrictYamlError(f"line {number}: indentation must use two-space steps")
        if any(token in stripped for token in ("&", "*", "!!")):
            raise StrictYamlError(f"line {number}: YAML anchors, aliases, and tags are forbidden")
        if stripped in {"|", ">"} or stripped.endswith((" |", " >")):
            raise StrictYamlError(f"line {number}: block scalars are forbidden")
        rows.append((number, indent, stripped))
    if not rows:
        raise StrictYamlError("document is empty")

    def parse_block(index: int, indent: int) -> tuple[Any, int]:
        if index >= len(rows) or rows[index][1] != indent:
            line = rows[index][0] if index < len(rows) else "EOF"
            raise StrictYamlError(f"line {line}: unexpected indentation")
        is_list = rows[index][2].startswith("- ") or rows[index][2] == "-"
        container: Any = [] if is_list else {}
        while index < len(rows):
            number, current_indent, content = rows[index]
            if current_indent < indent:
                break
            if current_indent > indent:
                raise StrictYamlError(f"line {number}: unexpected indentation")
            row_is_list = content.startswith("- ") or content == "-"
            if row_is_list != is_list:
                raise StrictYamlError(f"line {number}: cannot mix mapping and sequence entries")
            if is_list:
                item_text = content[1:].strip()
                if not item_text:
                    if index + 1 >= len(rows) or rows[index + 1][1] <= indent:
                        raise StrictYamlError(f"line {number}: sequence item has no value")
                    item, index = parse_block(index + 1, rows[index + 1][1])
                    container.append(item)
                    continue
                if ":" in item_text and re.match(r"^[A-Za-z0-9_.-]+\s*:", item_text):
                    key, raw_value = item_text.split(":", 1)
                    item = {}
                    key = key.strip()
                    raw_value = raw_value.strip()
                    if raw_value:
                        item[key] = _yaml_scalar(raw_value)
                        index += 1
                    else:
                        if index + 1 >= len(rows) or rows[index + 1][1] <= indent:
                            raise StrictYamlError(f"line {number}: key {key!r} has no value")
                        item[key], index = parse_block(index + 1, rows[index + 1][1])
                    if index < len(rows) and rows[index][1] > indent:
                        extra_indent = rows[index][1]
                        extra, index = parse_block(index, extra_indent)
                        if not isinstance(extra, dict):
                            raise StrictYamlError(f"line {rows[index - 1][0]}: list mapping continuation must be a mapping")
                        duplicates = set(item).intersection(extra)
                        if duplicates:
                            raise StrictYamlError(f"duplicate key: {sorted(duplicates)[0]}")
                        item.update(extra)
                    container.append(item)
                    continue
                container.append(_yaml_scalar(item_text))
                index += 1
                continue

            if ":" not in content:
                raise StrictYamlError(f"line {number}: mapping entry lacks ':'")
            key, raw_value = content.split(":", 1)
            key = key.strip()
            raw_value = raw_value.strip()
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", key):
                raise StrictYamlError(f"line {number}: unsupported mapping key {key!r}")
            if key in container:
                raise StrictYamlError(f"line {number}: duplicate key {key!r}")
            if raw_value:
                container[key] = _yaml_scalar(raw_value)
                index += 1
            else:
                if index + 1 >= len(rows) or rows[index + 1][1] <= indent:
                    raise StrictYamlError(f"line {number}: key {key!r} has no value")
                container[key], index = parse_block(index + 1, rows[index + 1][1])
        return container, index

    result, final_index = parse_block(0, rows[0][1])
    if rows[0][1] != 0:
        raise StrictYamlError("root document must not be indented")
    if final_index != len(rows):
        raise StrictYamlError(f"line {rows[final_index][0]}: trailing content")
    return result


def _read_json(root: Path, relative: str, findings: list[Finding]) -> Any | None:
    path = root / relative
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        findings.append(Finding("required-file-missing", relative, "required file is missing"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        findings.append(Finding("invalid-json", relative, str(exc)))
    return None


def _read_yaml(root: Path, relative: str, findings: list[Finding]) -> Any | None:
    path = root / relative
    try:
        return parse_strict_yaml(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        findings.append(Finding("required-file-missing", relative, "required file is missing"))
    except (OSError, UnicodeError, StrictYamlError) as exc:
        findings.append(Finding("invalid-yaml", relative, str(exc)))
    return None


def _exact_keys(
    value: Any,
    required: set[str],
    path: str,
    findings: list[Finding],
) -> bool:
    if not isinstance(value, dict):
        findings.append(Finding("policy-type", path, "must be a mapping"))
        return False
    actual = set(value)
    for key in sorted(required - actual):
        findings.append(Finding("policy-field-missing", path, f"required field {key!r} is missing"))
    for key in sorted(actual - required):
        findings.append(Finding("policy-field-unknown", path, f"unknown field {key!r}"))
    return actual == required


def _expect(value: Any, expected: Any, path: str, findings: list[Finding]) -> None:
    if value != expected:
        findings.append(Finding("policy-invariant", path, f"expected {expected!r}, found {value!r}"))


def validate_policy(policy: Any, findings: list[Finding]) -> None:
    top = {
        "schema_version", "policy_status", "frozen_at", "p1_started_at", "repository", "license",
        "public_api", "release", "readme", "permissions",
        "credential_and_authority", "automation", "platform_enforcement",
    }
    if not _exact_keys(policy, top, POLICY_PATH, findings):
        if not isinstance(policy, dict):
            return
    _expect(policy.get("schema_version"), 2, f"{POLICY_PATH}:schema_version", findings)
    if policy.get("policy_status") not in {"p1-in-progress", "p1-enforced"}:
        findings.append(Finding("policy-enum", POLICY_PATH, "policy_status must be p1-in-progress or p1-enforced"))
    for date_field in ("frozen_at", "p1_started_at"):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(policy.get(date_field, ""))):
            findings.append(Finding("policy-date", POLICY_PATH, f"{date_field} must be YYYY-MM-DD"))

    shapes = {
        "repository": {"owner", "name", "visibility", "profile", "default_branch"},
        "license": {"spdx", "source_reuse_policy", "clean_room_assurance", "third_party_notices_required", "legacy_repository"},
        "public_api": {"definition"},
        "release": {
            "current_state", "active_version_authority", "active_release_authority",
            "planned_version_and_release_authority", "planned_activation_gate",
            "accountable_human_maintainer", "active_automated_release_owner_count",
            "release_please_enabled", "direct_default_branch_commit", "local_git_tag",
            "git_push_all_tags", "direct_gh_release_create", "gh_skill_publish_tag",
            "gh_skill_publish_dry_run", "existing_release_skill_write_access",
        },
        "readme": {"primary_locale", "files", "contract", "machine_checks", "human_checks"},
        "permissions": {"R", "W", "C"},
        "credential_and_authority": {
            "raw_credentials_in_repository", "raw_credentials_in_skill",
            "technical_capability_counts_as_delegated_authority",
            "standing_skill_write_authority", "standing_skill_commitment_authority",
        },
        "automation": {
            "ai_pr_reviewers_enabled", "agentic_workflows_enabled", "automated_merge_enabled",
            "automated_release_enabled", "automated_ruleset_changes_enabled",
            "automated_secret_changes_enabled",
        },
        "platform_enforcement": {
            "phase", "current_state", "issues", "required_check", "codeowners",
            "policy_schema", "actions", "rulesets", "vulnerability_reporting",
        },
    }
    for key, required in shapes.items():
        _exact_keys(policy.get(key), required, f"{POLICY_PATH}:{key}", findings)
    license_value = policy.get("license") if isinstance(policy.get("license"), dict) else {}
    _exact_keys(license_value.get("legacy_repository"), {"url", "reuse_mode", "text_or_code_copy_allowed"}, f"{POLICY_PATH}:license.legacy_repository", findings)
    readme = policy.get("readme") if isinstance(policy.get("readme"), dict) else {}
    _exact_keys(readme.get("files"), {"en", "zh-CN"}, f"{POLICY_PATH}:readme.files", findings)

    permissions = policy.get("permissions") if isinstance(policy.get("permissions"), dict) else {}
    for name in ("R", "W", "C"):
        item = permissions.get(name)
        path = f"{POLICY_PATH}:permissions.{name}"
        _exact_keys(item, {"description", "default_decision", "delegation_mode", "requires", "examples"}, path, findings)
        if not isinstance(item, dict):
            continue
        if item.get("default_decision") not in {"allow", "deny"}:
            findings.append(Finding("policy-enum", path, "default_decision must be allow or deny"))
        if item.get("delegation_mode") not in {"standing", "task-scoped", "per-action"}:
            findings.append(Finding("policy-enum", path, "delegation_mode has an unknown value"))
        for field in ("requires", "examples"):
            if not isinstance(item.get(field), list) or not all(isinstance(entry, str) for entry in item.get(field, [])):
                findings.append(Finding("policy-type", path, f"{field} must be a list of strings"))
    for path, expected in {
        "permissions.R.default_decision": "allow",
        "permissions.R.delegation_mode": "standing",
        "permissions.W.default_decision": "deny",
        "permissions.W.delegation_mode": "task-scoped",
        "permissions.C.default_decision": "deny",
        "permissions.C.delegation_mode": "per-action",
    }.items():
        _, group, field = path.split(".")
        item = permissions.get(group) if isinstance(permissions.get(group), dict) else {}
        _expect(item.get(field), expected, f"{POLICY_PATH}:{path}", findings)

    release = policy.get("release") if isinstance(policy.get("release"), dict) else {}
    release_invariants = {
        "current_state": "disabled-until-p5",
        "active_version_authority": None,
        "active_release_authority": None,
        "planned_version_and_release_authority": "release-please",
        "planned_activation_gate": "P5",
        "accountable_human_maintainer": "Rain3Dmetrology",
        "active_automated_release_owner_count": 0,
        "release_please_enabled": False,
        "direct_default_branch_commit": "forbidden-after-bootstrap",
        "local_git_tag": "forbidden",
        "git_push_all_tags": "forbidden",
        "direct_gh_release_create": "forbidden",
        "gh_skill_publish_tag": "forbidden",
        "gh_skill_publish_dry_run": "allowed-after-p3",
        "existing_release_skill_write_access": "forbidden",
    }
    for key, expected in release_invariants.items():
        _expect(release.get(key), expected, f"{POLICY_PATH}:release.{key}", findings)

    credential = policy.get("credential_and_authority") if isinstance(policy.get("credential_and_authority"), dict) else {}
    for key, expected in {
        "raw_credentials_in_repository": "forbidden",
        "raw_credentials_in_skill": "forbidden",
        "technical_capability_counts_as_delegated_authority": False,
        "standing_skill_write_authority": False,
        "standing_skill_commitment_authority": False,
    }.items():
        _expect(credential.get(key), expected, f"{POLICY_PATH}:credential_and_authority.{key}", findings)
    automation = policy.get("automation") if isinstance(policy.get("automation"), dict) else {}
    for key in shapes["automation"]:
        _expect(automation.get(key), False, f"{POLICY_PATH}:automation.{key}", findings)

    platform = policy.get("platform_enforcement") if isinstance(policy.get("platform_enforcement"), dict) else {}
    _expect(platform.get("phase"), "P1", f"{POLICY_PATH}:platform_enforcement.phase", findings)
    if platform.get("current_state") not in {"pending-remote-activation", "enforced"}:
        findings.append(Finding("policy-enum", f"{POLICY_PATH}:platform_enforcement.current_state", "unknown P1 enforcement state"))
    for key, expected in {
        "issues": [1, 2],
        "required_check": "governance-baseline",
        "codeowners": CODEOWNERS_PATH,
        "policy_schema": POLICY_SCHEMA_PATH,
    }.items():
        _expect(platform.get(key), expected, f"{POLICY_PATH}:platform_enforcement.{key}", findings)
    actions = platform.get("actions")
    _exact_keys(actions, {"allowed_external_uses", "local_actions_allowed", "sha_pinning_required", "default_workflow_permissions", "can_approve_pull_request_reviews"}, f"{POLICY_PATH}:platform_enforcement.actions", findings)
    if isinstance(actions, dict):
        for key, expected in {
            "allowed_external_uses": [f"actions/checkout@{CHECKOUT_SHA}"],
            "local_actions_allowed": False,
            "sha_pinning_required": True,
            "default_workflow_permissions": "read",
            "can_approve_pull_request_reviews": False,
        }.items():
            _expect(actions.get(key), expected, f"{POLICY_PATH}:platform_enforcement.actions.{key}", findings)
    rulesets = platform.get("rulesets")
    _exact_keys(rulesets, {"main_desired_state", "all_tag_desired_state", "bypass_actor_count", "required_approving_review_count", "independent_approval_enforced", "required_check_integration_id"}, f"{POLICY_PATH}:platform_enforcement.rulesets", findings)
    if isinstance(rulesets, dict):
        for key, expected in {
            "main_desired_state": MAIN_RULESET_PATH,
            "all_tag_desired_state": TAG_RULESET_PATH,
            "bypass_actor_count": 0,
            "required_approving_review_count": 0,
            "independent_approval_enforced": False,
        }.items():
            _expect(rulesets.get(key), expected, f"{POLICY_PATH}:platform_enforcement.rulesets.{key}", findings)
        integration_id = rulesets.get("required_check_integration_id")
        if integration_id is not None and (isinstance(integration_id, bool) or not isinstance(integration_id, int) or integration_id < 1):
            findings.append(Finding("policy-type", f"{POLICY_PATH}:platform_enforcement.rulesets.required_check_integration_id", "must be null or a positive integer"))
        status = policy.get("policy_status")
        state = platform.get("current_state")
        if status == "p1-in-progress":
            _expect(state, "pending-remote-activation", f"{POLICY_PATH}:platform_enforcement.current_state", findings)
            _expect(integration_id, None, f"{POLICY_PATH}:platform_enforcement.rulesets.required_check_integration_id", findings)
        elif status == "p1-enforced":
            _expect(state, "enforced", f"{POLICY_PATH}:platform_enforcement.current_state", findings)
            if isinstance(integration_id, bool) or not isinstance(integration_id, int) or integration_id < 1:
                findings.append(Finding("policy-state", f"{POLICY_PATH}:platform_enforcement.rulesets.required_check_integration_id", "p1-enforced requires the positive App integration ID observed on the target check run"))
    vulnerability = platform.get("vulnerability_reporting")
    _exact_keys(vulnerability, {"required"}, f"{POLICY_PATH}:platform_enforcement.vulnerability_reporting", findings)
    if isinstance(vulnerability, dict):
        _expect(vulnerability.get("required"), True, f"{POLICY_PATH}:platform_enforcement.vulnerability_reporting.required", findings)


def validate_rulesets(root: Path, policy: Any, findings: list[Finding]) -> None:
    """Require an exact, fail-closed ruleset state for each P1 transition."""

    main = _read_json(root, MAIN_RULESET_PATH, findings)
    tags = _read_json(root, TAG_RULESET_PATH, findings)
    if not isinstance(policy, dict) or not isinstance(main, dict) or not isinstance(tags, dict):
        return
    platform = policy.get("platform_enforcement")
    ruleset_policy = platform.get("rulesets") if isinstance(platform, dict) else None
    if not isinstance(ruleset_policy, dict):
        return
    integration_id = ruleset_policy.get("required_check_integration_id")
    enforced = policy.get("policy_status") == "p1-enforced" and platform.get("current_state") == "enforced"
    enforcement = "active" if enforced else "disabled"

    required_check: dict[str, Any] = {"context": "governance-baseline"}
    if enforced and isinstance(integration_id, int) and not isinstance(integration_id, bool):
        required_check["integration_id"] = integration_id
    expected_main = {
        "name": "p1-main-governance",
        "target": "branch",
        "enforcement": enforcement,
        "bypass_actors": [],
        "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
        "rules": [
            {"type": "deletion"},
            {"type": "non_fast_forward"},
            {"type": "required_linear_history"},
            {
                "type": "pull_request",
                "parameters": {
                    "allowed_merge_methods": ["squash"],
                    "dismiss_stale_reviews_on_push": False,
                    "require_code_owner_review": False,
                    "require_last_push_approval": False,
                    "required_approving_review_count": 0,
                    "required_review_thread_resolution": True,
                },
            },
            {
                "type": "required_status_checks",
                "parameters": {
                    "do_not_enforce_on_create": False,
                    "required_status_checks": [required_check],
                    "strict_required_status_checks_policy": True,
                },
            },
        ],
    }
    expected_tags = {
        "name": "p1-freeze-all-tags-until-p5",
        "target": "tag",
        "enforcement": enforcement,
        "bypass_actors": [],
        "conditions": {"ref_name": {"include": ["~ALL"], "exclude": []}},
        "rules": [
            {"type": "creation"},
            {"type": "update", "parameters": {"update_allows_fetch_and_merge": False}},
            {"type": "deletion"},
            {"type": "non_fast_forward"},
        ],
    }
    if main != expected_main:
        findings.append(Finding("ruleset-main-state", MAIN_RULESET_PATH, f"must exactly match the {enforcement} P1 main-ruleset state"))
    if tags != expected_tags:
        findings.append(Finding("ruleset-tag-state", TAG_RULESET_PATH, f"must exactly match the {enforcement} all-tag freeze state"))


def validate_policy_schema(schema: Any, policy: Any, findings: list[Finding]) -> None:
    path = POLICY_SCHEMA_PATH
    if not isinstance(schema, dict):
        findings.append(Finding("schema-type", path, "schema must be a JSON object"))
        return
    _expect(schema.get("$schema"), "https://json-schema.org/draft/2020-12/schema", f"{path}:$schema", findings)
    _expect(schema.get("type"), "object", f"{path}:type", findings)
    _expect(schema.get("additionalProperties"), False, f"{path}:additionalProperties", findings)
    required = schema.get("required")
    properties = schema.get("properties")
    if not isinstance(required, list) or not isinstance(properties, dict) or set(required) != set(properties):
        findings.append(Finding("schema-root-closed", path, "root required fields must exactly match properties"))

    def check_closed_objects(value: Any, location: str) -> None:
        if isinstance(value, dict):
            if value.get("type") == "object":
                if value.get("additionalProperties") is not False:
                    findings.append(Finding("schema-object-open", path, f"{location} must set additionalProperties to false"))
                object_properties = value.get("properties")
                object_required = value.get("required")
                if not isinstance(object_properties, dict) or not isinstance(object_required, list) or set(object_properties) != set(object_required):
                    findings.append(Finding("schema-object-required", path, f"{location} required fields must exactly match properties"))
            for key, child in value.items():
                check_closed_objects(child, f"{location}/{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                check_closed_objects(child, f"{location}/{index}")

    check_closed_objects(schema, "#")

    def resolve_ref(reference: str) -> Any:
        if not reference.startswith("#/"):
            raise ValueError("only local JSON Pointer references are allowed")
        current: Any = schema
        for token in reference[2:].split("/"):
            token = token.replace("~1", "/").replace("~0", "~")
            if not isinstance(current, dict) or token not in current:
                raise ValueError(f"unresolved reference {reference!r}")
            current = current[token]
        return current

    def type_matches(instance: Any, expected: str) -> bool:
        return {
            "object": isinstance(instance, dict),
            "array": isinstance(instance, list),
            "string": isinstance(instance, str),
            "integer": isinstance(instance, int) and not isinstance(instance, bool),
            "boolean": isinstance(instance, bool),
            "null": instance is None,
        }.get(expected, False)

    def matches_schema(rule: Any, instance: Any) -> bool:
        """Evaluate the assertion subset needed by conditional transitions."""

        if not isinstance(rule, dict):
            return False
        if "$ref" in rule:
            try:
                if not matches_schema(resolve_ref(rule["$ref"]), instance):
                    return False
            except (TypeError, ValueError):
                return False
        if "const" in rule and instance != rule["const"]:
            return False
        if "enum" in rule and instance not in rule["enum"]:
            return False
        expected_type = rule.get("type")
        if expected_type is not None:
            expected_types = [expected_type] if isinstance(expected_type, str) else expected_type
            if not isinstance(expected_types, list) or not any(type_matches(instance, item) for item in expected_types if isinstance(item, str)):
                return False
        if isinstance(instance, dict):
            required_fields = rule.get("required", [])
            if isinstance(required_fields, list) and not set(required_fields).issubset(instance):
                return False
            properties = rule.get("properties")
            if isinstance(properties, dict):
                for key, child in properties.items():
                    if key in instance and not matches_schema(child, instance[key]):
                        return False
        all_of = rule.get("allOf", [])
        if isinstance(all_of, list) and not all(matches_schema(child, instance) for child in all_of):
            return False
        return True

    def apply_schema(rule: Any, instance: Any, instance_path: str) -> None:
        if not isinstance(rule, dict):
            findings.append(Finding("schema-definition", path, f"schema at {instance_path} is not an object"))
            return
        reference = rule.get("$ref")
        if reference is not None:
            try:
                apply_schema(resolve_ref(reference), instance, instance_path)
            except ValueError as exc:
                findings.append(Finding("schema-reference", path, str(exc)))
        all_of = rule.get("allOf", [])
        if not isinstance(all_of, list):
            findings.append(Finding("schema-definition", path, f"allOf at {instance_path} must be an array"))
        else:
            for child in all_of:
                apply_schema(child, instance, instance_path)
        condition = rule.get("if")
        if condition is not None:
            branch = rule.get("then") if matches_schema(condition, instance) else rule.get("else")
            if branch is not None:
                apply_schema(branch, instance, instance_path)
        if "const" in rule and instance != rule["const"]:
            findings.append(Finding("schema-validation", instance_path, f"must equal {rule['const']!r}"))
        if "enum" in rule and instance not in rule["enum"]:
            findings.append(Finding("schema-validation", instance_path, f"must be one of {rule['enum']!r}"))
        expected_type = rule.get("type")
        if expected_type is not None:
            expected_types = [expected_type] if isinstance(expected_type, str) else expected_type
            if not isinstance(expected_types, list) or not all(isinstance(item, str) for item in expected_types):
                findings.append(Finding("schema-definition", path, f"invalid type at {instance_path}"))
                return
            if not any(type_matches(instance, item) for item in expected_types):
                findings.append(Finding("schema-validation", instance_path, f"must have type {expected_types!r}"))
                return
        if isinstance(instance, dict) and isinstance(rule.get("properties"), dict):
            properties = rule["properties"]
            required_fields = rule.get("required", [])
            if isinstance(required_fields, list):
                for key in sorted(set(required_fields) - set(instance)):
                    findings.append(Finding("schema-validation", instance_path, f"required field {key!r} is missing"))
            if rule.get("additionalProperties") is False:
                for key in sorted(set(instance) - set(properties)):
                    findings.append(Finding("schema-validation", instance_path, f"additional field {key!r} is forbidden"))
            for key, child_rule in properties.items():
                if key in instance:
                    apply_schema(child_rule, instance[key], f"{instance_path}.{key}")
        if isinstance(instance, list):
            if isinstance(rule.get("minItems"), int) and len(instance) < rule["minItems"]:
                findings.append(Finding("schema-validation", instance_path, f"requires at least {rule['minItems']} items"))
            if rule.get("uniqueItems") is True:
                serialized = [json.dumps(item, ensure_ascii=False, sort_keys=True) for item in instance]
                if len(serialized) != len(set(serialized)):
                    findings.append(Finding("schema-validation", instance_path, "items must be unique"))
            if "items" in rule:
                for index, item in enumerate(instance):
                    apply_schema(rule["items"], item, f"{instance_path}[{index}]")
        if isinstance(instance, str):
            if isinstance(rule.get("minLength"), int) and len(instance) < rule["minLength"]:
                findings.append(Finding("schema-validation", instance_path, f"requires at least {rule['minLength']} characters"))
            if rule.get("format") == "date" and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", instance):
                findings.append(Finding("schema-validation", instance_path, "must be an ISO YYYY-MM-DD date"))
        if isinstance(instance, int) and not isinstance(instance, bool) and isinstance(rule.get("minimum"), int) and instance < rule["minimum"]:
            findings.append(Finding("schema-validation", instance_path, f"must be >= {rule['minimum']}"))

    apply_schema(schema, policy, POLICY_PATH)


SECTION_RE = re.compile(r"<!--\s*readme-contract:section:([a-z0-9-]+)\s*-->(.*?)<!--\s*/readme-contract:section:\1\s*-->", re.DOTALL)
CLAIM_RE = re.compile(r"<!--\s*readme-contract:claim:([a-z0-9.-]+)\s*-->")
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")


def _sections(text: str, path: str, findings: list[Finding]) -> dict[str, str]:
    found: dict[str, str] = {}
    for match in SECTION_RE.finditer(text):
        name = match.group(1)
        if name in found:
            findings.append(Finding("readme-section-duplicate", path, f"section {name!r} occurs more than once"))
        found[name] = match.group(2)
    opens = re.findall(r"<!--\s*readme-contract:section:([a-z0-9-]+)\s*-->", text)
    closes = re.findall(r"<!--\s*/readme-contract:section:([a-z0-9-]+)\s*-->", text)
    if sorted(opens) != sorted(closes) or len(found) != len(opens):
        findings.append(Finding("readme-section-markers", path, "section markers are unbalanced or nested incorrectly"))
    return found


def _claims_registry(value: Any, findings: list[Finding]) -> dict[str, dict[str, Any]]:
    if not isinstance(value, dict) or set(value) != {"schema_version", "claims"} or value.get("schema_version") != 1:
        findings.append(Finding("claims-schema", CLAIMS_PATH, "expected only schema_version: 1 and claims"))
        return {}
    claims = value.get("claims")
    if not isinstance(claims, list):
        findings.append(Finding("claims-schema", CLAIMS_PATH, "claims must be a list"))
        return {}
    result: dict[str, dict[str, Any]] = {}
    allowed = {"id", "kind", "status", "verified_at", "issue", "evidence"}
    for index, claim in enumerate(claims):
        path = f"{CLAIMS_PATH}:claims[{index}]"
        if not isinstance(claim, dict):
            findings.append(Finding("claims-schema", path, "claim must be a mapping"))
            continue
        unknown = set(claim) - allowed
        if unknown:
            findings.append(Finding("claims-field-unknown", path, f"unknown fields: {sorted(unknown)}"))
        claim_id = claim.get("id")
        if not isinstance(claim_id, str) or not re.fullmatch(r"claim\.[a-z0-9.-]+", claim_id):
            findings.append(Finding("claim-id", path, "id must match claim.<lowercase-id>"))
            continue
        if claim_id in result:
            findings.append(Finding("claim-id-duplicate", path, f"duplicate claim {claim_id}"))
        result[claim_id] = claim
        if claim.get("status") not in {"implemented", "in-progress", "planned", "rejected"}:
            findings.append(Finding("claim-status", path, "unknown claim status"))
        evidence = claim.get("evidence")
        if claim.get("status") == "implemented" and (not isinstance(evidence, list) or not evidence):
            findings.append(Finding("claim-evidence", path, "implemented claim requires evidence"))
        if claim.get("status") == "planned" and not claim.get("issue"):
            findings.append(Finding("claim-issue", path, "planned claim requires an issue"))
        if claim.get("kind") == "comparative" and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(claim.get("verified_at", ""))):
            findings.append(Finding("claim-comparison-date", path, "comparative claim requires verified_at YYYY-MM-DD"))
    return result


def _local_link_path(readme_path: str, target: str) -> str | None:
    target = target.strip().strip("<>").split("#", 1)[0].split("?", 1)[0]
    if not target or re.match(r"^(?:[a-z][a-z0-9+.-]*:|//)", target, re.IGNORECASE):
        return None
    decoded = unquote(target).replace("\\", "/")
    combined = PurePosixPath(readme_path).parent / decoded
    normalized: list[str] = []
    for part in combined.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not normalized:
                return "../OUTSIDE_REPOSITORY"
            normalized.pop()
        else:
            normalized.append(part)
    return "/".join(normalized)


def validate_readmes(root: Path, contract: Any, claims_value: Any, findings: list[Finding]) -> None:
    path = README_CONTRACT_PATH
    if not isinstance(contract, dict):
        findings.append(Finding("readme-contract", path, "contract must be an object"))
        return
    required_contract = {"schemaVersion", "status", "primaryLocale", "locales", "requiredSections", "policies", "style", "allowedClaimStatuses"}
    if set(contract) != required_contract:
        findings.append(Finding("readme-contract-fields", path, "contract fields are not the frozen exact set"))
    locales = contract.get("locales")
    if locales != {"en": "README.md", "zh-CN": "README.zh-CN.md"}:
        findings.append(Finding("readme-locales", path, "locales must map en and zh-CN to the canonical README files"))
        return
    required_sections = contract.get("requiredSections")
    if not isinstance(required_sections, list) or len(required_sections) != len(set(required_sections)):
        findings.append(Finding("readme-contract-sections", path, "requiredSections must be a unique list"))
        return
    registry = _claims_registry(claims_value, findings)
    readmes: dict[str, tuple[str, dict[str, str], set[str]]] = {}
    for locale, relative in locales.items():
        try:
            text = (root / relative).read_text(encoding="utf-8-sig")
        except (FileNotFoundError, OSError, UnicodeError) as exc:
            findings.append(Finding("readme-read", relative, str(exc)))
            continue
        sections = _sections(text, relative, findings)
        claims = set(CLAIM_RE.findall(text))
        if set(sections) != set(required_sections):
            missing = sorted(set(required_sections) - set(sections))
            extra = sorted(set(sections) - set(required_sections))
            findings.append(Finding("readme-section-parity", relative, f"missing={missing}; extra={extra}"))
        nonempty = [line.strip() for line in text.splitlines() if line.strip()]
        marker = "<!-- readme-contract:section:value-proposition -->"
        try:
            position = nonempty.index(marker) + 1
        except ValueError:
            position = len(nonempty) + 1
        max_lines = contract.get("style", {}).get("valueSentenceWithinFirstNonEmptyLines")
        if not isinstance(max_lines, int) or position > max_lines:
            findings.append(Finding("readme-value-position", relative, "value proposition starts too late"))
        value = re.sub(r"\s+", " ", sections.get("value-proposition", "").strip())
        if locale == "en":
            count = len(re.findall(r"\b[\w'-]+\b", value, re.UNICODE))
            limit = contract.get("style", {}).get("englishValueSentenceMaxWords")
        else:
            count = len(re.sub(r"[\s\p{P}]", "", value)) if False else len(re.sub(r"\s+", "", value))
            limit = contract.get("style", {}).get("chineseValueSentenceMaxCharacters")
        if not isinstance(limit, int) or count > limit:
            findings.append(Finding("readme-value-length", relative, f"value proposition length {count} exceeds {limit}"))
        for raw_target in MARKDOWN_LINK_RE.findall(text):
            target = raw_target.split(maxsplit=1)[0]
            local = _local_link_path(relative, target)
            if local is not None and not (root / local).is_file():
                findings.append(Finding("readme-local-link", relative, f"missing local target {local!r}"))
        readmes[locale] = (text, sections, claims)
    if set(readmes) == {"en", "zh-CN"}:
        en_text, _, en_claims = readmes["en"]
        zh_text, _, zh_claims = readmes["zh-CN"]
        if "(./README.zh-CN.md)" not in en_text or "(./README.md)" not in zh_text:
            findings.append(Finding("readme-reciprocal-link", "README.md", "canonical reciprocal language links are required"))
        if en_claims != zh_claims:
            findings.append(Finding("readme-claim-parity", "README.md", f"en-only={sorted(en_claims - zh_claims)}; zh-only={sorted(zh_claims - en_claims)}"))
        if en_claims != set(registry):
            findings.append(Finding("readme-claim-registry", CLAIMS_PATH, f"README-only={sorted(en_claims - set(registry))}; registry-only={sorted(set(registry) - en_claims)}"))
        for claim_id, claim in registry.items():
            evidence = claim.get("evidence", [])
            if isinstance(evidence, list):
                for evidence_path in evidence:
                    if not isinstance(evidence_path, str) or not (root / evidence_path).is_file():
                        findings.append(Finding("claim-evidence-path", CLAIMS_PATH, f"{claim_id} evidence does not exist: {evidence_path!r}"))
            if claim.get("kind") == "comparative":
                date = str(claim.get("verified_at", ""))
                for locale, (text, _, _) in readmes.items():
                    if date not in text:
                        findings.append(Finding("claim-comparison-date", locales[locale], f"comparative claim {claim_id} omits date {date}"))


def validate_owners(root: Path, owners: Any, findings: list[Finding]) -> None:
    path = OWNERS_PATH
    if not isinstance(owners, dict):
        findings.append(Finding("owners-schema", path, "owners mapping must be an object"))
        return
    expected_top = {"schema_version", "maintainer", "semantic_review", "authority"}
    _exact_keys(owners, expected_top, path, findings)
    _expect(owners.get("schema_version"), 1, f"{path}:schema_version", findings)
    maintainer = owners.get("maintainer")
    if not isinstance(maintainer, str) or not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", maintainer):
        findings.append(Finding("owners-maintainer", path, "maintainer must be a valid GitHub login"))
        return
    semantic = owners.get("semantic_review")
    _exact_keys(semantic, {"owner", "model", "independent_reviewer_required", "limitation"}, f"{path}:semantic_review", findings)
    if isinstance(semantic, dict):
        _expect(semantic.get("owner"), maintainer, f"{path}:semantic_review.owner", findings)
        _expect(semantic.get("model"), "maintainer-self-review", f"{path}:semantic_review.model", findings)
        _expect(semantic.get("independent_reviewer_required"), False, f"{path}:semantic_review.independent_reviewer_required", findings)
        if not isinstance(semantic.get("limitation"), str) or not semantic.get("limitation", "").strip():
            findings.append(Finding("owners-limitation", path, "single-maintainer review limitation must be explicit"))
    authority = owners.get("authority")
    _exact_keys(authority, {"interactive_task_actor", "all_skills", "legacy_release_skill"}, f"{path}:authority", findings)
    if isinstance(authority, dict):
        _exact_keys(authority.get("interactive_task_actor"), {"capability_may_exceed_delegated_scope", "delegated_scope"}, f"{path}:authority.interactive_task_actor", findings)
        _exact_keys(authority.get("all_skills"), {"standing_write_authority", "standing_commitment_authority"}, f"{path}:authority.all_skills", findings)
        _exact_keys(authority.get("legacy_release_skill"), {"delegated_write_authority", "delegated_tag_or_release_authority"}, f"{path}:authority.legacy_release_skill", findings)
        for group, keys in {
            "all_skills": ("standing_write_authority", "standing_commitment_authority"),
            "legacy_release_skill": ("delegated_write_authority", "delegated_tag_or_release_authority"),
        }.items():
            values = authority.get(group) if isinstance(authority.get(group), dict) else {}
            for key in keys:
                _expect(values.get(key), False, f"{path}:authority.{group}.{key}", findings)
        interactive = authority.get("interactive_task_actor") if isinstance(authority.get("interactive_task_actor"), dict) else {}
        _expect(interactive.get("capability_may_exceed_delegated_scope"), True, f"{path}:authority.interactive_task_actor.capability_may_exceed_delegated_scope", findings)
        _expect(interactive.get("delegated_scope"), "current-task-and-action-only", f"{path}:authority.interactive_task_actor.delegated_scope", findings)
    codeowners = root / CODEOWNERS_PATH
    try:
        lines = [line.strip() for line in codeowners.read_text(encoding="utf-8-sig").splitlines() if line.strip() and not line.lstrip().startswith("#")]
    except (FileNotFoundError, OSError, UnicodeError) as exc:
        findings.append(Finding("codeowners-read", CODEOWNERS_PATH, str(exc)))
        return
    parsed: dict[str, list[str]] = {}
    for line in lines:
        fields = line.split()
        if len(fields) < 2 or not all(owner.startswith("@") for owner in fields[1:]):
            findings.append(Finding("codeowners-line", CODEOWNERS_PATH, f"invalid CODEOWNERS line: {line!r}"))
            continue
        parsed[fields[0]] = fields[1:]
    expected_owner = f"@{maintainer}"
    required_patterns = {
        "*",
        "/README.md",
        "/README.zh-CN.md",
        "/SECURITY.md",
        "/.github/governance/",
        "/.github/workflows/",
        "/docs/adr/",
        "/scripts/",
        "/tests/",
    }
    for pattern in sorted(required_patterns):
        if expected_owner not in parsed.get(pattern, []):
            findings.append(Finding("codeowners-owner", CODEOWNERS_PATH, f"pattern {pattern!r} must include {expected_owner}"))


def _tracked_files(root: Path) -> tuple[list[str], set[str], str | None]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--stage", "-z"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        return [], set(), str(exc)
    if result.returncode != 0:
        return [], set(), result.stderr.decode("utf-8", "replace").strip()
    paths: list[str] = []
    executable: set[str] = set()
    for record in result.stdout.decode("utf-8", "strict").split("\0"):
        if not record:
            continue
        try:
            metadata, path = record.split("\t", 1)
            mode = metadata.split(" ", 1)[0]
        except ValueError:
            return [], set(), "git ls-files --stage returned an unexpected record"
        paths.append(path)
        if mode == "100755":
            executable.add(path.replace("\\", "/"))
    return sorted(paths), executable, None


SENSITIVE_NAMES = (
    re.compile(r"(?:^|/)\.env(?:\..+)?$", re.IGNORECASE),
    re.compile(r"(?:^|/)(?:credentials|secrets)\.json$", re.IGNORECASE),
    re.compile(r"\.(?:key|pem|p12|pfx)$", re.IGNORECASE),
)
SECRET_PATTERNS = (
    ("github-token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{36,255}|github_pat_[A-Za-z0-9_]{50,255})\b")),
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("generic-secret-assignment", re.compile(r"(?im)^\s*(?:api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{16,}")),
)


def validate_workflow_permissions(text: str, path: str, findings: list[Finding]) -> None:
    """Require the exact workflow-level mapping and forbid job overrides."""

    lines = text.splitlines()
    headers: list[tuple[int, int, str]] = []
    for index, line in enumerate(lines):
        content = line.split("#", 1)[0].rstrip()
        match = re.fullmatch(r"( *)permissions[ ]*:[ ]*(.*)", content)
        if match:
            headers.append((index, len(match.group(1)), match.group(2).strip()))
    top_level = [header for header in headers if header[1] == 0]
    if len(top_level) != 1:
        findings.append(Finding("workflow-permissions", path, "workflow must declare exactly one top-level permissions mapping"))
    else:
        index, _, inline_value = top_level[0]
        if inline_value:
            findings.append(Finding("workflow-permissions", path, "permissions shorthand or inline values are forbidden"))
        entries: list[tuple[str, str]] = []
        malformed = False
        for following in lines[index + 1:]:
            content = following.split("#", 1)[0].rstrip()
            if not content.strip():
                continue
            indent = len(content) - len(content.lstrip(" "))
            if indent == 0:
                break
            entry = re.fullmatch(r"  ([A-Za-z0-9-]+)[ ]*:[ ]*(read|write|none)[ ]*", content)
            if indent != 2 or not entry:
                malformed = True
                continue
            entries.append((entry.group(1), entry.group(2)))
        if malformed or entries != [("contents", "read")]:
            findings.append(Finding("workflow-permissions", path, "top-level permissions must be exactly contents: read"))
    if any(indent > 0 for _, indent, _ in headers):
        findings.append(Finding("workflow-permissions", path, "job-level permissions overrides are forbidden"))


def validate_tracked_content(
    root: Path,
    tracked: Iterable[str],
    findings: list[Finding],
    executable_paths: Iterable[str] = (),
) -> None:
    executable_suffixes = {".sh", ".ps1", ".cmd", ".bat", ".py", ".js", ".mjs", ".cjs", ".ts", ".rb"}
    forbidden_commands = (
        ("release-command", re.compile(r"\bgh\s+release\s+create\b", re.IGNORECASE)),
        ("release-command", re.compile(r"\bgh\s+skill\s+publish\b", re.IGNORECASE)),
        ("tag-command", re.compile(r"\bgit\s+tag\b|\bgit\s+push\s+--tags\b", re.IGNORECASE)),
        ("publisher-command", re.compile(r"\b(?:npm|cargo)\s+publish\b|\btwine\s+upload\b", re.IGNORECASE)),
        ("release-automation", re.compile(r"release-please|action-gh-release", re.IGNORECASE)),
    )
    tracked_paths = sorted(set(tracked))
    executable_path_set = {path.replace("\\", "/") for path in executable_paths}
    workflow_paths = [
        relative.replace("\\", "/")
        for relative in tracked_paths
        if relative.replace("\\", "/").startswith(".github/workflows/")
    ]
    if workflow_paths != [WORKFLOW_PATH]:
        findings.append(Finding("workflow-inventory", ".github/workflows", f"tracked workflows must be exactly [{WORKFLOW_PATH!r}]"))
    for relative in tracked_paths:
        normalized = relative.replace("\\", "/")
        if normalized.startswith(".github/actions/"):
            findings.append(Finding("local-action-forbidden", normalized, "local GitHub Actions are forbidden in P1"))
        if normalized == ".env.example":
            name_sensitive = False
        else:
            name_sensitive = any(pattern.search(normalized) for pattern in SENSITIVE_NAMES)
        if name_sensitive:
            findings.append(Finding("sensitive-filename", normalized, "tracked sensitive credential filename is forbidden"))
        path = root / relative
        try:
            raw = path.read_bytes()
        except (FileNotFoundError, OSError) as exc:
            findings.append(Finding("tracked-file-read", normalized, str(exc)))
            continue
        if b"\0" in raw:
            continue
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            findings.append(Finding("tracked-text-encoding", normalized, "non-binary tracked file is not UTF-8"))
            continue
        for secret_name, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(Finding("secret-signature", normalized, f"matched {secret_name}"))
        is_workflow = normalized.startswith(".github/workflows/") and path.suffix.lower() in {".yml", ".yaml"}
        is_executable = (
            normalized in executable_path_set
            or text.startswith("#!")
            or path.suffix.lower() in executable_suffixes
            or path.name.lower() in {"makefile", "justfile", "package.json", "pyproject.toml"}
        ) and not normalized.startswith("tests/")
        if is_executable and normalized == "scripts/validate_governance.py":
            is_executable = False
        if is_workflow or is_executable:
            for command_name, pattern in forbidden_commands:
                if pattern.search(text):
                    findings.append(Finding(command_name, normalized, "release, tag, or publisher command is forbidden before P5"))
        if not is_workflow:
            continue
        canonical_text = text.replace("\r\n", "\n")
        if normalized == WORKFLOW_PATH and ("\r" in canonical_text or canonical_text != EXPECTED_BASELINE_WORKFLOW):
            findings.append(Finding("workflow-canonical", normalized, "P1 baseline workflow must match the frozen canonical form exactly"))
        for use in re.findall(r"(?m)^[ \t]*-?[ \t]*uses:[ \t]*['\"]?([^'\"\s#]+)", text):
            if use.startswith("./"):
                findings.append(Finding("local-action-forbidden", normalized, f"local action {use!r} is forbidden in P1"))
                continue
            expected = f"actions/checkout@{CHECKOUT_SHA}"
            if use != expected:
                findings.append(Finding("workflow-action-pin", normalized, f"external action {use!r} is forbidden; only {expected!r} is allowed"))
        workflow_lines = text.splitlines()
        checkout_line = re.compile(rf"^[ \t]*-?[ \t]*uses:[ \t]*['\"]?actions/checkout@{CHECKOUT_SHA}['\"]?[ \t]*$")
        persist_line = re.compile(r"^[ \t]*persist-credentials:[ \t]*false[ \t]*$", re.IGNORECASE)
        for index, line in enumerate(workflow_lines):
            if not checkout_line.match(line):
                continue
            uses_indent = len(line) - len(line.lstrip(" \t"))
            persist_disabled = False
            for following in workflow_lines[index + 1:]:
                stripped = following.strip()
                if not stripped:
                    continue
                following_indent = len(following) - len(following.lstrip(" \t"))
                if following_indent <= uses_indent and stripped.startswith("-"):
                    break
                if persist_line.match(following):
                    persist_disabled = True
                    break
            if not persist_disabled:
                findings.append(Finding("workflow-checkout-credentials", normalized, "actions/checkout must set persist-credentials: false"))
        validate_workflow_permissions(text, normalized, findings)
        if re.search(r"(?mi)^[ \t]*(?:release|registry_package)[ \t]*:", text) or re.search(r"(?mi)^[ \t]*tags(?:-ignore)?[ \t]*:", text):
            findings.append(Finding("workflow-release-trigger", normalized, "release, package, or tag trigger is forbidden before P5"))


def validate_repository(root: Path, tracked: Iterable[str] | None = None) -> dict[str, Any]:
    root = root.resolve()
    findings: list[Finding] = []
    policy = _read_yaml(root, POLICY_PATH, findings)
    schema = _read_json(root, POLICY_SCHEMA_PATH, findings)
    contract = _read_json(root, README_CONTRACT_PATH, findings)
    owners = _read_yaml(root, OWNERS_PATH, findings)
    claims = _read_yaml(root, CLAIMS_PATH, findings)
    if policy is not None:
        validate_policy(policy, findings)
        validate_rulesets(root, policy, findings)
    if schema is not None:
        validate_policy_schema(schema, policy, findings)
    if contract is not None and claims is not None:
        validate_readmes(root, contract, claims, findings)
    if owners is not None:
        validate_owners(root, owners, findings)
    tracked_list: list[str]
    executable_paths: set[str] = set()
    if tracked is None:
        tracked_list, executable_paths, git_error = _tracked_files(root)
        if git_error:
            findings.append(Finding("git-tracked-inventory", ".git", git_error))
    else:
        tracked_list = sorted(set(tracked))
    validate_tracked_content(root, tracked_list, findings, executable_paths)
    unique = sorted(set(findings))
    return {
        "check": "github-skill-governance",
        "errors": [finding.as_dict() for finding in unique],
        "ok": not unique,
        "schema_version": 1,
        "summary": {"errors": len(unique), "tracked_files": len(tracked_list)},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    result = validate_repository(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
