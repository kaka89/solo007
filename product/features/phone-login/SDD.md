---
title: 手机号登录技术方案（含虚拟手机号支持）
feat: phone-login
lifecycle: living
created-at: 2026-04-18
updated-at: 2026-04-18
version: v1.3
---

# 手机号登录 SDD

## 概述
本文档描述手机号登录功能的技术实现方案，包括虚拟手机号支持、国际区号验证、验证码发送和验证等核心功能。

## 架构设计

### 系统架构图
```
┌─────────────────────────────────────────────────────────────┐
│                       客户端 (Web/Mobile)                    │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                     API Gateway / Load Balancer              │
└──────────────────────────────┬──────────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
           ┌─────────────────┐   ┌─────────────────┐
           │  认证服务        │   │  用户服务        │
           │  Auth Service   │   │  User Service   │
           └─────────────────┘   └─────────────────┘
                    │                     │
                    ▼                     ▼
           ┌─────────────────┐   ┌─────────────────┐
           │  验证码服务      │   │  数据库         │
           │  SMS Service    │   │  Database       │
           └─────────────────┘   └─────────────────┘
                    │
                    ▼
           ┌─────────────────────────────────────┐
           │       虚拟手机号服务提供商           │
           │  Virtual Phone Providers            │
           │  • TextNow API                      │
           │  • Google Voice API                 │
           │  • Burner API                       │
           └─────────────────────────────────────┘
```

### 组件说明
1. **客户端**：Web前端和移动端应用
2. **API Gateway**：请求路由、限流、认证
3. **认证服务**：处理登录、注册、验证码验证
4. **用户服务**：管理用户信息、权限
5. **验证码服务**：发送和验证短信验证码
6. **虚拟手机号服务**：集成第三方虚拟手机号API
7. **数据库**：存储用户、验证码、日志等数据

## 数据库设计

### 用户表 (users)
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) NOT NULL, -- 完整手机号（含区号）
    country_code VARCHAR(5) NOT NULL, -- 区号（如+86）
    phone_type VARCHAR(20) DEFAULT 'real', -- real/virtual/suspected
    virtual_provider VARCHAR(50), -- 虚拟手机号服务商
    risk_score DECIMAL(3,2) DEFAULT 0.0, -- 风险评分
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(phone_number)
);

CREATE INDEX idx_users_phone_number ON users(phone_number);
CREATE INDEX idx_users_phone_type ON users(phone_type);
CREATE INDEX idx_users_risk_score ON users(risk_score);
```

### 验证码表 (verification_codes)
```sql
CREATE TABLE verification_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) NOT NULL,
    country_code VARCHAR(5) NOT NULL,
    code VARCHAR(10) NOT NULL, -- 加密存储
    code_hash VARCHAR(64) NOT NULL, -- SHA256(code)
    phone_type VARCHAR(20) DEFAULT 'real',
    provider VARCHAR(50), -- 发送服务商
    status VARCHAR(20) DEFAULT 'pending', -- pending/used/expired
    send_count INTEGER DEFAULT 1,
    error_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_verification_codes_phone_number ON verification_codes(phone_number);
CREATE INDEX idx_verification_codes_expires_at ON verification_codes(expires_at);
CREATE INDEX idx_verification_codes_status ON verification_codes(status);
```

### 虚拟手机号识别规则表 (virtual_phone_rules)
```sql
CREATE TABLE virtual_phone_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_code VARCHAR(5) NOT NULL,
    prefix_pattern VARCHAR(20) NOT NULL, -- 号码前缀模式
    provider VARCHAR(50) NOT NULL, -- 服务提供商
    confidence DECIMAL(3,2) DEFAULT 1.0, -- 识别置信度
    is_active BOOLEAN DEFAULT TRUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_virtual_phone_rules_country_code ON virtual_phone_rules(country_code);
