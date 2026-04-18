# 删除头像功能 - SDD

## 技术方案

### 系统架构

```
前端 (React/Next.js)         后端 (Node.js/Express)         存储层
     │                              │                          │
     │ 1. 点击删除按钮              │                          │
     │─────────────────────────────>│                          │
     │                              │                          │
     │ 2. 显示确认对话框            │                          │
     │<─────────────────────────────│                          │
     │                              │                          │
     │ 3. 用户确认删除              │                          │
     │─────────────────────────────>│                          │
     │                              │ 4. 验证权限和CSRF token  │
     │                              │─────────────────────────>│
     │                              │                          │
     │                              │ 5. 删除存储文件          │
     │                              │─────────────────────────>│
     │                              │                          │
     │                              │ 6. 更新数据库记录        │
     │                              │─────────────────────────>│
     │                              │                          │
     │ 7. 返回成功响应              │                          │
     │<─────────────────────────────│                          │
     │                              │                          │
     │ 8. 更新UI显示默认头像        │                          │
     │                              │                          │
```

### 前端实现

#### 组件结构
```jsx
// AvatarDeleteButton.jsx
import { useState } from 'react';
import { deleteAvatar } from '@/lib/api/avatar';
import ConfirmationDialog from '@/components/ui/ConfirmationDialog';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export default function AvatarDeleteButton({ userId, onSuccess, onError }) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await deleteAvatar(userId);
      onSuccess?.();
      // 显示成功提示
      showToast('头像已成功删除', 'success');
    } catch (error) {
      onError?.(error);
      // 显示错误提示
      showToast(error.message || '删除失败，请重试', 'error');
    } finally {
      setIsDeleting(false);
      setShowConfirm(false);
    }
  };

  return (
    <>
      <button
        type="button"
        onClick={() => setShowConfirm(true)}
        className="btn btn-danger"
        disabled={isDeleting}
        aria-label="删除头像"
      >
        {isDeleting ? <LoadingSpinner size="sm" /> : '删除头像'}
      </button>

      <ConfirmationDialog
        isOpen={showConfirm}
        onClose={() => setShowConfirm(false)}
        onConfirm={handleDelete}
        title="确认删除头像"
        message="删除后您的头像将恢复为默认头像，此操作不可撤销。"
        confirmText="确认删除"
        cancelText="取消"
        variant="danger"
      />
    </>
  );
}
```

#### API客户端
```javascript
// lib/api/avatar.js
import apiClient from './client';

export const deleteAvatar = async (userId) => {
  const response = await apiClient.delete(`/api/users/${userId}/avatar`, {
    headers: {
      'X-CSRF-Token': getCSRFToken(),
    },
  });
  return response.data;
};

export const getDefaultAvatarUrl = () => {
  // 返回默认头像URL，可以配置化
  return '/images/default-avatar.svg';
};
```

#### 头像显示组件更新
```jsx
// UserAvatar.jsx
import { useState, useEffect } from 'react';
import { getDefaultAvatarUrl } from '@/lib/api/avatar';

export default function UserAvatar({ userId, avatarUrl, size = 'md' }) {
  const [currentAvatar, setCurrentAvatar] = useState(avatarUrl || getDefaultAvatarUrl());
  
  // 监听avatarUrl变化
  useEffect(() => {
    setCurrentAvatar(avatarUrl || getDefaultAvatarUrl());
  }, [avatarUrl]);

  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-16 h-16',
    xl: 'w-24 h-24',
  };

  return (
    <img
      src={currentAvatar}
      alt="用户头像"
      className={`rounded-full ${sizeClasses[size]} object-cover`}
      onError={() => setCurrentAvatar(getDefaultAvatarUrl())}
    />
  );
}
```

### 后端实现

#### 路由定义
```javascript
// routes/users.js
const express = require('express');
const router = express.Router();
const { authenticate } = require('../middleware/auth');
const { validateCSRF } = require('../middleware/security');
const avatarController = require('../controllers/avatarController');

// 删除头像
router.delete(
  '/:userId/avatar',
  authenticate,
  validateCSRF,
  avatarController.deleteAvatar
);

module.exports = router;
```

