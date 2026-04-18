---
feature: paragraph-rewrite
title: 段落一键重写 — 技术设计
status: beta
updatedAt: 2026-04-11
---

# 段落一键重写 — 技术设计文档

## 架构概述

段落重写功能基于 TipTap Editor Extension 实现，通过 GPT-4o 流式调用完成文本重写。

## 核心组件

### RewriteButton 组件

选中文本后浮动显示的重写按钮，包含完整的 Loading 状态和错误处理：

```tsx
const handleRewrite = async () => {
  setLoading(true);
  try {
    const result = await callGPT(selected);
    replaceText(result);
  } catch (err) {
    showToast('重写失败，请重试');
  } finally {
    setLoading(false);
  }
};
```

### IME Handler Hook

独立封装的输入法处理 Hook，解决中文 IME 输入时光标丢失问题：

```ts
export function useImeHandler(editor: Editor) {
  let composing = false;
  let savedSelection: Selection | null = null;

  editor.on('compositionstart', () => {
    composing = true;
    savedSelection = editor.getSelection();
  });

  editor.on('compositionend', () => {
    composing = false;
    if (savedSelection) editor.setSelection(savedSelection);
  });

  editor.on('keydown', (e) => {
    if (composing) return;
    handleKey(e);
  });
}
```

## 代码审查记录

### CR-001: 修复 Editor 光标丢失 bug（changes-requested）

- 修复方向正确，但建议将 compositionstart/end 处理封装为独立 Hook
- 需要补充单元测试敏感场景
- 涉及文件：`src/editor/plugins/ime-handler.ts`、`src/editor/hooks/use-editor.ts`

### CR-002: 实现段落重写功能 MVP（approved）

- 整体实现清晰，Loading 状态处理完善，错误边界已覆盖
- 代码结构合理，可直接合并
- 涉及文件：`src/components/RewriteButton.tsx`

## 测试覆盖

| 任务 | 测试状态 | 总用例 | 通过 | 失败 | 覆盖率 |
|------|---------|--------|------|------|--------|
| 修复光标丢失 | partial | 6 | 4 | 2 | 72% |
| 段落重写 MVP | passed | 8 | 8 | 0 | 89% |

## 技术决策

- AI 模型：GPT-4o（中文写作质量优先），长文档降级到 GPT-4o-mini
- 编辑器：TipTap（基于 ProseMirror），Extension 生态完善