CREATE INDEX idx_virtual_phone_rules_prefix ON virtual_phone_rules(prefix_pattern);
```

### 频率限制表 (rate_limits)
```sql
CREATE TABLE rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_type VARCHAR(50) NOT NULL, -- phone/ip/provider
    key_value VARCHAR(100) NOT NULL, -- 具体值
    action VARCHAR(50) NOT NULL, -- send_verification/login_attempt
    count INTEGER DEFAULT 1,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_rate_limits_key ON rate_limits(key_type, key_value);
CREATE INDEX idx_rate_limits_period ON rate_limits(period_start, period_end);
```

## 核心算法

### 虚拟手机号识别算法
```python
class VirtualPhoneDetector:
    def __init__(self):
        self.rules = self.load_rules()
        self.provider_apis = self.init_provider_apis()
        
    def detect(self, phone_number: str, country_code: str) -> Dict:
        """
        检测手机号类型
        返回: {
            'type': 'real'|'virtual'|'suspected',
            'provider': 'textnow'|'google_voice'|'burner'|None,
            'confidence': 0.0-1.0,
            'risk_score': 0.0-1.0
        }
        """
        result = {
            'type': 'real',
            'provider': None,
            'confidence': 1.0,
            'risk_score': 0.0
        }
        
        # 1. 基于规则的检测
        rule_match = self.detect_by_rules(phone_number, country_code)
        if rule_match:
            result.update(rule_match)
            
        # 2. 基于服务商API的验证
        if result['type'] == 'virtual' or result['confidence'] < 0.8:
            api_result = self.verify_by_provider(phone_number, country_code)
            if api_result:
                result.update(api_result)
                
        # 3. 基于行为模式的检测
        behavior_result = self.analyze_behavior(phone_number)
        if behavior_result:
            result['risk_score'] = max(result['risk_score'], behavior_result['risk_score'])
            
        return result
    
    def detect_by_rules(self, phone_number: str, country_code: str) -> Optional[Dict]:
        """基于规则库检测"""
        for rule in self.rules:
            if rule['country_code'] == country_code:
                if re.match(rule['prefix_pattern'], phone_number):
                    return {
                        'type': 'virtual',
                        'provider': rule['provider'],
                        'confidence': rule['confidence'],
                        'risk_score': 0.3
                    }
        return None
    
    def verify_by_provider(self, phone_number: str, country_code: str) -> Optional[Dict]:
        """通过服务商API验证"""
        for provider_name, api in self.provider_apis.items():
            try:
                is_valid = api.verify_number(phone_number, country_code)
                if is_valid:
                    return {
                        'type': 'virtual',
                        'provider': provider_name,
                        'confidence': 0.95,
                        'risk_score': 0.2
                    }
            except Exception as e:
                logger.warning(f"Provider {provider_name} verification failed: {e}")
        return None
    
    def analyze_behavior(self, phone_number: str) -> Optional[Dict]:
        """分析用户行为模式"""
        # 查询历史行为数据
        behavior_data = self.get_behavior_data(phone_number)
        
        if not behavior_data:
            return None
            
        risk_score = 0.0
        
        # 1. 发送频率分析
        if behavior_data['send_count_24h'] > 10:
            risk_score += 0.3
            
        # 2. 使用模式分析
        if behavior_data['unique_ips'] > 5:
            risk_score += 0.2
            
        # 3. 时间模式分析
        if self.is_abnormal_time_pattern(behavior_data):
            risk_score += 0.2
            
        return {'risk_score': min(risk_score, 1.0)}