#### 控制器
```javascript
// controllers/avatarController.js
const User = require('../models/User');
const avatarService = require('../services/avatarService');
const logger = require('../utils/logger');

exports.deleteAvatar = async (req, res, next) => {
  try {
    const { userId } = req.params;
    const currentUserId = req.user.id;

    // 权限验证：只能删除自己的头像
    if (userId !== currentUserId) {
      return res.status(403).json({
        error: 'FORBIDDEN',
        message: '您没有权限删除此头像',
      });
    }

    // 获取用户信息
    const user = await User.findById(userId);
    if (!user) {
      return res.status(404).json({
        error: 'USER_NOT_FOUND',
        message: '用户不存在',
      });
    }

    // 删除头像文件（如果存在）
    if (user.avatarUrl && user.avatarUrl !== avatarService.getDefaultAvatarUrl()) {
      await avatarService.deleteAvatarFile(user.avatarUrl);
    }

    // 更新用户记录
    user.avatarUrl = avatarService.getDefaultAvatarUrl();
    user.avatarUpdatedAt = new Date();
    await user.save();

    // 记录操作日志
    logger.info('Avatar deleted', {
      userId,
      ip: req.ip,
      userAgent: req.get('User-Agent'),
      timestamp: new Date().toISOString(),
    });

    // 返回成功响应
    res.json({
      success: true,
      message: '头像删除成功',
      data: {
        avatarUrl: user.avatarUrl,
        updatedAt: user.avatarUpdatedAt,
      },
    });
  } catch (error) {
    logger.error('Failed to delete avatar', {
      error: error.message,
      userId: req.params.userId,
      stack: error.stack,
    });
    
    next(error);
  }
};
```

#### 服务层
```javascript
// services/avatarService.js
const fs = require('fs').promises;
const path = require('path');
const { Storage } = require('@google-cloud/storage');
const config = require('../config');

class AvatarService {
  constructor() {
    // 初始化存储客户端（示例：Google Cloud Storage）
    this.storage = config.storage.enabled 
      ? new Storage({ keyFilename: config.storage.keyFile })
      : null;
    this.bucketName = config.storage.bucket;
  }

  // 获取默认头像URL
  getDefaultAvatarUrl() {
    return `${config.app.baseUrl}/images/default-avatar.svg`;
  }

  // 删除头像文件
  async deleteAvatarFile(avatarUrl) {
    try {
      // 解析URL获取文件路径
      const filePath = this.extractFilePathFromUrl(avatarUrl);
      
      if (!filePath) {
        throw new Error('Invalid avatar URL');
      }

      if (this.storage) {
        // 云存储删除
        await this.storage.bucket(this.bucketName).file(filePath).delete();
      } else {
        // 本地文件系统删除
        const fullPath = path.join(config.upload.directory, filePath);
        await fs.unlink(fullPath);
      }

      return true;
    } catch (error) {
      // 如果文件不存在，不视为错误
      if (error.code === 'ENOENT' || error.code === 404) {
        console.warn(`Avatar file not found: ${avatarUrl}`);
        return true;
      }
      throw error;
    }
  }

  // 从URL中提取文件路径
  extractFilePathFromUrl(url) {
    try {
      const urlObj = new URL(url);
      // 移除开头的斜杠
      return urlObj.pathname.replace(/^\//, '');
    } catch {
      // 如果不是有效的URL，可能是相对路径
      return url.replace(`${config.app.baseUrl}/`, '');
    }
  }

  // 清理孤立的头像文件（定时任务）
  async cleanupOrphanedAvatars() {
    // 实现逻辑：比较存储中的文件和数据库中的引用
    // 删除没有引用的文件
  }
}

module.exports = new AvatarService();
```

#### 数据模型更新
```javascript
// models/User.js
const mongoose = require('mongoose');
const avatarService = require('../services/avatarService');

const userSchema = new mongoose.Schema({
  // ... 其他字段
  avatarUrl: {
    type: String,
    default: avatarService.getDefaultAvatarUrl(),
  },
  avatarUpdatedAt: {
    type: Date,
    default: Date.now,
  },
  // 头像删除记录（用于审计）
  avatarHistory: [{
    action: {
      type: String,
      enum: ['upload', 'delete', 'update'],
    },
    timestamp: {
      type: Date,
      default: Date.now,
    },
    previousUrl: String,
    newUrl: String,
    ipAddress: String,
    userAgent: String,
  }],
}, {
  timestamps: true,
});

// 删除头像前的钩子
userSchema.pre('save', function(next) {
  if (this.isModified('avatarUrl')) {
    this.avatarUpdatedAt = new Date();
  }
  next();
});

module.exports = mongoose.model('User', userSchema);
```

