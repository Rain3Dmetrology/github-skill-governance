#!/usr/bin/env python3
"""Offline validator and read-only planner for bilingual repository READMEs."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass
from datetime import date
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping
from urllib.parse import unquote, urlsplit


VERSION = "1.0.0"
MAX_README_BYTES = 1_000_000
SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTRACT_PATH = SKILL_ROOT / "references" / "readme-contract.v1.json"
REQUIRED_SECTIONS_V1 = [
    "language-switch",
    "value-proposition",
    "why-this-repo",
    "quick-start",
    "comparison-and-tradeoffs",
    "current-limitations",
    "mitigations",
    "compatibility",
    "evidence",
    "roadmap",
    "security",
    "license",
]
STYLE_V1 = {
    "languageSwitchWithinFirstNonEmptyLines": 6,
    "valueSentenceWithinFirstNonEmptyLines": 12,
    "englishValueSentenceMaxWords": 25,
    "chineseValueSentenceMaxCharacters": 45,
}
POLICIES_V1 = {
    "reciprocalLanguageLinksRequired": True,
    "sectionIdParityRequired": True,
    "claimIdParityRequired": True,
    "localLinksBlocking": True,
    "externalLinksChecked": False,
    "comparisonDateAndEvidenceRequired": True,
    "limitationsAndMitigationsTablesRequired": True,
    "semanticReviewRequired": True,
    "extraPairedSectionsAllowed": True,
}
SECTION_RE = re.compile(
    r"<!--\s*readme-contract:section:([a-z0-9-]+)\s*-->"
    r"(.*?)"
    r"<!--\s*/readme-contract:section:\1\s*-->",
    re.DOTALL,
)
SECTION_OPEN_RE = re.compile(
    r"<!--\s*readme-contract:section:([a-z0-9-]+)\s*-->"
)
SECTION_CLOSE_RE = re.compile(
    r"<!--\s*/readme-contract:section:([a-z0-9-]+)\s*-->"
)
CLAIM_RE = re.compile(r"<!--\s*readme-contract:claim:([a-z0-9.-]+)\s*-->")
REFERENCE_LINK_RE = re.compile(
    r"^\s*\[([^\]]+)\]:\s*(<[^>]+>|\S+)", re.MULTILINE
)
AUTOLINK_RE = re.compile(r"<(https?://[^<>\s]+|mailto:[^<>\s]+)>", re.I)
PLACEHOLDER_RE = re.compile(r"\{\{[^{}]+\}\}")
TABLE_SEPARATOR_RE = re.compile(
    r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$"
)


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    path: str
    severity: str = "error"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class ContractError(ValueError):
    """Raised when the bundled or supplied contract is malformed."""


class ReadmeTooLarge(ValueError):
    """Raised before an oversized README is fully loaded."""


class _LinkHTMLParser(HTMLParser):
    def __init__(self, *, text_only: bool) -> None:
        super().__init__(convert_charrefs=True)
        self.text_only = text_only
        self.targets: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        allowed = {"href"} if self.text_only else {"href", "src"}
        for name, value in attrs:
            if name.casefold() in allowed and value:
                self.targets.append(value)

    handle_startendtag = handle_starttag


def _exact_keys(value: object, expected: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    if set(value) != expected:
        raise ContractError(
            f"{label} keys must be exactly {sorted(expected)}; got {sorted(value)}"
        )
    return value


def load_contract(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read contract: {exc}") from exc
    contract = _exact_keys(
        value,
        {"schemaVersion", "locales", "requiredSections", "style", "policies"},
        "contract",
    )
    if contract.get("schemaVersion") != 1:
        raise ContractError("contract.schemaVersion must equal 1")
    if contract.get("locales") != {
        "en": "README.md",
        "zh-CN": "README.zh-CN.md",
    }:
        raise ContractError("contract.locales must use the canonical README pair")
    sections = contract.get("requiredSections")
    if sections != REQUIRED_SECTIONS_V1:
        raise ContractError("contract.requiredSections does not match frozen v1")
    style = _exact_keys(
        contract.get("style"),
        {
            "languageSwitchWithinFirstNonEmptyLines",
            "valueSentenceWithinFirstNonEmptyLines",
            "englishValueSentenceMaxWords",
            "chineseValueSentenceMaxCharacters",
        },
        "contract.style",
    )
    if not all(isinstance(value, int) and value > 0 for value in style.values()):
        raise ContractError("all contract.style limits must be positive integers")
    if style != STYLE_V1:
        raise ContractError("contract.style does not match frozen v1")
    policies = _exact_keys(
        contract.get("policies"),
        {
            "reciprocalLanguageLinksRequired",
            "sectionIdParityRequired",
            "claimIdParityRequired",
            "localLinksBlocking",
            "externalLinksChecked",
            "comparisonDateAndEvidenceRequired",
            "limitationsAndMitigationsTablesRequired",
            "semanticReviewRequired",
            "extraPairedSectionsAllowed",
        },
        "contract.policies",
    )
    if not all(isinstance(value, bool) for value in policies.values()):
        raise ContractError("all contract.policies values must be booleans")
    if policies != POLICIES_V1:
        raise ContractError("contract.policies does not match frozen v1")
    return contract


def _read_text(path: Path) -> tuple[str, bytes]:
    with path.open("rb") as handle:
        raw = handle.read(MAX_README_BYTES + 1)
    if len(raw) > MAX_README_BYTES:
        raise ReadmeTooLarge(
            f"README exceeds the {MAX_README_BYTES}-byte deterministic limit"
        )
    return raw.decode("utf-8-sig"), raw


def _sections(text: str, path: str, findings: list[Finding]) -> dict[str, str]:
    result: dict[str, str] = {}
    for match in SECTION_RE.finditer(text):
        section_id = match.group(1)
        if section_id in result:
            findings.append(
                Finding(
                    "section_duplicate",
                    f"section {section_id!r} occurs more than once",
                    path,
                )
            )
        result[section_id] = match.group(2)
    opens = SECTION_OPEN_RE.findall(text)
    closes = SECTION_CLOSE_RE.findall(text)
    if sorted(opens) != sorted(closes) or len(result) != len(opens):
        findings.append(
            Finding(
                "section_markers_invalid",
                "section markers are unbalanced, duplicated, or nested",
                path,
            )
        )
    return result


def _clean_link_target(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        return target[1 : target.index(">")]
    return target.split(maxsplit=1)[0]


def _markup_outside_code(text: str) -> str:
    visible_lines: list[str] = []
    fence: tuple[str, int] | None = None
    for line in text.splitlines():
        if fence is not None:
            closing = re.match(r"^ {0,3}(`{3,}|~{3,})\s*$", line)
            if (
                closing
                and closing.group(1)[0] == fence[0]
                and len(closing.group(1)) >= fence[1]
            ):
                fence = None
            continue
        opening = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if opening:
            run = opening.group(1)
            fence = (run[0], len(run))
            continue
        if line.startswith(("    ", "\t")):
            continue
        visible_lines.append(line)
    without_code = "\n".join(visible_lines)
    without_code = re.sub(
        r"(?is)<(pre|code)\b[^>]*>.*?</\1\s*>", "", without_code
    )
    without_code = re.sub(r"(?is)<(?:pre|code)\b[^>]*>.*$", "", without_code)
    without_code = re.sub(r"(`+)[^\n]*?\1", "CODE", without_code)
    without_code = re.sub(r"`+[^`\n]*$", "", without_code, flags=re.MULTILINE)
    return without_code


def _visible_markup(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", _markup_outside_code(text), flags=re.DOTALL)


def _is_escaped(text: str, index: int) -> bool:
    backslashes = 0
    index -= 1
    while index >= 0 and text[index] == "\\":
        backslashes += 1
        index -= 1
    return backslashes % 2 == 1


def _balanced_end(text: str, start: int, opening: str, closing: str) -> int | None:
    if start >= len(text) or text[start] != opening:
        return None
    depth = 1
    cursor = start + 1
    while cursor < len(text):
        if _is_escaped(text, cursor):
            cursor += 1
            continue
        if text[cursor] == opening:
            depth += 1
        elif text[cursor] == closing:
            depth -= 1
            if depth == 0:
                return cursor
        cursor += 1
    return None


def _render_link_label(label: str) -> str:
    rendered: list[str] = []
    cursor = 0
    while cursor < len(label):
        is_image = (
            label[cursor] == "!"
            and cursor + 1 < len(label)
            and label[cursor + 1] == "["
            and not _is_escaped(label, cursor)
        )
        label_start = cursor + 1 if is_image else cursor
        if label[label_start] == "[" and not _is_escaped(label, label_start):
            label_end = _balanced_end(label, label_start, "[", "]")
            if label_end is not None and label_end + 1 < len(label):
                suffix_open = label[label_end + 1]
                if suffix_open in "([":
                    suffix_close = ")" if suffix_open == "(" else "]"
                    suffix_end = _balanced_end(
                        label, label_end + 1, suffix_open, suffix_close
                    )
                    if suffix_end is not None:
                        if not is_image:
                            rendered.append(
                                _render_link_label(label[label_start + 1 : label_end])
                            )
                        cursor = suffix_end + 1
                        continue
        rendered.append(label[cursor])
        cursor += 1
    visible = html.unescape("".join(rendered))
    return re.sub(r"<[^>]*>|<!--.*?-->|[*_`~]", "", visible)


def _markdown_link_targets(
    text: str, *, definitions: Mapping[str, str], text_only: bool
) -> list[str]:
    targets: list[str] = []
    label_start = 0
    while label_start < len(text):
        label_start = text.find("[", label_start)
        if label_start < 0:
            break
        if _is_escaped(text, label_start):
            label_start += 1
            continue
        label_end = _balanced_end(text, label_start, "[", "]")
        if label_end is None or label_end + 1 >= len(text):
            label_start += 1
            continue
        label = text[label_start + 1 : label_end]
        suffix_open = text[label_end + 1]
        if suffix_open in "([":
            suffix_close = ")" if suffix_open == "(" else "]"
            suffix_end = _balanced_end(
                text, label_end + 1, suffix_open, suffix_close
            )
            if suffix_end is None:
                label_start += 1
                continue
            if suffix_open == "(":
                target = text[label_end + 2 : suffix_end]
            else:
                reference_label = text[label_end + 2 : suffix_end]
                key = (reference_label or label).strip().casefold()
                target = definitions.get(key)
        else:
            line_start = text.rfind("\n", 0, label_start) + 1
            line_end = text.find("\n", label_end + 1)
            if line_end < 0:
                line_end = len(text)
            definition = (
                not text[line_start:label_start].strip()
                and text[label_end + 1 : line_end].lstrip().startswith(":")
            )
            key = label.strip().casefold()
            if definition:
                label_start += 1
                continue
            target = definitions.get(key)
        is_image = (
            label_start > 0
            and text[label_start - 1] == "!"
            and not _is_escaped(text, label_start - 1)
        )
        label_is_visible = any(
            character.isalnum() for character in _render_link_label(label)
        )
        if target is not None and (not text_only or (not is_image and label_is_visible)):
            targets.append(target)
        label_start += 1
    return targets


def _inline_link_targets(text: str, *, text_only: bool) -> list[str]:
    return _markdown_link_targets(text, definitions={}, text_only=text_only)


def _html_link_targets(text: str, *, text_only: bool) -> list[str]:
    parser = _LinkHTMLParser(text_only=text_only)
    parser.feed(text)
    parser.close()
    return parser.targets


def _link_targets(text: str) -> list[str]:
    without_code = _visible_markup(text)
    definitions = {
        label.strip().casefold(): target
        for label, target in REFERENCE_LINK_RE.findall(without_code)
    }
    return (
        _markdown_link_targets(
            without_code, definitions=definitions, text_only=False
        )
        + _html_link_targets(without_code, text_only=False)
        + AUTOLINK_RE.findall(without_code)
    )


def _text_link_targets(text: str) -> list[str]:
    visible = _visible_markup(text)
    definitions = {
        label.strip().casefold(): target
        for label, target in REFERENCE_LINK_RE.findall(visible)
    }
    return (
        _markdown_link_targets(visible, definitions=definitions, text_only=True)
        + _html_link_targets(visible, text_only=True)
        + AUTOLINK_RE.findall(visible)
    )


def _classify_link(root: Path, readme_path: str, raw: str) -> tuple[str, str]:
    target = _clean_link_target(raw)
    if re.match(r"^[A-Za-z]:[\\/]", target):
        return "outside", target
    parsed = urlsplit(target)
    if parsed.scheme.lower() in {"data", "file", "javascript", "vbscript"}:
        return "unsafe", target
    if parsed.scheme or parsed.netloc:
        return "external", target
    decoded = unquote(parsed.path).replace("\\", "/")
    if not decoded:
        return "anchor", target
    if decoded.startswith("/") or re.match(r"^[A-Za-z]:", decoded):
        return "outside", decoded
    combined = PurePosixPath(readme_path).parent / PurePosixPath(decoded)
    normalized: list[str] = []
    for part in combined.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not normalized:
                return "outside", decoded
            normalized.pop()
        else:
            normalized.append(part)
    relative = "/".join(normalized)
    candidate = (root / Path(*normalized)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return "outside", relative
    return "local", relative


def _is_exact_case_file(root: Path, relative: str) -> bool:
    current = root
    for part in PurePosixPath(relative).parts:
        try:
            names = {child.name for child in current.iterdir()}
        except OSError:
            return False
        if part not in names:
            return False
        current = current / part
    return current.is_file()


def _has_nonempty_table(value: str) -> bool:
    lines = [
        line.strip() for line in _visible_markup(value).splitlines() if line.strip()
    ]
    separators = [index for index, line in enumerate(lines) if TABLE_SEPARATOR_RE.match(line)]
    for index in separators:
        if index >= 1 and index + 1 < len(lines):
            header = [cell.strip() for cell in lines[index - 1].strip("|").split("|")]
            if not any(header):
                continue
            for line in lines[index + 1 :]:
                if "|" not in line:
                    break
                data = [cell.strip() for cell in line.strip("|").split("|")]
                visible_data = []
                for cell in data:
                    rendered = html.unescape(cell)
                    rendered = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", rendered)
                    rendered = re.sub(
                        r"(?<!!)\[([^\]]*)\]\([^)]+\)", r"\1", rendered
                    )
                    rendered = re.sub(
                        r"(?<!!)\[([^\]]*)\]\[[^\]]*\]", r"\1", rendered
                    )
                    rendered = re.sub(r"<[^>]*>|<!--.*?-->|[*_`~]", "", rendered)
                    visible_data.append(rendered)
                if (
                    len(header) == len(data)
                    and any(
                        any(character.isalnum() for character in cell)
                        for cell in visible_data
                    )
                ):
                    return True
    return False


def _value_character_count(value: str) -> int:
    return sum(
        1
        for character in value
        if not character.isspace()
        and not unicodedata.category(character).startswith(("P", "S"))
    )


def _sentence_terminator_count(value: str) -> int:
    without_abbreviations = re.sub(
        r"\b(?:e\.g|i\.e|u\.s|u\.k|etc|vs|mr|mrs|ms|dr|prof)\.",
        lambda match: match.group(0).replace(".", ""),
        value,
        flags=re.I,
    )
    without_embedded_periods = re.sub(
        r"(?<=[A-Za-z0-9])\.(?=[a-z0-9])", "", without_abbreviations
    )
    return len(re.findall(r"[.!?。！？]+", without_embedded_periods))


def _validate_value(
    *,
    locale: str,
    relative: str,
    text: str,
    sections: Mapping[str, str],
    style: Mapping[str, Any],
    findings: list[Finding],
) -> None:
    marker = "<!-- readme-contract:section:value-proposition -->"
    nonempty = [line.strip() for line in text.splitlines() if line.strip()]
    position = nonempty.index(marker) + 1 if marker in nonempty else len(nonempty) + 1
    if position > style["valueSentenceWithinFirstNonEmptyLines"]:
        findings.append(
            Finding(
                "value_position",
                "value proposition starts too late in the README",
                relative,
            )
        )
    raw_value = sections.get("value-proposition", "").strip()
    paragraphs = [item for item in re.split(r"\n\s*\n", raw_value) if item.strip()]
    value = re.sub(r"\s+", " ", raw_value)
    if (
        len(paragraphs) != 1
        or not value
        or value.startswith(("#", "-", "*", "|", ">", "```"))
        or value[-1:] not in ".?!。！？"
        or _sentence_terminator_count(value) != 1
    ):
        findings.append(
            Finding(
                "value_not_one_sentence",
                "value proposition must be one prose paragraph ending in sentence punctuation",
                relative,
            )
        )
    if locale == "en":
        count = len(re.findall(r"\b[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*\b", value))
        limit = style["englishValueSentenceMaxWords"]
    else:
        count = _value_character_count(value)
        limit = style["chineseValueSentenceMaxCharacters"]
    if count > limit:
        findings.append(
            Finding(
                "value_too_long",
                f"value proposition length {count} exceeds limit {limit}",
                relative,
            )
        )


def _validate_language_switch(
    *,
    locale: str,
    relative: str,
    text: str,
    sections: Mapping[str, str],
    style: Mapping[str, Any],
    findings: list[Finding],
) -> None:
    marker = "<!-- readme-contract:section:language-switch -->"
    nonempty = [line.strip() for line in text.splitlines() if line.strip()]
    position = nonempty.index(marker) + 1 if marker in nonempty else len(nonempty) + 1
    if position > style["languageSwitchWithinFirstNonEmptyLines"]:
        findings.append(
            Finding(
                "language_switch_position",
                "language switch starts too late in the README",
                relative,
            )
        )
    expected = "./README.zh-CN.md" if locale == "en" else "./README.md"
    visible = _visible_markup(sections.get("language-switch", ""))
    targets = {
        _clean_link_target(target)
        for target in _inline_link_targets(visible, text_only=True)
    }
    if expected not in targets:
        findings.append(
            Finding(
                "reciprocal_language_link_missing",
                f"language-switch section must link to {expected}",
                relative,
            )
        )


def _has_valid_iso_date(value: str) -> bool:
    labelled_date = re.compile(
        r"(?:Assessment[ \t]+date|评估日期)[ \t]*[:：][ \t]*"
        r"(?:[*_~]+[ \t]*)?(\d{4}-\d{2}-\d{2})(?:[ \t]*[*_~]+)?",
        re.I,
    )
    for candidate in labelled_date.findall(_visible_markup(value)):
        try:
            date.fromisoformat(candidate)
        except ValueError:
            continue
        return True
    return False


def _has_evidence_link(root: Path, relative: str, value: str) -> bool:
    for raw in _text_link_targets(value):
        target = _clean_link_target(raw)
        parsed = urlsplit(target)
        if parsed.scheme.lower() in {"http", "https"} and parsed.netloc:
            return True
        kind, local = _classify_link(root, relative, raw)
        if kind == "local" and _is_exact_case_file(root, local):
            return True
    return False


def _validate_content_sections(
    root: Path,
    relative: str,
    sections: Mapping[str, str],
    findings: list[Finding],
) -> None:
    comparison = sections.get("comparison-and-tradeoffs", "")
    if not _has_nonempty_table(comparison):
        findings.append(
            Finding(
                "comparison_table_missing",
                "comparison section requires a non-empty Markdown table",
                relative,
            )
        )
    if not _has_valid_iso_date(comparison):
        findings.append(
            Finding(
                "comparison_date_missing",
                "comparison section requires an ISO assessment date",
                relative,
            )
        )
    if not _has_evidence_link(root, relative, comparison):
        findings.append(
            Finding(
                "comparison_evidence_missing",
                "comparison section requires at least one evidence link",
                relative,
            )
        )
    for section_id in ("current-limitations", "mitigations"):
        if not _has_nonempty_table(sections.get(section_id, "")):
            findings.append(
                Finding(
                    f"{section_id}_table_missing",
                    f"{section_id} requires a non-empty Markdown table",
                    relative,
                )
            )
    if not _has_evidence_link(root, relative, sections.get("evidence", "")):
        findings.append(
            Finding(
                "evidence_link_missing",
                "evidence section requires at least one link",
                relative,
            )
        )
    if not re.search(r"\blicense\b|许可证|许可", sections.get("license", ""), re.I):
        findings.append(
            Finding(
                "license_notice_missing",
                "license section must identify the repository license or notice",
                relative,
            )
        )


def validate_repository(root: Path, contract_path: Path = DEFAULT_CONTRACT_PATH) -> dict[str, Any]:
    root = root.resolve()
    contract = load_contract(contract_path.resolve())
    locales = contract["locales"]
    required = set(contract["requiredSections"])
    style = contract["style"]
    findings: list[Finding] = []
    warnings: list[Finding] = []
    documents: dict[str, dict[str, Any]] = {}
    total_external_links = 0

    if not root.is_dir():
        findings.append(Finding("root_missing", "target root is not a directory", "."))
    else:
        for locale, relative in locales.items():
            path = root / relative
            if path.is_symlink():
                findings.append(
                    Finding(
                        "readme_symlink_forbidden",
                        "canonical README files must not be symbolic links",
                        relative,
                    )
                )
                continue
            try:
                text, raw = _read_text(path)
            except FileNotFoundError:
                findings.append(Finding("readme_missing", "required README is missing", relative))
                continue
            except (OSError, UnicodeError) as exc:
                findings.append(Finding("readme_unreadable", str(exc), relative))
                continue
            except ReadmeTooLarge as exc:
                findings.append(Finding("readme_too_large", str(exc), relative))
                continue

            structural_text = _markup_outside_code(text)
            sections = _sections(structural_text, relative, findings)
            missing = sorted(required - set(sections))
            if missing:
                findings.append(
                    Finding(
                        "required_sections_missing",
                        f"missing sections: {missing}",
                        relative,
                    )
                )
            if PLACEHOLDER_RE.search(text):
                findings.append(
                    Finding(
                        "template_placeholder_present",
                        "draft template placeholders must be replaced",
                        relative,
                    )
                )

            _validate_value(
                locale=locale,
                relative=relative,
                text=structural_text,
                sections=sections,
                style=style,
                findings=findings,
            )
            _validate_language_switch(
                locale=locale,
                relative=relative,
                text=structural_text,
                sections=sections,
                style=style,
                findings=findings,
            )
            _validate_content_sections(root, relative, sections, findings)

            local_links = 0
            external_links = 0
            for raw_target in _link_targets(text):
                kind, target = _classify_link(root, relative, raw_target)
                if kind == "external":
                    external_links += 1
                elif kind == "unsafe":
                    findings.append(
                        Finding(
                            "unsafe_link_scheme",
                            f"unsafe link scheme is forbidden: {target!r}",
                            relative,
                        )
                    )
                elif kind == "outside":
                    findings.append(
                        Finding(
                            "local_link_outside_repository",
                            f"link escapes repository: {target!r}",
                            relative,
                        )
                    )
                elif kind == "local":
                    local_links += 1
                    if not _is_exact_case_file(root, target):
                        findings.append(
                            Finding(
                                "local_link_missing",
                                f"local link target does not exist: {target!r}",
                                relative,
                            )
                        )
            total_external_links += external_links
            documents[locale] = {
                "bytes": len(raw),
                "claims": sorted(set(CLAIM_RE.findall(structural_text))),
                "external_links": external_links,
                "local_links": local_links,
                "path": relative,
                "sections": sorted(sections),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }

    if set(documents) == set(locales):
        en = documents["en"]
        zh = documents["zh-CN"]
        if en["sections"] != zh["sections"]:
            findings.append(
                Finding(
                    "section_parity_mismatch",
                    "English and Chinese section IDs must match exactly",
                    "README.md",
                )
            )
        if en["claims"] != zh["claims"]:
            findings.append(
                Finding(
                    "claim_parity_mismatch",
                    "English and Chinese claim IDs must match exactly",
                    "README.md",
                )
            )

    if total_external_links:
        warnings.append(
            Finding(
                "external_links_unchecked",
                f"{total_external_links} external links were inventoried but not fetched",
                "README.md",
                "warning",
            )
        )
    warnings.append(
        Finding(
            "semantic_review_required",
            "deterministic validation does not certify truth, translation parity, or preservation",
            "README.md",
            "warning",
        )
    )
    return {
        "authority_class": "R",
        "contract_version": contract["schemaVersion"],
        "documents": documents,
        "errors": [finding.to_dict() for finding in findings],
        "mutation_performed": False,
        "network_used": False,
        "ok": not findings,
        "result": "PASS" if not findings else "FAIL",
        "schema_version": 1,
        "semantic_review": {"attested": False, "required": True},
        "target": root.name,
        "warnings": [warning.to_dict() for warning in warnings],
    }


ACTION_BY_CODE = {
    "readme_missing": "Create the missing locale from the matching asset template, then replace every placeholder.",
    "required_sections_missing": "Add the missing paired section markers without deleting existing content.",
    "section_parity_mismatch": "Give both locales the same section IDs while preserving natural language.",
    "claim_parity_mismatch": "Reconcile claim IDs and verify each claim against evidence.",
    "reciprocal_language_link_missing": "Add the canonical reciprocal language link near the top of both files.",
    "language_switch_position": "Move the reciprocal language switch into the first six non-empty lines.",
    "value_position": "Move the value proposition into the first 12 non-empty lines.",
    "value_not_one_sentence": "Rewrite the value proposition as one evidence-backed sentence.",
    "value_too_long": "Shorten the value sentence without adding unsupported superlatives.",
    "comparison_table_missing": "Add a fair project-versus-alternative comparison table.",
    "comparison_date_missing": "Date the comparison with an ISO YYYY-MM-DD assessment date.",
    "comparison_evidence_missing": "Link the comparison to repository evidence or cited research.",
    "current-limitations_table_missing": "Add at least one material limitation and its user impact.",
    "mitigations_table_missing": "Pair each material limitation with mitigation, permanent path, and state.",
    "evidence_link_missing": "Add at least one verifiable evidence link.",
    "license_notice_missing": "Restore the repository license and existing attribution notices.",
    "local_link_missing": "Repair or remove the broken local link only after checking intended content.",
    "local_link_outside_repository": "Replace the escaping path with a repository-contained or explicit external link.",
    "unsafe_link_scheme": "Replace the unsafe URI with a repository-relative or HTTPS link.",
    "readme_symlink_forbidden": "Replace the canonical README symlink with a reviewed regular file inside the repository.",
    "readme_too_large": "Reduce the README below one megabyte and move detailed material into linked documents.",
    "template_placeholder_present": "Replace all template placeholders with repository-specific, verified content.",
}


def plan_repository(root: Path, contract_path: Path = DEFAULT_CONTRACT_PATH) -> dict[str, Any]:
    validation = validate_repository(root, contract_path)
    steps: list[str] = []
    for finding in validation["errors"]:
        step = ACTION_BY_CODE.get(
            finding["code"],
            f"Resolve {finding['code']} in {finding['path']} without deleting unrelated content.",
        )
        if step not in steps:
            steps.append(step)
    if not steps:
        steps.append(
            "No deterministic edit is required; perform semantic truth, parity, and preservation review."
        )
    return {
        "allowed_write_scope_after_task_authorization": [
            "README.md",
            "README.zh-CN.md",
        ],
        "authority_class": "R",
        "errors": [],
        "forbidden_effects": [
            "direct-main-write",
            "pull-request-merge",
            "tag",
            "release",
            "deployment",
            "secret-change",
            "repository-control-change",
        ],
        "mutation_performed": False,
        "network_used": False,
        "ok": True,
        "schema_version": 1,
        "steps": steps,
        "target": root.resolve().name,
        "validation": validation,
    }


def _emit_text(payload: Mapping[str, Any]) -> None:
    print(f"result: {payload.get('result', 'PLAN')}")
    validation = payload.get("validation", payload)
    if isinstance(validation, dict):
        for finding in validation.get("errors", []):
            print(f"{finding['severity']}: {finding['path']}: {finding['code']}: {finding['message']}")
    for step in payload.get("steps", []):
        print(f"step: {step}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "plan"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--root", type=Path, required=True)
        subparser.add_argument("--format", choices=("json", "text"), default="json")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        payload = (
            validate_repository(args.root)
            if args.command == "validate"
            else plan_repository(args.root)
        )
    except ContractError as exc:
        payload = {
            "authority_class": "R",
            "errors": [
                Finding(
                    "contract_invalid",
                    str(exc),
                    "references/readme-contract.v1.json",
                ).to_dict()
            ],
            "mutation_performed": False,
            "network_used": False,
            "ok": False,
            "result": "ERROR",
            "schema_version": 1,
        }
        exit_code = 2
    else:
        exit_code = 0 if args.command == "plan" or payload["ok"] else 1
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        _emit_text(payload)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