```

### 验证码发送流程
```python
class VerificationCodeService:
    def send_verification_code(self, phone_number: str, country_code: str) -> Dict:
        """
        发送验证码流程
        1. 验证手机号格式和类型
        2. 检查频率限制
        3. 选择发送渠道
        4. 发送验证码
        5. 记录发送结果
        """
        # 1. 验证手机号
        validation_result = self.validate_phone(phone_number, country_code)
        if not validation_result['valid']:
            return {'success': False, 'error': validation_result['error']}
            
        # 2. 检测手机号类型
        detector = VirtualPhoneDetector()
        phone_info = detector.detect(phone_number, country_code)
        
        # 3. 检查频率限制
        if not self.check_rate_limit(phone_number, phone_info):
            return {'success': False, 'error': 'rate_limit_exceeded'}
            
        # 4. 生成验证码
        code = self.generate_code()
        code_hash = self.hash_code(code)
        
        # 5. 选择发送渠道
        channel = self.select_channel(phone_info)
        
        # 6. 发送验证码
        send_result = self.send_via_channel(phone_number, code, channel)
        
        # 7. 保存记录
        self.save_verification_record(
            phone_number=phone_number,
            country_code=country_code,
            code_hash=code_hash,
            phone_type=phone_info['type'],
            provider=phone_info.get('provider'),
            channel=channel,
            expires_at=datetime.now() + timedelta(minutes=5)
        )
        
        return {
            'success': send_result['success'],
            'message': 'verification_code_sent',
            'channel': channel,
            'expires_in': 300  # 5分钟
        }
    
    def select_channel(self, phone_info: Dict) -> str:
        """选择发送渠道"""
        if phone_info['type'] == 'virtual':
            # 虚拟手机号优先使用服务商API
            if phone_info.get('provider'):
                return f"virtual_{phone_info['provider']}"
            else:
                return "virtual_sms_gateway"
        else:
            # 真实手机号使用短信网关
            return "sms_gateway"
    
    def send_via_channel(self, phone_number: str, code: str, channel: str) -> Dict:
        """通过指定渠道发送验证码"""
        if channel.startswith('virtual_'):
            provider = channel.replace('virtual_', '')
            return self.send_via_virtual_provider(phone_number, code, provider)
        else:
            return self.send_via_sms_gateway(phone_number, code)
```

### 验证码验证流程
```python
class VerificationValidator:
    def validate_code(self, phone_number: str, country_code: str, input_code: str) -> Dict:
        """
        验证验证码流程
        1. 验证输入格式
        2. 查询验证码记录
        3. 检查状态（是否已使用、过期）
        4. 验证码匹配
        5. 更新状态
        6. 处理登录/注册
        """
        # 1. 验证输入格式
        if not self.validate_input_format(input_code):
            return {'success': False, 'error': 'invalid_code_format'}
            
        # 2. 查询验证码记录
        record = self.get_latest_code_record(phone_number)
        if not record:
            return {'success': False, 'error': 'code_not_found'}
            
        # 3. 检查状态
        if record['status'] == 'used':
            return {'success': False, 'error': 'code_already_used'}
            
        if record['expires_at'] < datetime.now():
            return {'success': False, 'error': 'code_expired'}
            
        # 4. 验证码匹配
        input_hash = self.hash_code(input_code)
        if not self.secure_compare(input_hash, record['code_hash']):
            # 记录错误次数
            self.increment_error_count(record['id'])
            
            # 检查是否达到锁定阈值
            if self.should_lock_account(record):
                self.lock_account(phone_number)
                return {'success': False, 'error': 'account_locked'}
                
            return {'success': False, 'error': 'invalid_code'}
            
        # 5. 更新状态
        self.mark_code_as_used(record['id'])
        
        # 6. 处理登录/注册
        user_result = self.handle_user_auth(phone_number, country_code)
        
        return {
            'success': True,
            'user_exists': user_result['exists'],
            'user_id': user_result.get('user_id'),
            'token': user_result.get('token'),
            'requires_profile_setup': not user_result.get('profile_complete', True)
        }
    
    def handle_user_auth(self, phone_number: str, country_code: str) -> Dict:
        """处理用户认证（登录或注册）"""
        # 检查用户是否存在
        user = self.get_user_by_phone(phone_number)
        
        if user:
            # 用户存在，执行登录
            token = self.generate_auth_token(user['id'])
            self.update_last_login(user['id'])
            
            return {
                'exists': True,
                'user_id': user['id'],
                'token': token,
                'profile_complete': user.get('profile_complete', True)
            }
        else:
            # 用户不存在，创建新用户
            # 检测手机号类型
            detector = VirtualPhoneDetector()
            phone_info = detector.detect(phone_number, country_code)
            
            new_user = self.create_user(
                phone_number=phone_number,
                country_code=country_code,
                phone_type=phone_info['type'],
                virtual_provider=phone_info.get('provider'),
                risk_score=phone_info['risk_score']
            )
            
            token = self.generate_auth_token(new_user['id'])
            
            return {
                'exists': False,
                'user_id': new_user['id'],
                'token': token,
                'profile_complete': False  # 新用户需要完善资料
            }