### 数据库迁移

```sql
-- 如果使用SQL数据库
ALTER TABLE users 
ADD COLUMN avatar_url VARCHAR(500) DEFAULT '/images/default-avatar.svg',
ADD COLUMN avatar_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 创建头像操作历史表
CREATE TABLE avatar_history (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  action VARCHAR(20) NOT NULL, -- 'upload', 'delete', 'update'
  previous_url VARCHAR(500),
  new_url VARCHAR(500) NOT NULL,
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_avatar_history_user_id ON avatar_history(user_id);
CREATE INDEX idx_avatar_history_created_at ON avatar_history(created_at);
```

### 安全考虑

#### 1. 权限验证
- 用户只能删除自己的头像
- 管理员可以删除任何用户的头像（需要特殊权限）

#### 2. CSRF防护
```javascript
// middleware/security.js
const { v4: uuidv4 } = require('uuid');

exports.validateCSRF = (req, res, next) => {
  const clientToken = req.headers['x-csrf-token'];
  const sessionToken = req.session.csrfToken;

  if (!clientToken || clientToken !== sessionToken) {
    return res.status(403).json({
      error: 'CSRF_TOKEN_INVALID',
      message: '无效的安全令牌',
    });
  }

  next();
};

exports.generateCSRFToken = (req, res, next) => {
  if (!req.session.csrfToken) {
    req.session.csrfToken = uuidv4();
  }
  res.locals.csrfToken = req.session.csrfToken;
  next();
};
```

#### 3. 速率限制
```javascript
// middleware/rateLimit.js
const rateLimit = require('express-rate-limit');

const avatarDeleteLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15分钟
  max: 5, // 每个IP最多5次删除请求
  message: {
    error: 'RATE_LIMIT_EXCEEDED',
    message: '操作过于频繁，请15分钟后再试',
  },
  standardHeaders: true,
  legacyHeaders: false,
});

// 应用限制
router.delete('/:userId/avatar', avatarDeleteLimiter, avatarController.deleteAvatar);
```

### 错误处理

#### 前端错误处理
```javascript
// lib/errorHandler.js
export const handleAvatarDeleteError = (error) => {
  const { response } = error;
  
  if (!response) {
    return {
      title: '网络错误',
      message: '请检查网络连接后重试',
      type: 'network',
    };
  }

  switch (response.status) {
    case 403:
      return {
        title: '权限不足',
        message: '您没有权限删除此头像',
        type: 'permission',
      };
    case 404:
      return {
        title: '用户不存在',
        message: '用户信息不存在或已被删除',
        type: 'not_found',
      };
    case 429:
      return {
        title: '操作过于频繁',
        message: '请稍后再试',
        type: 'rate_limit',
      };
    default:
      return {
        title: '删除失败',
        message: response.data?.message || '服务器错误，请重试',
        type: 'server',
      };
  }
};
```

#### 后端错误处理中间件
```javascript
// middleware/errorHandler.js
const logger = require('../utils/logger');

module.exports = (err, req, res, next) => {
  logger.error('Unhandled error', {
    error: err.message,
    stack: err.stack,
    path: req.path,
    method: req.method,
    userId: req.user?.id,
  });

  // 文件系统错误
  if (err.code === 'ENOENT') {
    return res.status(404).json({
      error: 'FILE_NOT_FOUND',
      message: '头像文件不存在',
    });
  }

  // 存储服务错误
  if (err.code === 'STORAGE_ERROR') {
    return res.status(500).json({
      error: 'STORAGE_ERROR',
      message: '存储服务暂时不可用',
    });
  }

  // 默认错误响应
  res.status(500).json({
    error: 'INTERNAL_SERVER_ERROR',
    message: '服务器内部错误',
    // 开发环境显示详细错误
    ...(process.env.NODE_ENV === 'development' && { details: err.message }),
  });
};
```

### 测试策略

#### 单元测试
```javascript
// tests/unit/avatarController.test.js
describe('Avatar Controller', () => {
  describe('deleteAvatar', () => {
    it('should delete avatar successfully', async () => {
      // 模拟请求和响应
      // 验证权限检查
      // 验证文件删除
      // 验证数据库更新
      // 验证响应格式
    });

    it('should return 403 when deleting other user avatar', async () => {
      // 测试权限验证
    });

    it('should handle missing avatar gracefully', async () => {
      // 测试用户没有自定义头像的情况
    });
  });
});
```

