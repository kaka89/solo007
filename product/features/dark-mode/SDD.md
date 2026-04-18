---
feature: dark-mode
title: 主题模式技术方案
status: design
prd: PRD.md
since: v1.2.2
updatedAt: 2026-04-18
---

# 主题模式 — 技术方案

## 架构设计

### 1. 主题系统架构
```
Theme System
├── ThemeProvider (Context)
│   ├── ThemeState (浅色/深色/彩色)
│   ├── ColorTheme (彩色主题配置)
│   └── ThemeConfig (全局配置)
├── ThemeEngine (主题引擎)
│   ├── CSS变量生成器
│   ├── 颜色计算器
│   └── 过渡动画控制器
└── ThemeStorage (持久化)
    ├── localStorage
    ├── 用户偏好API
    └── 同步服务
```

### 2. 数据模型

```typescript
// 主题类型
type ThemeMode = 'light' | 'dark' | 'color';

// 彩色主题配置
interface ColorTheme {
  id: string;
  name: string;
  colors: {
    primary: string;      // 主色
    secondary: string;    // 辅色
    background: string;   // 背景色
    surface: string;      // 表面色
    text: string;         // 文字色
    textSecondary: string;// 次要文字色
    accent: string;       // 强调色
    error: string;        // 错误色
    success: string;      // 成功色
    warning: string;      // 警告色
  };
  isPreset: boolean;      // 是否为预设主题
}

// 主题配置
interface ThemeConfig {
  mode: ThemeMode;
  colorThemeId?: string;  // 彩色主题ID
  followSystem: boolean;  // 是否跟随系统
}
```

## 技术实现

### 1. CSS 变量方案

```css
/* 基础变量 */
:root {
  /* 浅色模式默认值 */
  --color-primary: #007AFF;
  --color-background: #FFFFFF;
  --color-text: #000000;
  /* ... 其他变量 */
}

/* 深色模式 */
[data-theme="dark"] {
  --color-primary: #0A84FF;
  --color-background: #000000;
  --color-text: #FFFFFF;
  /* ... 其他变量 */
}

/* 彩色模式 - 日落橙 */
[data-theme="color"][data-color-theme="sunset-orange"] {
  --color-primary: #FF6B35;
  --color-background: #FFF8F0;
  --color-text: #2D1B00;
  /* ... 其他变量 */
}

/* 彩色模式 - 森林绿 */
[data-theme="color"][data-color-theme="forest-green"] {
  --color-primary: #2E8B57;
  --color-background: #F5FFF5;
  --color-text: #1A3C27;
  /* ... 其他变量 */
}
```

### 2. React Context 实现

```typescript
// ThemeContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';

interface ThemeContextType {
  theme: ThemeConfig;
  colorThemes: ColorTheme[];
  setThemeMode: (mode: ThemeMode) => void;
  setColorTheme: (themeId: string) => void;
  toggleFollowSystem: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<ThemeConfig>(() => {
    // 从 localStorage 恢复
    const saved = localStorage.getItem('theme-config');
    return saved ? JSON.parse(saved) : defaultTheme;
  });

  const colorThemes: ColorTheme[] = [
    {
      id: 'sunset-orange',
      name: '日落橙',
      colors: { /* 配色方案 */ },
      isPreset: true
    },
    // ... 其他预设主题
  ];

  // 应用主题到 DOM
  useEffect(() => {
    const root = document.documentElement;
    
    // 设置主题属性
    root.setAttribute('data-theme', theme.mode);
    if (theme.mode === 'color' && theme.colorThemeId) {
      root.setAttribute('data-color-theme', theme.colorThemeId);
    } else {
      root.removeAttribute('data-color-theme');
    }

    // 保存到 localStorage
    localStorage.setItem('theme-config', JSON.stringify(theme));
  }, [theme]);

  // 监听系统主题变化
  useEffect(() => {
    if (!theme.followSystem) return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      setTheme(prev => ({
        ...prev,
        mode: e.matches ? 'dark' : 'light'
      }));
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme.followSystem]);

  const value = {
    theme,
    colorThemes,
    setThemeMode: (mode: ThemeMode) => 
      setTheme(prev => ({ ...prev, mode })),
    setColorTheme: (themeId: string) => 
      setTheme(prev => ({ ...prev, colorThemeId: themeId })),
    toggleFollowSystem: () => 
      setTheme(prev => ({ ...prev, followSystem: !prev.followSystem }))
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};
```

### 3. 主题切换组件

