---
id: K-005
category: tech-note
title: Supabase RLS 策略最佳实践
tags: [Supabase, RLS, 安全]
createdAt: 2026-03-18
---

## 核心规则

每张表**必须**开启 RLS，哪怕是只读表。

## 关键要点

1. 用 `auth.uid()` 而非 `auth.role()` 进行行级权限控制
2. JOIN 查询中关联表也**必须有对应 RLS 策略**，否则返回空
3. 测试时注意：匿名访问和认证访问的策略要分别验证

## 常见踩坑

```sql
-- ❌ 错误：关联表未设置 RLS，JOIN 后返回空
SELECT * FROM posts JOIN comments ON posts.id = comments.post_id;

-- ✅ 正确：确保 posts 和 comments 都有 RLS 策略
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE comments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own posts" ON posts
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view comments on own posts" ON comments
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM posts WHERE posts.id = comments.post_id AND posts.user_id = auth.uid())
  );
```
