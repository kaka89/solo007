---
name: knowledge-conventions
description: 知识管理规约 — 在生成文档前调用此 Skill 获取正确的放置路径和命名格式
---

# 知识管理规约（Solo 模式）

> **调用时机**：在生成任何文档前 MUST 调用本 Skill。

## 目录结构

| 区域 | 路径 | 职责 |
|------|------|------|
| 活文档 | `product/` | 产品当前全貌（PRD / SDD / 功能索引 / Roadmap） |
| 增量文档 | `iterations/` | 执行过程（假设 / 任务 / 发布 / 归档） |
| 知识库 | `knowledge/` | 个人知识沉淀（踩坑 / 洞察 / 技术笔记） |
| 源代码 | `code/` | 产品源代码容器，按需包含 web/、server/、shared/ 等子工程（eng-brain 操作区域） |
| 运行时 | 根目录 `.yml` | focus / metrics / feature-flags / adrs |

## 活文档（原地更新）

| 类型 | 路径 | 说明 |
|------|------|------|
| PRD | `product/features/{feat}/PRD.md` | 功能需求（活文档，持续更新） |
| SDD | `product/features/{feat}/SDD.md` | 技术方案（活文档，持续更新） |
| 功能索引 | `product/features/_index.yml` | 功能全景清单 |
| 概述 | `product/overview.md` | 产品定位 |
| 路线图 | `product/roadmap.md` | 未来规划 |

## 增量文档（只增不改）

| 类型 | 路径 | 命名 | 台账 |
|------|------|------|------|
| 假设 | `iterations/hypotheses/` | H-{NNN}-{name}.md | _index.yml |
| 任务 | `iterations/tasks/` | T-{NNN}-{name}.yml | _index.yml |
| 发布 | `iterations/releases/` | v{x.y.z}.yml | — |

## 回写规则

- 任务完成 → `changelog` 回写到 `product/features/{feat}/SDD.md`
- 假设验证 → 结论回写到 `product/features/{feat}/PRD.md`
- 增量文档本身不受影响

## 归档

版本发布后，将已完成的假设和任务移入 `iterations/archive/{version}/`。
_index.yml 中归档条目标记 `archived: true`。