```typescript
// ThemeSelector.tsx
import React from 'react';
import { useTheme } from '../contexts/ThemeContext';

export const ThemeSelector: React.FC = () => {
  const { theme, colorThemes, setThemeMode, setColorTheme } = useTheme();

  return (
    <div className="theme-selector">
      <div className="theme-mode-selector">
        <button 
          onClick={() => setThemeMode('light')}
          className={theme.mode === 'light' ? 'active' : ''}
        >
          浅色
        </button>
        <button 
          onClick={() => setThemeMode('dark')}
          className={theme.mode === 'dark' ? 'active' : ''}
        >
          深色
        </button>
        <button 
          onClick={() => setThemeMode('color')}
          className={theme.mode === 'color' ? 'active' : ''}
        >
          彩色
        </button>
      </div>

      {theme.mode === 'color' && (
        <div className="color-theme-grid">
          {colorThemes.map(colorTheme => (
            <div
              key={colorTheme.id}
              className={`color-theme-item ${
                theme.colorThemeId === colorTheme.id ? 'active' : ''
              }`}
              onClick={() => setColorTheme(colorTheme.id)}
              style={{
                backgroundColor: colorTheme.colors.primary,
                color: colorTheme.colors.text
              }}
            >
              <div className="color-preview">
                <div style={{ backgroundColor: colorTheme.colors.primary }} />
                <div style={{ backgroundColor: colorTheme.colors.secondary }} />
                <div style={{ backgroundColor: colorTheme.colors.background }} />
              </div>
              <span>{colorTheme.name}</span>
            </div>
          ))}
        </div>
      )}

      <div className="system-follow-toggle">
        <label>
          <input
            type="checkbox"
            checked={theme.followSystem}
            onChange={() => {}}
          />
          跟随系统主题
        </label>
      </div>
    </div>
  );
};
```

## 预设彩色主题

### 1. 日落橙 (Sunset Orange)
- 主色: #FF6B35 (活力橙色)
- 背景色: #FFF8F0 (暖白)
- 文字色: #2D1B00 (深棕色)
- 适用场景: 创意写作、日记

### 2. 森林绿 (Forest Green)
- 主色: #2E8B57 (森林绿)
- 背景色: #F5FFF5 (淡绿)
- 文字色: #1A3C27 (深绿)
- 适用场景: 技术文档、学习笔记

### 3. 海洋蓝 (Ocean Blue)
- 主色: #1E90FF (道奇蓝)
- 背景色: #F0F8FF (爱丽丝蓝)
- 文字色: #0A2E5C (深蓝)
- 适用场景: 专业写作、报告

### 4. 薰衣草紫 (Lavender Purple)
- 主色: #9370DB (中紫)
- 背景色: #F8F0FF (淡紫)
- 文字色: #3C1E5C (深紫)
- 适用场景: 诗歌、文学创作

### 5. 玫瑰粉 (Rose Pink)
- 主色: #FF69B4 (热粉红)
- 背景色: #FFF0F5 (淡粉)
- 文字色: #5C1E3C (深玫瑰)
- 适用场景: 个人博客、情感记录

## 性能优化

### 1. CSS 变量优化
- 使用 CSS 自定义属性实现主题切换，避免重绘
- 预加载所有主题的 CSS 变量定义
- 使用 `will-change: opacity` 优化过渡动画

### 2. 代码分割
- 主题相关组件按需加载
- 彩色主题配置懒加载
- 主题切换动画使用 CSS 而非 JavaScript

### 3. 存储优化
- 使用 IndexedDB 存储用户自定义主题
- 压缩主题配置数据
- 实现增量同步策略

## 测试策略

### 1. 单元测试
- 测试主题切换逻辑
- 测试颜色计算函数
- 测试持久化存储

### 2. 集成测试
- 测试主题与组件集成
- 测试系统主题跟随
- 测试多设备同步

### 3. 视觉测试
- 截图对比不同主题
- 可访问性测试（对比度检查）
- 跨浏览器兼容性测试

## 部署计划

### Phase 1: 基础架构 (v1.3.0)
- 实现主题系统基础架构
- 支持浅色/深色/彩色模式切换
- 5个预设彩色主题
- 本地存储用户偏好

### Phase 2: 高级功能 (v1.3.1)
- 自定义颜色主题
- 主题分享功能
- 云端同步主题偏好
- A/B 测试数据分析

### Phase 3: 生态系统 (v1.4.0)
- 主题市场（用户创作主题）
- 主题导入/导出
- 主题推荐算法
- 与编辑器插件集成

## 风险评估

### 技术风险
1. **CSS 变量兼容性**: 需要确保支持 IE11 等旧浏览器
   - 缓解方案: 提供回退方案，使用 CSS 类名降级

2. **性能影响**: 频繁主题切换可能导致性能问题
   - 缓解方案: 实现防抖机制，优化 CSS 计算

3. **颜色对比度**: 确保所有主题满足 WCAG 可访问性标准
   - 缓解方案: 使用自动化工具检查对比度

### 产品风险
1. **用户接受度**: 用户可能不习惯彩色模式
   - 缓解方案: 渐进式推出，收集用户反馈

2. **功能复杂度**: 过多选项可能让用户困惑
   - 缓解方案: 提供智能推荐和简化模式

## 变更记录

### v1.3.0 (计划中)
- 新增彩色模式支持
- 5个预设彩色主题
- 主题系统基础架构
- 用户偏好本地存储

### v1.2.2 (已上线)
- 深色模式全量上线
- 基础主题切换功能
- 系统主题跟随支持