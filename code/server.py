#!/usr/bin/env python3
"""
简单的HTTP服务器，用于预览百度首页Demo
"""

import http.server
import socketserver
import webbrowser
import os
import sys

PORT = 8000

class DemoHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器"""
    
    def end_headers(self):
        # 添加CORS头，方便开发
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    
    def log_message(self, format, *args):
        # 简化日志输出
        print(f"[{self.log_date_time_string()}] {format % args}")

def main():
    """启动HTTP服务器"""
    
    # 切换到当前目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 检查文件是否存在
    if not os.path.exists('baidu-demo.html'):
        print("错误: 找不到 baidu-demo.html 文件")
        print("请确保在正确的目录中运行此脚本")
        sys.exit(1)
    
    try:
        # 创建HTTP服务器
        with socketserver.TCPServer(("", PORT), DemoHTTPRequestHandler) as httpd:
            print("=" * 60)
            print("百度首页 Demo - HTTP服务器")
            print("=" * 60)
            print(f"服务器运行在: http://localhost:{PORT}/")
            print(f"主页面: http://localhost:{PORT}/baidu-demo.html")
            print("")
            print("可用文件:")
            print(f"  • baidu-demo.html - 百度首页Demo")
            print(f"  • README.md - 说明文档")
            print("")
            print("按 Ctrl+C 停止服务器")
            print("=" * 60)
            
            # 尝试自动打开浏览器
            try:
                webbrowser.open(f'http://localhost:{PORT}/baidu-demo.html')
                print("已尝试在浏览器中打开页面...")
            except:
                print("无法自动打开浏览器，请手动访问上述URL")
            
            # 启动服务器
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"错误: 端口 {PORT} 已被占用")
            print("请尝试:")
            print(f"  1. 关闭占用端口 {PORT} 的程序")
            print(f"  2. 使用其他端口: python server.py --port 8080")
        else:
            print(f"服务器错误: {e}")
    except Exception as e:
        print(f"未知错误: {e}")

if __name__ == "__main__":
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='启动百度首页Demo HTTP服务器')
    parser.add_argument('--port', type=int, default=PORT, 
                       help=f'服务器端口 (默认: {PORT})')
    parser.add_argument('--no-browser', action='store_true',
                       help='不自动打开浏览器')
    
    args = parser.parse_args()
    PORT = args.port
    
    if args.no_browser:
        # 临时覆盖webbrowser.open函数
        import types
        webbrowser.open = lambda url: None
    
    main()