---
id: K-006
category: tech-note
title: TipTap Extension 的正确开发姿势
tags: [TipTap, ProseMirror, Extension]
feature: paragraph-rewrite
createdAt: 2026-02-25
---

## 核心原则

1. **不要直接修改 Node 的 attrs**，要通过 Command 触发
2. **Extension 之间通信用 `Editor.storage`**，不要用全局状态
3. 测试时**必须 mock ProseMirror state**

## 正确示例

```ts
// ✅ 通过 Command 修改 Node attrs
editor.chain()
  .focus()
  .updateAttributes('paragraph', { style: 'formal' })
  .run();

// ❌ 不要直接操作 DOM 或 attrs
// node.attrs.style = 'formal'; // 这样不会触发重渲染
```

## Extension 间通信

```ts
// 在 Extension A 中写入
this.storage.sharedData = { key: 'value' };

// 在 Extension B 中读取
const data = editor.storage.extensionA?.sharedData;
```

## 测试要点

- 必须创建完整的 Editor 实例用于测试
- Mock ProseMirror 的 EditorState 和 Transaction
- 使用 `jest-prosemirror` 辅助库简化测试编写