#### 集成测试
```javascript
// tests/integration/avatarDelete.test.js
describe('Avatar Delete Integration', () => {
  let testUser;
  let authToken;

  beforeAll(async () => {
    // 创建测试用户
    // 获取认证令牌
  });

  it('should complete full delete flow', async () => {
    // 1. 上传测试头像
    // 2. 调用删除API
    // 3. 验证响应
    // 4. 验证数据库状态
    // 5. 验证文件系统
  });

  it('should show confirmation dialog in UI', async () => {
    // 使用Puppeteer或Cypress测试UI流程
  });
});
```

#### E2E测试
```javascript
// tests/e2e/avatar.spec.js
describe('Avatar Management', () => {
  it('should allow user to delete avatar', () => {
    // 登录
    // 导航到个人资料页面
    // 点击删除按钮
    // 确认对话框出现
    // 点击确认
    // 验证头像变为默认
    // 验证成功提示
  });
});
```

### 部署与监控

#### 环境配置
```yaml
# config/production.js
module.exports = {
  storage: {
    enabled: true,
    provider: 'gcs', // 或 's3', 'azure'
    bucket: 'myapp-avatars-prod',
    keyFile: process.env.GCS_KEY_FILE,
  },
  upload: {
    directory: '/var/www/uploads/avatars',
    maxFileSize: 5 * 1024 * 1024, // 5MB
  },
};
```

#### 监控指标
```javascript
// utils/metrics.js
const client = require('prom-client');

const avatarDeleteCounter = new client.Counter({
  name: 'avatar_delete_total',
  help: 'Total number of avatar delete operations',
  labelNames: ['status'], // success, error
});

const avatarDeleteDuration = new client.Histogram({
  name: 'avatar_delete_duration_seconds',
  help: 'Duration of avatar delete operations',
  buckets: [0.1, 0.5, 1, 2, 5],
});

// 在控制器中使用
exports.deleteAvatar = async (req, res, next) => {
  const endTimer = avatarDeleteDuration.startTimer();
  
  try {
    // ... 删除逻辑
    avatarDeleteCounter.inc({ status: 'success' });
  } catch (error) {
    avatarDeleteCounter.inc({ status: 'error' });
    throw error;
  } finally {
    endTimer();
  }
};
```

#### 告警规则
```yaml
# prometheus/alerts.yml
groups:
  - name: avatar_alerts
    rules:
      - alert: HighAvatarDeleteErrorRate
        expr: rate(avatar_delete_total{status="error"}[5m]) / rate(avatar_delete_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "头像删除错误率过高"
          description: "过去5分钟内头像删除错误率超过10%"
```

### 维护任务

#### 1. 定期清理任务
```javascript
// scripts/cleanupOrphanedAvatars.js
const avatarService = require('../services/avatarService');

async function cleanupOrphanedAvatars() {
  console.log('Starting orphaned avatar cleanup...');
  
  try {
    const deletedCount = await avatarService.cleanupOrphanedAvatars();
    console.log(`Cleaned up ${deletedCount} orphaned avatar files`);
  } catch (error) {
    console.error('Cleanup failed:', error);
    process.exit(1);
  }
}

// 添加到cron job
// 0 2 * * * node scripts/cleanupOrphanedAvatars.js
```

#### 2. 备份策略
- 重要用户的头像文件定期备份
- 删除操作前可考虑临时备份（根据隐私政策）
- 数据库变更记录保留90天

### 回滚计划

如果功能出现问题，按以下步骤回滚：

1. **前端回滚**：移除删除按钮组件，恢复原头像显示逻辑
2. **API回滚**：禁用删除端点，返回501状态码
3. **数据库回滚**：如果有破坏性变更，执行回滚迁移
4. **配置回滚**：恢复相关配置到之前版本

---

**技术负责人**：工程团队  
**创建时间**：2026-04-18  
**最后更新**：2026-04-18  
**状态**：草案  
**技术栈**：React, Node.js, Express, MongoDB/PostgreSQL, 云存储  
**复杂度**：中等  
**预估开发时间**：前端1-2天，后端1-2天，测试1天