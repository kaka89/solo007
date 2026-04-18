# 百度首页 Demo - 使用指南

## 快速开始

### 方法1：直接打开HTML文件
1. 双击 `baidu-demo.html` 文件
2. 使用浏览器打开即可

### 方法2：使用HTTP服务器（推荐）
```bash
# 进入code目录
cd /path/to/solo007/code

# 方法A：使用启动脚本（macOS/Linux）
./start-demo.sh

# 方法B：直接运行Python脚本
python3 server.py

# 方法C：指定端口
python3 server.py --port 8080

# 方法D：不自动打开浏览器
python3 server.py --no-browser
```

### 方法3：使用其他HTTP服务器
```bash
# 使用Python内置服务器
python3 -m http.server 8000

# 使用Node.js的http-server
npx http-server -p 8000

# 使用PHP内置服务器
php -S localhost:8000
```

## 功能演示

### 1. 基本交互
- **搜索框**: 点击输入文字，获得焦点时有蓝色边框
- **导航链接**: 鼠标悬停时变为蓝色
- **更多菜单**: 鼠标悬停在"更多"上显示下拉选项
- **按钮**: "百度一下"和"手气不错"按钮的点击效果

### 2. 搜索功能演示
- 在搜索框中输入文字
- 点击"百度一下"按钮 → 显示搜索提示
- 点击"手气不错"按钮 → 显示随机搜索提示
- 按回车键 → 触发搜索

### 3. 其他功能
- **语音搜索图标** 🎤: 点击显示语音搜索提示
- **图片搜索图标** 📷: 点击显示图片搜索提示
- **登录按钮**: 点击显示登录提示

## 开发说明

### 文件结构
```
code/
├── baidu-demo.html      # 主HTML文件（包含所有代码）
├── server.py           # Python HTTP服务器
├── start-demo.sh       # 启动脚本（macOS/Linux）
├── README.md           # 项目说明
└── USAGE.md           # 使用指南（本文档）
```

### 技术特点
1. **纯前端实现**: 无需后端，所有功能在浏览器中运行
2. **响应式设计**: 适配桌面和移动设备
3. **现代CSS**: 使用Flexbox布局和CSS过渡动画
4. **交互丰富**: 多种鼠标和点击交互效果
5. **语义化HTML**: 良好的可访问性基础

### 浏览器兼容性
- ✅ Chrome 60+
- ✅ Firefox 55+
- ✅ Safari 11+
- ✅ Edge 79+
- ✅ 移动端浏览器

## 常见问题

### Q1: 页面无法正常显示
- 检查浏览器是否支持现代CSS特性
- 尝试使用Chrome或Firefox最新版本
- 检查控制台是否有错误信息

### Q2: HTTP服务器无法启动
- 确保Python 3已安装
- 检查端口是否被占用（默认8000端口）
- 尝试使用其他端口：`python3 server.py --port 8080`

### Q3: 某些功能不工作
- 确保JavaScript未被浏览器阻止
- 检查浏览器控制台是否有错误
- 尝试禁用浏览器扩展程序

### Q4: 移动端显示异常
- 页面已适配移动端，但某些旧版浏览器可能有问题
- 确保使用最新版移动浏览器
- 可以尝试调整浏览器缩放

## 扩展开发

### 添加新功能
1. **修改HTML**: 编辑 `baidu-demo.html` 文件
2. **修改样式**: 在 `<style>` 标签中添加CSS
3. **修改交互**: 在 `<script>` 标签中添加JavaScript

### 示例：添加新按钮
```html
<!-- 在搜索按钮区域添加 -->
<button class="search-btn" id="newBtn">新功能</button>

<script>
// 在JavaScript部分添加
document.getElementById('newBtn').addEventListener('click', function() {
    alert('新功能按钮被点击！');
});
</script>
```

### 示例：修改颜色主题
```css
/* 修改主色调 */
.search-btn.primary {
    background-color: #ff6b6b; /* 改为红色 */
}

.logo-text span:nth-child(1) { 
    color: #ff6b6b; /* 修改Logo颜色 */
}
```

## 注意事项

1. 这是一个演示页面，不包含真实的后端功能
2. 所有搜索都是模拟的，不会访问真实搜索引擎
3. 页面设计参考百度首页，但进行了简化和修改
4. 仅供学习和演示使用

## 反馈与支持

如有问题或建议，请查看项目文档或联系开发者。

---

**最后更新**: 2026-04-18  
**版本**: 1.0.0  
**状态**: 演示版本