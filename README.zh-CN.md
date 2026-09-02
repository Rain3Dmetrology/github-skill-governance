# GitHub Skill 治理

<!-- readme-contract:section:language-switch -->
[English](./README.md) | 简体中文
<!-- /readme-contract:section:language-switch -->

<!-- readme-contract:section:value-proposition -->
在智能体 Skill 获得 GitHub 写入或发布权前，先建立可审计的双语治理基线。
<!-- /readme-contract:section:value-proposition -->

> 当前状态：**P1 平台强制已生效**。GitHub 回读与被阻断的负向 PR 已证明
> required check、main 保护和全标签冻结。受保护的 `c-authorization`
> Environment 已启用；本 PR-B1 候选加入唯一标准精确 PR Broker 工作流，
> 在被单独合并到 `main` 前不会生效，发布权仍禁用。

<!-- readme-contract:section:why-this-repo -->
## 为什么选择这个仓库

单体提示词会把指令、GitHub 写操作、版本决策和发布命令混在一起。本仓库把
人类承诺、确定性检查和智能体辅助分开，使后续每项自动化都能被测试、审计
和撤销。

<!-- readme-contract:claim:claim.independent-rewrite-policy -->
P0 基线是采用独立重写策略的新 Apache-2.0 仓库。来源日志记录了输入与排除
范围；这不是法律意义上的正式 clean-room 认证。

<!-- readme-contract:claim:claim.release-authority-frozen -->
版本与发布权威冻结为未来唯一的 `release-please`；P4 结束前明确禁用。

<!-- readme-contract:claim:claim.readme-contract-frozen -->
英文和简体中文 README 共享稳定的 section ID 与 claim ID，而不是强制逐句直译。

<!-- readme-contract:claim:claim.permission-boundaries-frozen -->
仓库操作分为只读 R、可逆写 W 和外部承诺 C；智能体默认没有 C 权限。

<!-- readme-contract:claim:claim.p1-platform-enforcement -->
P1 平台控制已生效：`main` 只能通过带严格治理检查的 PR 更新，所有标签名在
P5 前均被冻结。该状态不向任何 Skill 授予常驻变更权或发布权。

<!-- readme-contract:claim:claim.c-authorization-broker-bootstrap -->
仓库现已包含单路由 C 授权契约、经过本地测试的执行器，以及精确 squash
merge 的标准工作流候选。受保护 Environment 已启用，但工作流合并和远端
canary 仍是彼此独立的后续 Gate。
<!-- /readme-contract:section:why-this-repo -->

<!-- readme-contract:section:quick-start -->
## 快速开始

P1 是已生效的治理强制，不是安装器或发布器：

```text
1. 运行：python3 -m unittest discover -s tests -p 'test_*.py'
2. 运行：python3 scripts/validate_governance.py --root .
3. 查看：python3 scripts/github_preflight.py --help
4. 查看：python3 scripts/c_authorization_broker.py --help
5. 修改已生效控制前审核 docs/P1_C_BROKER_ACCEPTANCE.md
6. PR-B1 合并后按 docs/runbooks/C_AUTHORIZATION_BROKER.md 操作
```

不要从该 revision 安装 AI 审查器或启用发布自动化。
<!-- /readme-contract:section:quick-start -->

<!-- readme-contract:section:comparison-and-tradeoffs -->
## 对比与取舍

<!-- readme-contract:claim:claim.p0-alternatives-comparison -->
评估日期：**2026-08-30**。这是范围与架构对比，不是性能基准测试。

