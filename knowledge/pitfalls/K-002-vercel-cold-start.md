---
id: K-002
category: pitfall
title: Vercel Serverless 冷启动超时
tags: [Vercel, Serverless, OpenAI]
createdAt: 2026-03-28
---

## 问题

OpenAI Stream 接口在冷启动时会超过 Vercel 10s 限制。

## 现象

- 首次请求 AI 续写/重写功能时出现超时错误
- 后续请求正常（热启动状态）

## 解法

迁移到 Edge Runtime，或使用 Vercel Pro 的更长超时配置。

| 方案 | 优点 | 缺点 |
|------|------|------|
| Edge Runtime | 无冷启动 | 功能受限（不支持 Node.js API） |
| Vercel Pro | 超时上限 60s | 成本增加 |

当前选择：迁移到 Edge Runtime，v1.2.1 回滚后已在 v1.2.3 中修复。
