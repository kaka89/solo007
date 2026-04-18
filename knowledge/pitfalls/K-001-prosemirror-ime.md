---
id: K-001
category: pitfall
title: ProseMirror IME 输入光标丢失
tags: [ProseMirror, IME, 中文输入]
feature: paragraph-rewrite
createdAt: 2026-04-08
---

## 问题

在中文 IME 输入过程中，composition 事件会导致 selection 状态错误。

## 现象

- 用户输入中文时，光标位置会突然跳到错误位置
- compositionstart/end 事件触发期间 selection state 被 handleKeyDown 覆盖

## 解法

在 compositionstart/end 事件中缓存 selection state，避免 handleKeyDown 覆盖：

```ts
editor.on('compositionstart', () => {
  composing = true;
  savedSelection = editor.getSelection();
});

editor.on('compositionend', () => {
  composing = false;
  if (savedSelection) editor.setSelection(savedSelection);
});
```

> **AI 提示**：当前正在修复的 bug (T-001) 与此坑直接相关！
