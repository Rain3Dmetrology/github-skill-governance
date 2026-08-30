# GitHub Skill 治理

<!-- readme-contract:section:language-switch -->
[English](./README.md) | 简体中文
<!-- /readme-contract:section:language-switch -->

<!-- readme-contract:section:value-proposition -->
在智能体 Skill 获得 GitHub 写入或发布权前，先建立可审计的双语治理基线。
<!-- /readme-contract:section:value-proposition -->

> 当前状态：**P1 强制实施中**。本 revision 加入确定性检查、CODEOWNERS
> 和可审查的 Ruleset 期望状态。只有 P1 验收中的 GitHub 回执全部完成后，
> 才会声明平台强制已生效。

<!-- readme-contract:section:why-this-repo -->
## 为什么选择这个仓库

单体提示词会把指令、GitHub 写操作、版本决策和发布命令混在一起。本仓库把
人类承诺、确定性检查和智能体辅助分开，使后续每项自动化都能被测试、审计
和撤销。

<!-- readme-contract:claim:claim.independent-rewrite-policy -->
P0 基线是采用独立重写策略的新 Apache-2.0 仓库。来源日志记录了输入与排除
范围；这不是法律意义上的正式 clean-room 认证。

<!-- readme-contract:claim:claim.release-authority-frozen -->
版本与发布权威冻结为未来唯一的 `release-please`；P0 阶段明确禁用。

<!-- readme-contract:claim:claim.readme-contract-frozen -->
英文和简体中文 README 共享稳定的 section ID 与 claim ID，而不是强制逐句直译。

<!-- readme-contract:claim:claim.permission-boundaries-frozen -->
仓库操作分为只读 R、可逆写 W 和外部承诺 C；智能体默认没有 C 权限。
<!-- /readme-contract:section:why-this-repo -->

<!-- readme-contract:section:quick-start -->
## 快速开始

P1 是治理强制，不是安装器或发布器：

```text
1. 运行：python3 -m unittest discover -s tests -p 'test_*.py'
2. 运行：python3 scripts/validate_governance.py --root .
3. 查看：python3 scripts/github_preflight.py --help
4. 声明平台强制生效前审核 docs/P1_ACCEPTANCE.md
```

不要从该 revision 安装 AI 审查器或启用发布自动化。
<!-- /readme-contract:section:quick-start -->

<!-- readme-contract:section:comparison-and-tradeoffs -->
## 对比与取舍

<!-- readme-contract:claim:claim.p0-alternatives-comparison -->
评估日期：**2026-08-29**。这是范围与架构对比，不是性能基准测试。