| 方案 | 适合选择的条件 | 不该选择的条件 | 当前取舍 | 证据 |
|---|---|---|---|---|
| 本治理仓库 | 需要在自动化前冻结许可证、发布权威、双语 README 和权限契约 | 今天就需要已验证的多宿主包或可用发布路径 | P1 控制和受保护 Environment 已生效；标准 Broker 工作流仍是 PR-B1 候选，远端 canary、多宿主分发与发布尚未交付 | [当前策略与验收](./docs/comparisons/P0_ALTERNATIVES.md#this-p0-baseline) |
| 人工监督的单体发布提示词 | 可信维护者需要人工监督的检查清单，并接受其仓库许可证 | 需要 OSI 开源核心、确定性 Gate 或已验证多宿主使用 | 配置更少；策略与写命令仍处于同一指令面 | [已审查旧仓快照](./docs/comparisons/P0_ALTERNATIVES.md#legacy-release-prompt) |
| 每个智能体的非托管副本 | 内容临时且不需要共享期望状态 | 必须跨宿主复现或审计同一 revision | 无中央配置；每个操作者自行跟踪版本并协调收敛 | [对比范围定义](./docs/comparisons/P0_ALTERNATIVES.md#unmanaged-per-agent-copies) |

旧 `github-release-management` 仓库只作为需求和失败场景参考，不作为依赖或
生产发布执行器。
<!-- /readme-contract:section:comparison-and-tradeoffs -->

<!-- readme-contract:section:current-limitations -->
## 当前限制

| 限制 | 对用户的影响 |
|---|---|
| C Broker 工作流仍是 PR-B1 候选 | 单独合并前不能调度 Broker 变更；远端 canary 通过前不声称生产可用 |
| 发布自动化被禁用 | 尚无受支持的 tag 或 GitHub Release 路径 |
| 没有宿主 adapter 与 smoke test | 当前不声称已验证任何智能体平台 |
| 只有一名维护者负责审查 | CODEOWNERS 可以路由审查，但不能提供独立批准 |
<!-- /readme-contract:section:current-limitations -->

<!-- readme-contract:section:mitigations -->
## 弥补措施

| 限制 | 立即措施 | 永久方案 | 状态 |
|---|---|---|---|
| Broker 尚未远端验证 | C 动作继续由人类紧邻授权并拒绝可复用回执字符串 | 标准单路由工作流、负向/重放 canary、精确效果回读与 PR-B2 证据 | PR-B1 候选；Issue #1 仍开放 |
| 没有发布路径 | 不创建 tag 或 Release | P5 Draft-first 发布 Saga | 策略禁用 |
| 没有已验证宿主 | 不声明平台兼容性 | P6 exact-SHA 双宿主 canary | 未开始 |
| 没有独立审查者 | 如实记录维护者自审，审批数保持为 0 | 强制独立批准前先增加第二名可信人类 | 开放限制 |

后续功能在实施前必须先建立 GitHub Issue；在此之前不会包装成已交付能力。
<!-- /readme-contract:section:mitigations -->

<!-- readme-contract:section:compatibility -->
## 兼容性

P1 不验证任何运行时或智能体宿主。未来包格式采用开放 Agent Skills 目录约定，
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
| `claim.p1-platform-enforcement` | `P1_ACCEPTANCE.md`、ADR-0008、远端 active 回执 |
| `claim.c-authorization-broker-bootstrap` | Broker schema、执行器、标准工作流、runbook、`P1_C_BROKER_ACCEPTANCE.md`、ADR-0009、威胁模型 |
| `claim.p0-alternatives-comparison` | `P0_ALTERNATIVES.md`，评估于 2026-08-30 |

机器可读声明映射位于 [`docs/claims.yaml`](./docs/claims.yaml)。
<!-- /readme-contract:section:evidence -->

<!-- readme-contract:section:roadmap -->
## 路线图

| 阶段 | 进入条件 | 进入下一阶段前必须得到的结果 |
|---|---|---|
| P0 | 已授权仓库 bootstrap | 许可证、版本权威、README 契约和 R/W/C 权限冻结 |
| P1 | P0 验收 | GitHub 平台强制与最小权限检查；已验收 |
| P1-C | P1 已强制 | 激活并远端验证精确 PR C Broker；Issue #1 |
| P2a | P1-C 已验证 | 确定性跨仓库双语 README Skill，默认 dry-run、仅 PR |
| P2b+ | P2a 已有证据 | 发布状态与分发校验器，再进入 Core Skills 与发布 Saga |

P0 与 P1 平台强制已验收。P1-C、P2 及以后仍是决策 Gate，不是交付声明。
<!-- /readme-contract:section:roadmap -->

<!-- readme-contract:section:security -->
## 安全

禁止提交凭据、客户私密名称、内部路径或生产 Token。参见
[`SECURITY.md`](./SECURITY.md)。P1 不向任何 Skill 委派常驻的 merge、tag、
Release、Ruleset、Secret 或生产部署权限。经人类授权的任务执行者只能执行
ADR-0005 明确限定的 C 类动作。标准 Broker 候选只有在 Environment 批准后
才获得 job-scoped 写 Token，且只暴露精确 squash-merge 路由；它不会向任何
Skill 授予常驻 C 权限。
<!-- /readme-contract:section:security -->

<!-- readme-contract:section:license -->
## 许可证

Apache License 2.0。参见 [`LICENSE`](./LICENSE) 和
[`THIRD_PARTY_NOTICES.md`](./THIRD_PARTY_NOTICES.md)。
<!-- /readme-contract:section:license -->