```

## API设计

### 发送验证码 API
```http
POST /api/v1/auth/send-verification-code
Content-Type: application/json

{
  "phone_number": "13800138000",
  "country_code": "+86"
}

Response:
{
  "success": true,
  "message": "verification_code_sent",
  "channel": "sms_gateway", // 或 "virtual_textnow"
  "expires_in": 300,
  "next_retry_after": 60 // 秒
}
```

### 验证验证码 API
```http
POST /api/v1/auth/verify-code
Content-Type: application/json

{
  "phone_number": "13800138000",
  "country_code": "+86",
  "code": "123456"
}

Response:
{
  "success": true,
  "user_exists": true,
  "user_id": "uuid",
  "token": "jwt_token",
  "requires_profile_setup": false,
  "phone_type": "real" // real/virtual/suspected
}
```

### 虚拟手机号检测 API（内部）
```http
POST /api/internal/phone/detect-type
Content-Type: application/json

{
  "phone_number": "5551234567",
  "country_code": "+1"
}

Response:
{
  "type": "virtual",
  "provider": "textnow",
  "confidence": 0.95,
  "risk_score": 0.2,
  "suggested_action": "allow" // allow/limit/block/review
}
```

## 安全设计

### 频率限制策略
```yaml
rate_limits:
  # 基于手机号的限制
  per_phone:
    verification_send:
      window: 3600  # 1小时
      max_attempts: 3  # 虚拟手机号
      max_attempts_real: 10  # 真实手机号
    login_attempt:
      window: 3600
      max_attempts: 5
      
  # 基于IP的限制
  per_ip:
    verification_send:
      window: 3600
      max_attempts: 20
    registration:
      window: 86400  # 24小时
      max_attempts: 50
      
  # 基于服务商的限制
  per_provider:
    verification_send:
      window: 60  # 1分钟
      max_attempts: 10
```

### 风险评分模型
```python
class RiskScorer:
    def calculate_risk(self, phone_info: Dict, behavior_data: Dict) -> float:
        """计算风险评分（0.0-1.0）"""
        risk_score = 0.0
        
        # 1. 手机号类型风险
        if phone_info['type'] == 'virtual':
            risk_score += 0.3
        elif phone_info['type'] == 'suspected':
            risk_score += 0.5
            
        # 2. 服务商风险
        provider_risk = self.get_provider_risk(phone_info.get('provider'))
        risk_score += provider_risk * 0.2
        
        # 3. 行为风险
        if behavior_data['send_count_24h'] > 5:
            risk_score += 0.2
            
        if behavior_data['unique_ips'] > 3:
            risk_score += 0.15
            
        if self.has_abnormal_pattern(behavior_data):
            risk_score += 0.25
            
        # 4. 时间风险
        if self.is_off_hours():
            risk_score += 0.1
            
        return min(risk_score, 1.0)
    
    def get_action_by_risk(self, risk_score: float) -> str:
        """根据风险评分决定行动"""
        if risk_score < 0.3:
            return "allow"
        elif risk_score < 0.6:
            return "limit"  # 增加验证或限制频率
        elif risk_score < 0.8:
            return "review"  # 需要人工审核
        else:
            return "block"  # 直接阻止
```

### 数据加密
1. **验证码加密**：使用SHA256哈希存储，加盐处理
2. **敏感数据加密**：用户手机号等敏感信息加密存储
3. **传输加密**：所有API使用HTTPS
4. **密钥管理**：使用密钥管理服务（KMS）管理API密钥

## 监控与日志

### 关键指标
```yaml
metrics:
  # 发送相关
  verification_send_total
  verification_send_success_rate
  verification_send_latency_seconds
  virtual_phone_send_total
  virtual_phone_success_rate
  
  # 验证相关
  verification_validate_total
  verification_validate_success_rate
  verification_validate_error_by_type
  
  # 安全相关
  rate_limit_hits_total
  risk_score_distribution
  blocked_attempts_total
  
  # 用户相关
  new_users_total
  virtual_phone_users_total
  user_conversion_rate
