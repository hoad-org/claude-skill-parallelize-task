---
name: Confluence Documentation Links
description: Central index of all Confluence pages related to parallelize-task skill
type: reference
---

# parallelize-task Skill — Confluence Documentation Index

## 🎯 Core Architecture & Design

| Page | Purpose | Link |
|------|---------|------|
| **parallelize-task Superpower Spec** | Complete architecture, decision engine, gap analysis, implementation roadmap | [https://darkmothcreative.atlassian.net/wiki/spaces/hoadplatfo/pages/24772926/claude-skill-paralellize-task](https://darkmothcreative.atlassian.net/wiki/spaces/hoadplatfo/pages/24772926/claude-skill-paralellize-task) |
| **Claude Orientation Guide** | Required reading: repo structure, AWS landing zone, Terraform backend, GitHub OIDC | [https://darkmothcreative.atlassian.net/wiki/spaces/hoadcloudp/pages/15237122](https://darkmothcreative.atlassian.net/wiki/spaces/hoadcloudp/pages/15237122) |
| **CloudCTL Rail** | How Claude uses cloud tools (AWS, GCP, Azure context switching) | [https://darkmothcreative.atlassian.net/wiki/spaces/hoadplatfo/pages/25165826/](https://darkmothcreative.atlassian.net/wiki/spaces/hoadplatfo/pages/25165826/) |

## 🛠️ Related Infrastructure & Governance

| Page | Purpose | Link |
|------|---------|------|
| **HCP Cost Optimization Strategy** | Cost control, CloudFlare DNS, free-tier AWS validation | [../../../Repos/aws-terraform-platform-aws-org/COST_OPTIMIZATION_STRATEGY.md](../../../Repos/aws-terraform-platform-aws-org/COST_OPTIMIZATION_STRATEGY.md) |
| **HCP Platform Key Decisions** | Repo cost validation, account separation, free-tier performance | [../../../Repos/aws-terraform-platform-aws-org/PLATFORM_DECISIONS_SUMMARY.md](../../../Repos/aws-terraform-platform-aws-org/PLATFORM_DECISIONS_SUMMARY.md) |
| **DevArmor Status** | What's protected, enforcement rules, quick commands | [Confluence: devarmor_status.md](https://darkmothcreative.atlassian.net/wiki/spaces/hoadplatfo/pages/TODO) |
| **Cost Control Standards** | AWS $30/mo budget enforcement, resource pricing | [../../../Repos/COST-CONTROL-STANDARDS.md](../../../Repos/COST-CONTROL-STANDARDS.md) |
| **Multi-Repo Terraform Backend** | Centralized state bucket, OIDC for 6 repos | [Confluence: project_multi_repo_backend.md](https://darkmothcreative.atlassian.net/wiki/spaces/hoadplatfo/pages/TODO) |

## 🎓 Skill Development Reference

| Page | Purpose | Link |
|------|---------|------|
| **Skill Development Reference** | Master guide: 3-pillar architecture, 4-level config, >85% coverage | [Memory: skill_development_reference.md](../../.claude/projects/-Users-craighoad-Repos/memory/skill_development_reference.md) |
| **Jira Skill v2.0.0** | Production reference skill (28 commands, 100% test pass, 3-pillar) | [https://github.com/hoad-org/jira-skill](https://github.com/hoad-org/jira-skill) |
| **Confluence Skill v1.2.0** | Enterprise-grade reference (85%+ coverage, 8 templates, Jira integration) | [https://github.com/hoad-org/confluence-skill](https://github.com/hoad-org/confluence-skill) |

## 🔗 Related Repositories

| Repo | Purpose | Link |
|------|---------|------|
| **parallelize-task Skill** | This skill (agent orchestration, token optimization) | [https://github.com/hoad-org/claude-skill-parallelize-task](https://github.com/hoad-org/claude-skill-parallelize-task) |
| **DevArmor** | Infrastructure operations automation (uses parallelize-task) | [https://github.com/hoad-org/devarmor-infra-cloudops](https://github.com/hoad-org/devarmor-infra-cloudops) |
| **AWS Terraform Platform** | Landing zone, account vending, cost governance | [https://github.com/hoad-org/aws-terraform-platform-aws-org](https://github.com/hoad-org/aws-terraform-platform-aws-org) |
| **GCP Terraform Platform** | GCP equivalent (multi-cloud strategy) | [https://github.com/hoad-org/gcp-terraform-platform](https://github.com/hoad-org/gcp-terraform-platform) |

## 📚 How to Use This Index

1. **For implementation**: Start with "parallelize-task Superpower Spec" (architecture + gaps resolved)
2. **For context**: Read "Claude Orientation Guide" (required for HOAD infrastructure)
3. **For cost governance**: Check "Cost Control Standards" (enforcement rules)
4. **For DevArmor integration**: See "DevArmor Status" (how parallelize-task fits in)
5. **For skill patterns**: Reference "Skill Development Reference" + Jira/Confluence skills

## 🔄 Confluence Page Sync

This file is a snapshot. For latest updates, visit:

**Primary spec page:**
```
https://darkmothcreative.atlassian.net/wiki/spaces/hoadplatfo/pages/24772926/claude-skill-paralellize-task
```

**Claude Orientation (required reading):**
```
https://darkmothcreative.atlassian.net/wiki/spaces/hoadcloudp/pages/15237122
```

## ✅ Action Items

- [ ] Validate Claude Code agent pool API exists (GAP 5)
- [ ] Define DevArmor callback interface (GAP 8)
- [ ] Choose persistence layer (GAP 9)
- [ ] Finalize escalation policy (GAP 6)
- [ ] Link this index from main README.md

---

**Last Updated**: 2026-05-17  
**Status**: Ready for implementation (all gaps resolved)
