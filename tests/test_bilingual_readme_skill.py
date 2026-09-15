from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "bilingual-readme-governance"
SCRIPT_PATH = SKILL_ROOT / "scripts" / "readme_governance.py"
SPEC = importlib.util.spec_from_file_location("readme_governance", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load bilingual README validator")
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


def section(section_id: str, content: str) -> str:
    return (
        f"<!-- readme-contract:section:{section_id} -->\n"
        f"{content.strip()}\n"
        f"<!-- /readme-contract:section:{section_id} -->"
    )


def valid_readme(*, chinese: bool = False) -> str:
    if chinese:
        title = "# 示例项目"
        language = "[English](./README.md) | 简体中文"
        value = "用可审计的离线检查维护可信的中英双语项目说明。"
        why = "## 为什么选择这个仓库\n\n它把结构检查与语义审核明确分开。"
        quick = "## 快速开始\n\n运行本地校验器。"
        comparison = (
            "## 对比与取舍\n\n评估日期：2026-09-08。"
            "证据：[对比依据](./docs/evidence.md)。\n\n"
            "| 方案 | 优势 | 劣势 |\n|---|---|---|\n"
            "| 本项目 | 离线确定性检查 | 仍需语义审核 |"
        )
        limitations = (
            "## 当前限制\n\n| 限制 | 影响 |\n|---|---|\n| 不检查外链 | 需另行复核 |"
        )
        mitigations = (
            "## 弥补措施\n\n| 限制 | 措施 | 状态 |\n|---|---|---|\n"
            "| 不检查外链 | 在审核中人工复核 | 已记录 |"
        )
        compatibility = "## 兼容性\n\n仅声明已验证的 Python 运行方式。"
        evidence = "## 证据\n\n- [本地证据](./docs/evidence.md)"
        roadmap = "## 路线图\n\n已交付校验；其他能力保持计划状态。"
        security = "## 安全\n\n校验器不联网且不修改目标仓库。"
        license_text = "## 许可证\n\n参见 [LICENSE](./LICENSE)。"
    else:
        title = "# Example Project"
        language = "English | [简体中文](./README.zh-CN.md)"
        value = "Maintain trustworthy bilingual project guidance with auditable offline checks."
        why = "## Why this repository\n\nIt separates structural checks from semantic review."
        quick = "## Quick start\n\nRun the local validator."
        comparison = (
            "## Comparison and trade-offs\n\nAssessment date: 2026-09-08. "
            "Evidence: [comparison basis](./docs/evidence.md).\n\n"
            "| Approach | Advantage | Disadvantage |\n|---|---|---|\n"
            "| This project | Deterministic offline checks | Semantic review remains manual |"
        )
        limitations = (
            "## Current limitations\n\n| Limitation | Impact |\n|---|---|\n"
            "| External links are not fetched | Review them separately |"
        )
        mitigations = (
            "## Mitigations\n\n| Limitation | Mitigation | Status |\n|---|---|---|\n"
            "| External links are not fetched | Review them in the PR | Recorded |"
        )
        compatibility = "## Compatibility\n\nClaim only verified Python execution."
        evidence = "## Evidence\n\n- [Local evidence](./docs/evidence.md)"
        roadmap = "## Roadmap\n\nValidation is delivered; other capabilities remain planned."
        security = "## Security\n\nThe validator is offline and does not mutate the target."
        license_text = "## License\n\nSee [LICENSE](./LICENSE)."
    blocks = [
        section("language-switch", language),
        section("value-proposition", value),
        section("why-this-repo", why),
        section("quick-start", quick),
        section("comparison-and-tradeoffs", comparison),
        section("current-limitations", limitations),
        section("mitigations", mitigations),
        section("compatibility", compatibility),
        section("evidence", evidence),
        section("roadmap", roadmap),
        section("security", security),
        section("license", license_text),
    ]
    return title + "\n\n" + "\n\n".join(blocks) + "\n"


class BilingualReadmeSkillTests(unittest.TestCase):
    def setUp(self) -> None:
        base = (ROOT / "tests" / ".readme-skill-work").resolve()
        self.work_root = (base / self._testMethodName).resolve()
        self.work_root.relative_to(base)
        shutil.rmtree(self.work_root, ignore_errors=True)
        self.root = self.work_root / "sandbox-repository"
        self.root.mkdir(parents=True)

    def tearDown(self) -> None:
        base = (ROOT / "tests" / ".readme-skill-work").resolve()
        self.work_root.resolve().relative_to(base)
        shutil.rmtree(self.work_root, ignore_errors=True)

    def write_valid_pair(self) -> None:
        (self.root / "docs").mkdir(exist_ok=True)
        (self.root / "docs" / "evidence.md").write_text(
            "# Evidence\n", encoding="utf-8"
        )
        (self.root / "LICENSE").write_text("Apache-2.0\n", encoding="utf-8")
        (self.root / "README.md").write_text(valid_readme(), encoding="utf-8")
        (self.root / "README.zh-CN.md").write_text(
            valid_readme(chinese=True), encoding="utf-8"
        )

    def test_skill_metadata_and_runtime_surface_are_self_contained(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        metadata = (SKILL_ROOT / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )
        source = SCRIPT_PATH.read_text(encoding="utf-8")

        self.assertTrue(skill.startswith("---\nname: bilingual-readme-governance\n"))
        self.assertNotIn("TODO", skill)
        self.assertIn("$bilingual-readme-governance", metadata)
        self.assertNotIn("dependencies:", metadata)
        self.assertNotIn("subprocess", source)
        self.assertNotIn("urllib.request", source)
        self.assertNotIn("requests", source)
        self.assertNotIn(".write_text(", source)
        self.assertNotIn(".write_bytes(", source)

    def test_current_repository_is_an_exact_contract_canary(self) -> None:
        result = validator.validate_repository(ROOT)

        self.assertTrue(result["ok"], result["errors"])
        self.assertEqual(result["result"], "PASS")
        self.assertTrue(result["semantic_review"]["required"])
        self.assertFalse(result["semantic_review"]["attested"])

    def test_arbitrary_sandbox_repository_passes_without_network_or_mutation(self) -> None:
        self.write_valid_pair()
        before = {
            path.relative_to(self.root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in self.root.rglob("*")
            if path.is_file()
        }

        result = validator.validate_repository(self.root)
        plan = validator.plan_repository(self.root)

        after = {
            path.relative_to(self.root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in self.root.rglob("*")
            if path.is_file()
        }
        self.assertTrue(result["ok"], result["errors"])
        self.assertEqual(before, after)
        self.assertFalse(result["network_used"])
        self.assertFalse(plan["mutation_performed"])
        self.assertEqual(plan["authority_class"], "R")
        self.assertIn("pull-request-merge", plan["forbidden_effects"])

    def test_missing_locale_and_broken_or_escaping_links_fail_closed(self) -> None:
        self.write_valid_pair()
        (self.root / "README.zh-CN.md").unlink()
        missing = validator.validate_repository(self.root)
        self.assertIn("readme_missing", {item["code"] for item in missing["errors"]})

        self.write_valid_pair()
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        readme = readme.replace("./docs/evidence.md", "../outside.md", 1)
        (self.root / "README.md").write_text(readme, encoding="utf-8")
        broken = validator.validate_repository(self.root)
        self.assertIn(
            "local_link_outside_repository",
            {item["code"] for item in broken["errors"]},
        )

    def test_section_and_claim_parity_are_exact(self) -> None:
        self.write_valid_pair()
        en_path = self.root / "README.md"
        en = en_path.read_text(encoding="utf-8")
        en += "\n" + section("project-specific", "Extra English content.") + "\n"
        en = en.replace(
            "It separates structural checks from semantic review.",
            "<!-- readme-contract:claim:claim.example -->\n"
            "It separates structural checks from semantic review.",
        )
        en_path.write_text(en, encoding="utf-8")

        result = validator.validate_repository(self.root)
        codes = {item["code"] for item in result["errors"]}
        self.assertIn("section_parity_mismatch", codes)
        self.assertIn("claim_parity_mismatch", codes)

    def test_link_checks_cover_case_images_references_html_and_unsafe_schemes(self) -> None:
        self.write_valid_pair()
        path = self.root / "README.md"
        text = path.read_text(encoding="utf-8")
        text = text.replace(
            "It separates structural checks from semantic review.",
            "It separates structural checks from semantic review.\n\n"
            "![case mismatch](./Docs/evidence.md)\n"
            "[missing reference][missing]\n"
            "[missing]: ./docs/missing.md\n"
            "<a href=\"javascript:alert(1)\">unsafe</a>",
        )
        path.write_text(text, encoding="utf-8")

        result = validator.validate_repository(self.root)
        codes = [item["code"] for item in result["errors"]]
        self.assertGreaterEqual(codes.count("local_link_missing"), 2)
        self.assertIn("unsafe_link_scheme", codes)

    def test_unquoted_html_and_parenthesized_markdown_links_are_checked(self) -> None:
        self.write_valid_pair()
        path = self.root / "README.md"
        text = path.read_text(encoding="utf-8")
        text = text.replace(
            "It separates structural checks from semantic review.",
            "It separates structural checks from semantic review.\n\n"
            "<a href=../outside.md>outside</a>",
        )
        path.write_text(text, encoding="utf-8")
        outside = validator.validate_repository(self.root)
        self.assertIn(
            "local_link_outside_repository",
            {item["code"] for item in outside["errors"]},
        )

        self.write_valid_pair()
        parenthesized = self.root / "docs" / "API_(legacy).md"
        parenthesized.write_text("# Legacy API\n", encoding="utf-8")
        text = path.read_text(encoding="utf-8")
        text = text.replace(
            "It separates structural checks from semantic review.",
            "It separates structural checks from semantic review.\n\n"
            "[Legacy API](./docs/API_(legacy).md)",
        )
        path.write_text(text, encoding="utf-8")
        valid = validator.validate_repository(self.root)
        self.assertTrue(valid["ok"], valid["errors"])

    def test_nested_markdown_link_labels_cannot_bypass_path_checks(self) -> None:
        cases = (
            "[outer [inner]](../outside.md)",
            "[![Build](./docs/badge.svg)](../outside.md)",
            "[outer [inner]][escape]\n[escape]: ../outside.md",
            "[![Build][badge]][outer]\n"
            "[badge]: ./docs/badge.svg\n[outer]: ../outside.md",
            "[outside]\n[outside]: ../outside.md",
            "![badge]\n[badge]: ../outside.svg",
        )
        for markup in cases:
            with self.subTest(markup=markup):
                self.write_valid_pair()
                (self.root / "docs" / "badge.svg").write_text(
                    "<svg xmlns='http://www.w3.org/2000/svg'/>\n", encoding="utf-8"
                )
                path = self.root / "README.md"
                text = path.read_text(encoding="utf-8")
                text = text.replace(
                    "It separates structural checks from semantic review.",
                    "It separates structural checks from semantic review.\n\n" + markup,
                )
                path.write_text(text, encoding="utf-8")
                escaped = validator.validate_repository(self.root)
                self.assertIn(
                    "local_link_outside_repository",
                    {item["code"] for item in escaped["errors"]},
                )

    def test_complete_readmes_inside_fences_fail_closed(self) -> None:
        self.write_valid_pair()
        for name in ("README.md", "README.zh-CN.md"):
            path = self.root / name
            original = path.read_text(encoding="utf-8")
            path.write_text(f"```markdown\n{original}```\n", encoding="utf-8")

        fenced = validator.validate_repository(self.root)
        self.assertFalse(fenced["ok"])
        self.assertIn(
            "required_sections_missing",
            {item["code"] for item in fenced["errors"]},
        )

    def test_value_and_content_shape_gates_reject_empty_marketing_shell(self) -> None:
        self.write_valid_pair()
        path = self.root / "README.md"
        text = path.read_text(encoding="utf-8")
        text = text.replace(
            "Maintain trustworthy bilingual project guidance with auditable offline checks.",
            "{{ONE_SENTENCE_MAXIMUM_VALUE}}",
        )
        text = text.replace(
            "| Approach | Advantage | Disadvantage |\n|---|---|---|\n"
            "| This project | Deterministic offline checks | Semantic review remains manual |",
            "No comparison evidence is available.",
        )
        path.write_text(text, encoding="utf-8")

        result = validator.validate_repository(self.root)
        codes = {item["code"] for item in result["errors"]}
        self.assertIn("template_placeholder_present", codes)
        self.assertIn("value_not_one_sentence", codes)
        self.assertIn("comparison_table_missing", codes)

    def test_value_gate_rejects_two_sentences_but_allows_versions_and_abbreviation(self) -> None:
        self.write_valid_pair()
        path = self.root / "README.md"
        original = path.read_text(encoding="utf-8")
        value = "Maintain trustworthy bilingual project guidance with auditable offline checks."
        for replacement in (
            "First sentence. Second sentence.",
            "First sentence. second sentence.",
            "First sentence.Second sentence.",
        ):
            with self.subTest(invalid=replacement):
                path.write_text(original.replace(value, replacement), encoding="utf-8")
                invalid = validator.validate_repository(self.root)
                self.assertIn(
                    "value_not_one_sentence",
                    {item["code"] for item in invalid["errors"]},
                )

        for replacement in (
            "Ship v1.0 reliably with e.g. offline validation.",
            "Use e.g. GitHub evidence.",
            "Use U.S. Teams safely.",
            "Validate Node.js documentation offline.",
        ):
            with self.subTest(valid=replacement):
                path.write_text(original.replace(value, replacement), encoding="utf-8")
                valid = validator.validate_repository(self.root)
                self.assertTrue(valid["ok"], valid["errors"])

    def test_empty_table_and_impossible_calendar_date_fail(self) -> None:
        self.write_valid_pair()
        path = self.root / "README.md"
        text = path.read_text(encoding="utf-8")
        text = text.replace("2026-09-08", "2026-99-99")
        text = text.replace(
            "| External links are not fetched | Review them separately |",
            "| | |",
        )
        path.write_text(text, encoding="utf-8")

        result = validator.validate_repository(self.root)
        codes = {item["code"] for item in result["errors"]}
        self.assertIn("comparison_date_missing", codes)
        self.assertIn("current-limitations_table_missing", codes)

        self.write_valid_pair()
        text = path.read_text(encoding="utf-8")
        text = text.replace("2026-09-08", "<!-- 2026-09-08 -->")
        text = text.replace(
            "| External links are not fetched | Review them separately |",
            "```markdown\n| Hidden | Row |\n|---|---|\n| Value | Value |\n```",
        )
        path.write_text(text, encoding="utf-8")
        hidden = validator.validate_repository(self.root)
        hidden_codes = {item["code"] for item in hidden["errors"]}
        self.assertIn("comparison_date_missing", hidden_codes)
        self.assertIn("current-limitations_table_missing", hidden_codes)

        for empty_row in (
            "| &nbsp; | &#32; |",
            "| [ ](#empty) | |",
        ):
            with self.subTest(empty_row=empty_row):
                self.write_valid_pair()
                text = path.read_text(encoding="utf-8")
                text = text.replace(
                    "| External links are not fetched | Review them separately |",
                    empty_row,
                )
                path.write_text(text, encoding="utf-8")
                empty = validator.validate_repository(self.root)
                self.assertIn(
                    "current-limitations_table_missing",
                    {item["code"] for item in empty["errors"]},
                )

        self.write_valid_pair()
        text = path.read_text(encoding="utf-8")
        text = text.replace(
            "Assessment date: 2026-09-08.",
            "Evidence: [dated report](./docs/report-2026-09-08.md).",
        )
        path.write_text(text, encoding="utf-8")
        link_path_date = validator.validate_repository(self.root)
        self.assertIn(
            "comparison_date_missing",
            {item["code"] for item in link_path_date["errors"]},
        )

    def test_language_switch_must_be_visible_inside_early_section(self) -> None:
        self.write_valid_pair()
        path = self.root / "README.md"
        text = path.read_text(encoding="utf-8")
        visible = "English | [简体中文](./README.zh-CN.md)"
        text = text.replace(visible, f"```markdown\n{visible}\n```")
        text += "\n" + visible + "\n"
        path.write_text(text, encoding="utf-8")
        hidden = validator.validate_repository(self.root)
        self.assertIn(
            "reciprocal_language_link_missing",
            {item["code"] for item in hidden["errors"]},
        )

        self.write_valid_pair()
        text = path.read_text(encoding="utf-8")
        unequal_fence = f"````markdown\n```\n{visible}\n````"
        text = text.replace(visible, unequal_fence)
        path.write_text(text, encoding="utf-8")
        fenced = validator.validate_repository(self.root)
        self.assertIn(
            "reciprocal_language_link_missing",
            {item["code"] for item in fenced["errors"]},
        )

        self.write_valid_pair()
        text = path.read_text(encoding="utf-8")
        switch = section("language-switch", visible)
        text = text.replace(switch + "\n\n", "") + "\n" + switch + "\n"
        path.write_text(text, encoding="utf-8")
        late = validator.validate_repository(self.root)
        self.assertIn(
            "language_switch_position",
            {item["code"] for item in late["errors"]},
        )

    def test_anchor_is_not_evidence_and_markdown_autolink_is_inventoried(self) -> None:
        self.write_valid_pair()
        path = self.root / "README.md"
        text = path.read_text(encoding="utf-8")
        text = text.replace("(./docs/evidence.md)", "(#claim)")
        path.write_text(text, encoding="utf-8")
        anchor_only = validator.validate_repository(self.root)
        codes = {item["code"] for item in anchor_only["errors"]}
        self.assertIn("comparison_evidence_missing", codes)
        self.assertIn("evidence_link_missing", codes)

        self.write_valid_pair()
        text = path.read_text(encoding="utf-8")
        text = text.replace(
            "- [Local evidence](./docs/evidence.md)",
            "![Evidence image](./docs/evidence.md)",
        )
        path.write_text(text, encoding="utf-8")
        image_only = validator.validate_repository(self.root)
        self.assertIn(
            "evidence_link_missing",
            {item["code"] for item in image_only["errors"]},
        )

        self.write_valid_pair()
        text = path.read_text(encoding="utf-8")
        text = text.replace(
            "It separates structural checks from semantic review.",
            "It separates structural checks from semantic review. <https://example.com>",
        )
        path.write_text(text, encoding="utf-8")
        autolink = validator.validate_repository(self.root)
        warning = next(
            item for item in autolink["warnings"] if item["code"] == "external_links_unchecked"
        )
        self.assertIn("1 external", warning["message"])

    def test_oversized_readme_is_rejected_before_full_read(self) -> None:
        self.write_valid_pair()
        (self.root / "README.md").write_bytes(b"x" * (validator.MAX_README_BYTES + 1))

        result = validator.validate_repository(self.root)

        self.assertIn("readme_too_large", {item["code"] for item in result["errors"]})

    def test_canonical_readme_symlink_is_rejected(self) -> None:
        self.write_valid_pair()
        outside = self.work_root / "outside.md"
        outside.write_text(valid_readme(), encoding="utf-8")
        path = self.root / "README.md"
        path.unlink()
        try:
            path.symlink_to(outside)
        except OSError as exc:
            self.skipTest(f"symlink creation is unavailable: {exc}")

        result = validator.validate_repository(self.root)

        self.assertIn(
            "readme_symlink_forbidden",
            {item["code"] for item in result["errors"]},
        )

    def test_templates_are_drafting_aids_not_false_positive_compliance(self) -> None:
        (self.root / "LICENSE").write_text("Apache-2.0\n", encoding="utf-8")
        shutil.copyfile(SKILL_ROOT / "assets" / "README.md.template", self.root / "README.md")
        shutil.copyfile(
            SKILL_ROOT / "assets" / "README.zh-CN.md.template",
            self.root / "README.zh-CN.md",
        )

        result = validator.validate_repository(self.root)

        self.assertFalse(result["ok"])
        self.assertIn(
            "template_placeholder_present",
            {item["code"] for item in result["errors"]},
        )

    def test_utf8_bom_pair_is_supported(self) -> None:
        self.write_valid_pair()
        for name in ("README.md", "README.zh-CN.md"):
            path = self.root / name
            path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8-sig")

        result = validator.validate_repository(self.root)

        self.assertTrue(result["ok"], result["errors"])

    def test_cli_exit_codes_distinguish_validation_failure_and_plan_success(self) -> None:
        validate = subprocess.run(
            [sys.executable, "-I", str(SCRIPT_PATH), "validate", "--root", str(self.root)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        plan = subprocess.run(
            [sys.executable, "-I", str(SCRIPT_PATH), "plan", "--root", str(self.root)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        self.assertEqual(validate.returncode, 1)
        self.assertEqual(plan.returncode, 0)
        self.assertFalse(json.loads(plan.stdout)["mutation_performed"])

    def test_malformed_contract_is_rejected(self) -> None:
        contract = json.loads(validator.DEFAULT_CONTRACT_PATH.read_text(encoding="utf-8"))
        malformed = copy.deepcopy(contract)
        malformed["policies"]["semanticReviewRequired"] = "yes"
        path = self.root / "contract.json"
        path.write_text(json.dumps(malformed), encoding="utf-8")

        with self.assertRaises(validator.ContractError):
            validator.load_contract(path)

        weakened = copy.deepcopy(contract)
        weakened["policies"]["localLinksBlocking"] = False
        path.write_text(json.dumps(weakened), encoding="utf-8")
        with self.assertRaises(validator.ContractError):
            validator.load_contract(path)

    def test_skill_directory_is_portable_to_two_host_layouts(self) -> None:
        self.write_valid_pair()
        for host in ("codex", "claude"):
            installed = self.work_root / host / "skills" / SKILL_ROOT.name
            shutil.copytree(SKILL_ROOT, installed)
            result = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    str(installed / "scripts" / "readme_governance.py"),
                    "validate",
                    "--root",
                    str(self.root),
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["result"], "PASS")


if __name__ == "__main__":
    unittest.main()