```

### 日志格式
```json
{
  "timestamp": "2026-04-18T10:30:00Z",
  "level": "INFO",
  "service": "auth-service",
  "event": "verification_code_sent",
  "phone_number": "***",  // 脱敏处理
  "country_code": "+86",
  "phone_type": "virtual",
  "provider": "textnow",
  "channel": "virtual_textnow",
  "success": true,
  "latency_ms": 1200,
  "request_id": "req_123456"
}
```

## 部署配置

### 环境变量
```bash
# 虚拟手机号服务商配置
TEXTNOW_API_KEY=xxx
TEXTNOW_API_SECRET=xxx
GOOGLE_VOICE_CLIENT_ID=xxx
GOOGLE_VOICE_CLIENT_SECRET=xxx
BURNER_API_KEY=xxx

# 短信服务商配置
SMS_PROVIDER=twilio  # 或 aliyun, tencent
TWILIO_ACCOUNT_SID=xxx
TWILIO_AUTH_TOKEN=xxx

# 安全配置
VIRTUAL_PHONE_ENABLED=true
VIRTUAL_PHONE_RISK_THRESHOLD=0.6
VIRTUAL_PHONE_REQUIRE_EXTRA_VERIFICATION=true

# 频率限制配置
RATE_LIMIT_VIRTUAL_PHONE_PER_HOUR=3
RATE_LIMIT_REAL_PHONE_PER_HOUR=10
RATE_LIMIT_IP_PER_HOUR=20
```

### Docker配置
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

## 测试策略

### 单元测试
```python
def test_virtual_phone_detection():
    detector = VirtualPhoneDetector()
    
    # 测试虚拟手机号识别
    result = detector.detect("5551234567", "+1")
    assert result['type'] == 'virtual'
    assert result['provider'] == 'textnow'
    assert result['confidence'] > 0.8
    
    # 测试真实手机号识别
    result = detector.detect("13800138000", "+86")
    assert result['type'] == 'real'
    assert result['confidence'] > 0.9
```

### 集成测试
```python
def test_verification_flow():
    # 测试完整验证码流程
    service = VerificationCodeService()
    
    # 发送验证码
    send_result = service.send_verification_code("5551234567", "+1")
    assert send_result['success'] == True
    assert 'channel' in send_result
    
    # 验证验证码
    validator = VerificationValidator()
    verify_result = validator.validate_code("5551234567", "+1", "123456")
    assert verify_result['success'] == True
    assert 'token' in verify_result
```

### 性能测试
```bash
# 虚拟手机号识别性能测试
ab -n 1000 -c 10 -p test_data.json -T application/json \
  http://localhost:8000/api/internal/phone/detect-type

# 验证码发送性能测试
ab -n 500 -c 5 -p send_data.json -T application/json \
  http://localhost:8000/api/v1/auth/send-verification-code
```

## 回滚计划

### 回滚条件
1. 虚拟手机号识别错误率 > 5%
2. 验证码发送失败率 > 10%
3. 用户投诉率 > 1%
4. 系统性能下降 > 30%

### 回滚步骤
1. 停止新版本服务
2. 恢复数据库备份（如有数据变更）
3. 启动旧版本服务
4. 验证功能正常
5. 通知相关团队

## 后续优化

### 短期优化（1-2周）
1. 增加更多虚拟手机号服务提供商支持
2. 优化识别算法准确率
3. 完善监控告警机制

### 中期优化（1-2月）
1. 引入机器学习模型改进风险评分
2. 实现自适应频率限制
3. 增加多因素认证支持

### 长期优化（3-6月）
1. 构建虚拟手机号信誉系统
2. 实现跨服务商号码池管理
3. 开发虚拟手机号管理控制台