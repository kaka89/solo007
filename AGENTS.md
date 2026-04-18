# AGENTS.md — solo007 知识管理规约

> Solo 模式 — 所有 Agent 在生成文档前 **MUST** 遵循此规约。

## 目录结构

```
├── product/           活文档（产品全貌：PRD / SDD / 功能索引）
├── iterations/        增量文档（假设 / 任务 / 发布 / 归档）
├── knowledge/         个人知识库（踩坑 / 洞察 / 技术笔记）
├── code/              源代码（前端 / 后端 / 共享包，按需创建子工程）
├── .xingjing/         星静元数据
├── .opencode/         Agent + Skill
├── focus.yml          今日焦点
├── metrics.yml        商业指标
├── feature-flags.yml  功能开关
├── adrs.yml           架构决策
└── AGENTS.md
```

## 角色-目录所有权

| Agent | 主要产出 | 输出路径 |
|-------|---------|---------|
| product-brain | PRD（功能需求）| `product/features/{feat}/PRD.md` |
| eng-brain | SDD（技术方案）、Task、源代码 | `product/features/{feat}/SDD.md`、`iterations/tasks/`、`code/` |
| growth-brain | 用户洞察、增长策略 | `knowledge/insights/` |
| ops-brain | 发布记录 | `iterations/releases/` |

## 回写规则

- 任务完成 → changelog 回写到 `product/features/{feat}/SDD.md`
- 假设验证 → 结论回写到 `product/features/{feat}/PRD.md`
- 增量文档（iterations/）只增不改，保持原样

## 命名规范

| 类型 | 格式 | 示例 |
|------|------|------|
| 功能目录 | `{kebab-name}/` | `product/features/paragraph-rewrite/` |
| 假设 | `H-{NNN}-{name}.md` | `H-001-rewrite.md` |
| 任务 | `T-{NNN}-{name}.yml` | `T-002-rewrite-mvp.yml` |
| 发布 | `v{x.y.z}.yml` | `v1.3.0.yml` |
| 知识 | `K-{NNN}-{name}.md` | `K-001-prosemirror-ime.md` |

## 台账规则

生成文档后 **MUST** 更新同目录 `_index.yml`。
所有 Agent 生成文档前 **MUST** 调用 `knowledge-conventions` skill。
