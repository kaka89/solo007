# K-001: 密码安全最佳实践

## 概述
本文档记录在实现用户修改密码功能时学到的密码安全最佳实践和注意事项。

## 密码存储安全

### 1. 哈希算法选择
- **推荐**: bcrypt, Argon2, scrypt
- **避免**: MD5, SHA-1, SHA-256（用于密码）
- **原因**: 专用密码哈希算法包含盐值和工作因子，抗暴力破解

### 2. bcrypt 最佳实践
```javascript
// Node.js 示例
const bcrypt = require('bcrypt');
const saltRounds = 12; // 工作因子，越高越安全但越慢

// 哈希密码
const hash = await bcrypt.hash(password, saltRounds);

// 验证密码
const isValid = await bcrypt.compare(password, hash);
```

### 3. 工作因子选择
- **开发环境**: 8-10（快速）
- **生产环境**: 12-14（平衡安全与性能）
- **高安全要求**: 15+（金融、医疗等）

## 密码强度验证

### 1. 最小要求
- 长度: ≥ 8 字符
- 包含: 大写字母、小写字母、数字
- 可选: 特殊字符（!@#$%^&*）

### 2. 常见弱密码检测
```javascript
const weakPasswords = [
  'password', '123456', 'qwerty', 'admin',
  'welcome', 'monkey', 'letmein', 'password1'
];

function isWeakPassword(password) {
  const lowerPassword = password.toLowerCase();
  return weakPasswords.some(weak => lowerPassword.includes(weak));
}
```

### 3. 模式检测
- 连续字符: abc, 123, 789
- 重复字符: aaa, 111
- 键盘模式: qwerty, asdfgh
- 个人信息: 用户名、邮箱、生日

## 传输安全

### 1. HTTPS 必须
- 所有密码相关请求必须使用 HTTPS
- 启用 HSTS（HTTP Strict Transport Security）
- 使用安全的 TLS 版本（TLS 1.2+）

### 2. 前端加密（可选）
```javascript
// 使用 Web Crypto API 或 libsodium
async function hashPasswordClientSide(password) {
  const encoder = new TextEncoder();
  const data = encoder.encode(password);
  const hash = await crypto.subtle.digest('SHA-256', data);
  return Array.from(new Uint8Array(hash))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}
```

## 用户体验与安全平衡

### 1. 实时验证反馈
- **即时反馈**: 用户输入时显示密码强度
- **明确要求**: 列出未满足的条件
- **建议生成**: 提供随机密码建议

### 2. 错误信息安全
- **安全**: "用户名或密码错误"（不指明具体）
- **不安全**: "密码错误"（泄露信息）

### 3. 防暴力破解
- **速率限制**: 同一 IP/用户每分钟最多 5 次尝试
- **账户锁定**: 连续 5 次失败后锁定 15 分钟
- **渐进延迟**: 失败次数越多，响应越慢

## 审计与监控

### 1. 日志记录
```javascript
// 密码修改日志
const passwordChangeLog = {
  userId: user.id,
  timestamp: new Date(),
  ipAddress: req.ip,
  userAgent: req.headers['user-agent'],
  success: true/false,
  reason: '密码修改成功' / '当前密码错误'
};
```

### 2. 监控指标
- 密码修改成功率/失败率
- 常见错误类型分布
- 暴力破解尝试次数
- 密码强度分布

### 3. 告警规则
- 同一用户短时间内多次失败尝试
- 同一 IP 大量密码修改请求
- 密码修改失败率突然升高

## 多设备会话管理

### 1. 修改密码后的会话处理
- **选项1**: 保持所有设备登录（用户体验好）
- **选项2**: 登出所有设备（安全性高）
- **选项3**: 让用户选择（平衡）

### 2. 实现建议
```javascript
// 修改密码后处理会话
async function handlePasswordChange(userId, newPasswordHash) {
  // 更新密码
  await updatePassword(userId, newPasswordHash);
  
  // 可选：使旧令牌失效
  await invalidateOldTokens(userId);
  
  // 可选：发送通知邮件
  await sendPasswordChangeNotification(userId);
}
```

## 测试要点

### 1. 安全测试
- SQL 注入测试
- XSS 攻击测试
- CSRF 保护测试
- 暴力破解防护测试

### 2. 功能测试
- 正常流程：正确密码修改
- 错误流程：错误当前密码
- 边界测试：最小/最大密码长度
- 并发测试：同时修改密码

### 3. 性能测试
- 密码哈希性能（不同工作因子）
- 高并发下的响应时间
- 内存使用情况

## 常见陷阱

### 1. 密码长度限制
- **问题**: 前端/后端长度限制不一致
- **解决**: 统一验证规则，前端提示最大长度

### 2. 特殊字符处理
- **问题**: 某些特殊字符导致存储/验证问题
- **解决**: 明确允许的字符集，统一编码

### 3. 密码历史检查
- **问题**: 允许用户重复使用旧密码
- **解决**: 保存最近 N 次密码哈希，禁止重复使用

## 法规合规

### 1. GDPR 要求
- 用户有权删除账户（包括密码数据）
- 密码属于个人数据，需安全处理
- 数据泄露需在 72 小时内报告

### 2. PCI DSS（支付卡行业）
- 密码最小长度 7 字符
- 包含数字和字母
- 90 天强制修改密码（可选）

### 3. NIST 指南
- 取消定期强制修改密码要求
- 取消复杂字符要求
- 推荐使用密码管理器
- 实施黑名单检查

## 总结
密码安全是系统安全的基础。需要在安全性、用户体验和性能之间找到平衡点。关键原则：
1. **永远不存储明文密码**
2. **使用专用密码哈希算法**
3. **实施适当的速率限制**
4. **提供清晰的用户反馈**
5. **记录所有安全相关操作**

---
**创建时间**: 2026-04-18  
**更新记录**:  
- 2026-04-18: 创建文档，记录密码安全最佳实践  
**相关功能**: user-password-change  
**标签**: security, authentication, best-practices