| 方案 | 适合选择的条件 | 不该选择的条件 | 当前取舍 | 证据 |
|---|---|---|---|---|
| 本治理仓库 | 需要在自动化前冻结许可证、发布权威、双语 README 和权限契约 | 今天就需要已验证的多宿主包或可用发布路径 | P0 已验收；P1 检查与期望控制可审核，远端强制仍需回执 | [当前策略与验收](./docs/comparisons/P0_ALTERNATIVES.md#this-p0-baseline) |
| 人工监督的单体发布提示词 | 可信维护者需要人工监督的检查清单，并接受其仓库许可证 | 需要 OSI 开源核心、确定性 Gate 或已验证多宿主使用 | 配置更少；策略与写命令仍处于同一指令面 | [已审查旧仓快照](./docs/comparisons/P0_ALTERNATIVES.md#legacy-release-prompt) |
| 每个智能体的非托管副本 | 内容临时且不需要共享期望状态 | 必须跨宿主复现或审计同一 revision | 无中央配置；每个操作者自行跟踪版本并协调收敛 | [对比范围定义](./docs/comparisons/P0_ALTERNATIVES.md#unmanaged-per-agent-copies) |

旧 `github-release-management` 仓库只作为需求和失败场景参考，不作为依赖或
生产发布执行器。
<!-- /readme-contract:section:comparison-and-tradeoffs -->

<!-- readme-contract:section:current-limitations -->
## 当前限制

| 限制 | 对用户的影响 |
|---|---|
| P1 平台激活尚无完整回执 | 新检查尚未被声明为 required merge Gate |
| 发布自动化被禁用 | 尚无受支持的 tag 或 GitHub Release 路径 |
| 没有宿主 adapter 与 smoke test | 当前不声称已验证任何智能体平台 |
| 只有一名维护者负责审查 | CODEOWNERS 可以路由审查，但不能提供独立批准 |
<!-- /readme-contract:section:current-limitations -->

<!-- readme-contract:section:mitigations -->
## 弥补措施

| 限制 | 立即措施 | 永久方案 | 状态 |
|---|---|---|---|
| required Gate 尚未验收 | 在本地和 P1 PR 上运行确定性测试 | 绑定真实 check App ID 并激活 main Ruleset | 进行中：Issue #1、#2 |
| 没有发布路径 | 不创建 tag 或 Release | P5 Draft-first 发布 Saga | 策略禁用 |
| 没有已验证宿主 | 不声明平台兼容性 | P6 exact-SHA 双宿主 canary | 未开始 |
| 没有独立审查者 | 如实记录维护者自审，审批数保持为 0 | 强制独立批准前先增加第二名可信人类 | 开放限制 |

后续功能在实施前必须先建立 GitHub Issue；在此之前不会包装成已交付能力。
<!-- /readme-contract:section:mitigations -->

<!-- readme-contract:section:compatibility -->
## 兼容性

P0 不验证任何运行时或智能体宿主。未来包格式采用开放 Agent Skills 目录约定，
但兼容性声明必须有固定 revision 的安装结果和 smoke-test 回执。
<!-- /readme-contract:section:compatibility -->

<!-- readme-contract:section:evidence -->
## 证据

| Claim ID | 证据 |
|---|---|
| `claim.independent-rewrite-policy` | `LICENSE`、`THIRD_PARTY_NOTICES.md`、`P0_SOURCE_LOG.md`、ADR-0001 |
| `claim.release-authority-frozen` | `repo-policy.yaml`、ADR-0002、ADR-0005 |
| `claim.readme-contract-frozen` | `readme-contract.json`、ADR-0003、两份 README |
| `claim.permission-boundaries-frozen` | `repo-policy.yaml`、`owners.yaml`、ADR-0004、ADR-0005、ADR-0006 |
| `claim.p0-alternatives-comparison` | `P0_ALTERNATIVES.md`，评估于 2026-08-29 |

机器可读声明映射位于 [`docs/claims.yaml`](./docs/claims.yaml)。
<!-- /readme-contract:section:evidence -->

<!-- readme-contract:section:roadmap -->
## 路线图

| 阶段 | 进入条件 | 进入下一阶段前必须得到的结果 |
|---|---|---|
| P0 | 已授权仓库 bootstrap | 许可证、版本权威、README 契约和 R/W/C 权限冻结 |
| P1 | P0 验收 | GitHub 平台强制与最小权限检查；当前阶段 |
| P2 | P1 已强制 | 确定性 README、发布状态和分发校验器 |
| P3+ | 上一阶段证据存在 | Core Skills、Draft 发布 Saga、双宿主 canary |

P0 已验收，P1 是当前实施阶段。P2 及以后仍是决策 Gate，不是交付声明。
<!-- /readme-contract:section:roadmap -->

<!-- readme-contract:section:security -->
## 安全

禁止提交凭据、客户私密名称、内部路径或生产 Token。参见
[`SECURITY.md`](./SECURITY.md)。P1 不向任何 Skill 委派常驻的 merge、tag、
Release、Ruleset、Secret 或生产部署权限。经人类授权的任务执行者只能执行
ADR-0005 明确限定的 C 类动作。
<!-- /readme-contract:section:security -->

<!-- readme-contract:section:license -->
## 许可证

Apache License 2.0。参见 [`LICENSE`](./LICENSE) 和
[`THIRD_PARTY_NOTICES.md`](./THIRD_PARTY_NOTICES.md)。
<!-- /readme-contract:section:license -->
