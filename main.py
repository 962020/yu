from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, Response, session, flash
import os
import tempfile
from pathlib import Path
# import base64  # 暂时不需要，因为解密接口已注释
import requests
import logging
import pymysql
import pymysql.cursors
import hashlib
# video_service模块暂时不可用，注释掉相关导入
# from video_service import video_service
# from excel_analyzer import excel_analyzer  # 注释掉缺失的模块
# from pdf_to_html import pdf_to_html  # 注释掉缺失的模块
# from document_converter import document_converter  # 注释掉缺失的模块
import sys

app = Flask(__name__)

# 设置密钥，用于会话加密
# 生产环境中应使用固定的secret_key，确保会话一致性
# 这里使用一个随机生成的密钥，实际部署时应更改为安全的固定密钥
app.secret_key = os.environ.get('SECRET_KEY', 'a8c3f9e1d7b4c2a5b8d9e6f3g2h1i4j7k6l5m8n9o')

# 获取当前脚本的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 配置静态文件目录
app.static_folder = '.'

# 数据库连接配置
DB_CONFIG = {
    'host': 'mysql2.sqlpub.com',
    'port': 3307,
    'user': 'zhanghaoku',
    'password': 'gWJLgkTuXeP5sviN',
    'db': 'zhanghaoku',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# 创建数据库连接
def get_db_connection():
    try:
        print("尝试建立数据库连接...")
        connection = pymysql.connect(**DB_CONFIG)
        print("数据库连接成功")
        return connection
    except Exception as e:
        print(f"数据库连接失败: {str(e)}")
        # 重新抛出异常以便上层处理
        raise

# 确保用户表存在
def ensure_user_table_exists():
    print("开始初始化用户表...")
    connection = None
    try:
        connection = get_db_connection()
        print("数据库连接成功")
        
        with connection.cursor() as cursor:
            print("正在创建users表（如果不存在）...")
            # 创建users表（如果不存在）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("users表创建/验证完成")
            
            # 检查默认管理员是否存在
            print("检查默认管理员是否存在...")
            cursor.execute("SELECT * FROM users WHERE username = 'admin'")
            admin_exists = cursor.fetchone()
            
            if not admin_exists:
                print("没有找到默认管理员，创建默认管理员...")
                # 创建默认管理员用户，密码为admin123
                hashed_password = hashlib.sha256('admin123'.encode()).hexdigest()
                cursor.execute(
                    "INSERT INTO users (username, password) VALUES (%s, %s)",
                    ('admin', hashed_password)
                )
                print("默认管理员用户创建成功：admin / admin123")
            else:
                print("默认管理员用户已存在")
                
            # 显示当前所有用户
            cursor.execute("SELECT id, username, created_at FROM users")
            users = cursor.fetchall()
            print(f"当前用户表中有 {len(users)} 个用户:")
            for user in users:
                print(f"  - ID: {user['id']}, 用户名: {user['username']}")
        
        connection.commit()
        print("数据库事务提交成功")
    except Exception as e:
        print(f"初始化用户表时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        # 在生产环境中不要中断应用启动
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            connection.close()
            print("数据库连接已关闭")
        print("ensure_user_table_exists函数执行完毕")

# 应用启动时自动初始化
with app.app_context():
    try:
        print("应用启动中...")
        # 确保用户表存在，自动创建默认管理员
        ensure_user_table_exists()
        print("应用初始化完成")
    except Exception as e:
        print(f"应用初始化时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        print("应用继续启动，但某些功能可能受限")

# 登录验证装饰器
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # 如果未登录，重定向到登录页面
            return redirect('/login.html')
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
def index():
    # 重定向到首页，登录后才能访问
    if 'user_id' not in session:
        return redirect('/login.html')
    return redirect('/index.html')

@app.route('/login.html')
def login_page():
    # 提供登录页面
    print("访问登录页面")
    # 检查是否已登录
    if 'user_id' in session:
        print(f"用户 {session['username']} 已登录，重定向到首页")
        return redirect('/index.html')
    
    # 直接嵌入login.html内容
    login_html = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="description" content="VIP追剧神器 - 用户登录" />
  <meta name="keywords" content="VIP追剧,用户登录" />
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:">
  <title>VIP追剧神器 - 用户登录</title>
  <style>
    /* 全局样式和背景效果 */
    html, body {
      height: 100%;
      margin: 0;
      padding: 0;
      font-family: 'Microsoft YaHei', Arial, sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      overflow: hidden;
      position: relative;
    }

    /* 动态渐变背景 */
    .bg-container {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: -1;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      animation: gradientBG 15s ease infinite;
      background-size: 400% 400%;
    }

    @keyframes gradientBG {
      0% {
        background-position: 0% 50%;
      }
      50% {
        background-position: 100% 50%;
      }
      100% {
        background-position: 0% 50%;
      }
    }

    /* 粒子效果容器 */
    #particles-js {
      position: fixed;
      width: 100%;
      height: 100%;
      top: 0;
      left: 0;
      z-index: -1;
    }

    .login-container {
      background: rgba(255, 255, 255, 0.95);
      border-radius: 20px;
      padding: 2.5rem;
      box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2);
      width: 100%;
      max-width: 420px;
      backdrop-filter: blur(15px);
      animation: fadeInUp 0.6s ease-out;
      transition: all 0.3s ease;
    }

    .login-container:hover {
      transform: translateY(-5px);
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
    }

    @keyframes fadeInUp {
      from {
        opacity: 0;
        transform: translateY(30px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    /* 页面加载动画 */
    @keyframes pageLoad {
      0% {
        opacity: 0;
      }
      100% {
        opacity: 1;
      }
    }

    /* Logo脉冲动画 */
    @keyframes pulse {
      0% {
        transform: scale(1);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
      }
      50% {
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
      }
      100% {
        transform: scale(1);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
      }
    }
    
    /* Logo旋转动画 - 简化版 */
    @keyframes rotate {
      0% {
        transform: rotate(0deg);
      }
      100% {
        transform: rotate(360deg);
      }
    }

    .login-header {
      text-align: center;
      margin-bottom: 2rem;
    }

    .login-title {
      font-size: 2rem;
      color: #333;
      margin: 0 0 0.5rem 0;
      font-weight: bold;
    }

    .login-subtitle {
      color: #666;
      font-size: 1rem;
    }

    .login-form {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    /* 表单组设计 */
    .form-group {
      position: relative;
      margin-bottom: 1.5rem;
    }

    .form-group label {
      display: block;
      margin-bottom: 0.75rem;
      color: #555;
      font-weight: 600;
      font-size: 0.95rem;
      letter-spacing: 0.5px;
      transition: color 0.3s ease;
    }

    .form-group:focus-within label {
      color: #4a90e2;
    }

    /* 输入框容器 */
    .input-wrapper {
      position: relative;
      display: flex;
      align-items: center;
    }

    /* 输入框图标 */
    .input-icon {
      position: absolute;
      left: 15px;
      color: #999;
      font-size: 1.1rem;
      transition: color 0.3s ease;
      pointer-events: none;
    }

    .form-group:focus-within .input-icon {
      color: #4a90e2;
    }

    /* 现代输入框设计 */
    .form-input {
      width: 100%;
      padding: 1.1rem 1rem 1.1rem 3.5rem;
      border: 2px solid transparent;
      border-radius: 12px;
      font-size: 1rem;
      background: linear-gradient(white, white) padding-box,
                  linear-gradient(135deg, #667eea, #764ba2) border-box;
      transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
      box-sizing: border-box;
    }

    .form-input:focus {
      outline: none;
      background: linear-gradient(rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.9)) padding-box,
                  linear-gradient(135deg, #4a90e2, #357abd) border-box;
      box-shadow: 0 8px 25px rgba(74, 144, 226, 0.15);
      transform: translateY(-2px);
    }

    .form-input::placeholder {
      color: #999;
      transition: opacity 0.3s ease;
    }

    .form-input:focus::placeholder {
      opacity: 0.7;
    }

    /* 密码切换按钮 */
    .password-toggle {
      position: absolute;
      right: 15px;
      cursor: pointer;
      color: #666;
      font-size: 1.2rem;
      user-select: none;
      padding: 8px;
      border-radius: 50%;
      transition: all 0.3s ease;
    }
    
    /* 输入框提示文本样式 */
    .input-hint {
      font-size: 0.85rem;
      color: #666;
      margin-top: 0.5rem;
      padding-left: 0.5rem;
      opacity: 0.8;
      transition: opacity 0.3s ease;
    }
    
    .form-group:focus-within .input-hint {
      opacity: 1;
      color: #4a90e2;
    }

    .password-toggle:hover {
      background-color: rgba(0, 0, 0, 0.05);
      color: #4a90e2;
    }

    /* 现代登录按钮设计 */
    .login-button {
      position: relative;
      background: linear-gradient(135deg, #4a90e2, #357abd);
      color: white;
      border: none;
      padding: 1.1rem 2rem;
      border-radius: 12px;
      font-size: 1.1rem;
      font-weight: bold;
      cursor: pointer;
      transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
      margin-top: 1.5rem;
      overflow: hidden;
      box-shadow: 0 5px 15px rgba(74, 144, 226, 0.3);
      z-index: 1;
    }

    /* 按钮渐变覆盖层 */
    .login-button::before {
      content: '';
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(
        90deg,
        transparent,
        rgba(255, 255, 255, 0.2),
        transparent
      );
      transition: all 0.6s ease;
      z-index: -1;
    }

    /* 悬停效果 */
    .login-button:hover {
      transform: translateY(-4px) scale(1.02);
      box-shadow: 0 12px 25px rgba(74, 144, 226, 0.4);
    }

    /* 悬停时的光效 */
    .login-button:hover::before {
      left: 100%;
    }

    /* 点击效果 */
    .login-button:active {
      transform: translateY(-2px) scale(0.98);
      box-shadow: 0 6px 15px rgba(74, 144, 226, 0.3);
    }

    /* 禁用状态 */
    .login-button:disabled {
      background: linear-gradient(135deg, #ccc, #aaa);
      cursor: not-allowed;
      transform: none;
      box-shadow: none;
      opacity: 0.8;
    }

    /* 按钮加载状态 */
    .login-button:disabled::before {
      display: none;
    }

    /* 错误消息设计增强 */
    .error-message {
      background-color: #ffebee;
      color: #c62828;
      padding: 1rem;
      border-radius: 10px;
      font-size: 0.95rem;
      margin-bottom: 1.5rem;
      display: none;
      animation: slideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
      border-left: 4px solid #c62828;
      position: relative;
      overflow: hidden;
      box-shadow: 0 4px 12px rgba(198, 40, 40, 0.1);
    }

    .error-message::before {
      content: '⚠️';
      position: absolute;
      left: 12px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 1.2rem;
      margin-right: 0.5rem;
    }

    .error-message {
      padding-left: 2.5rem;
    }

    @keyframes slideIn {
      from {
        opacity: 0;
        transform: translateX(-10px);
      }
      to {
        opacity: 1;
        transform: translateX(0);
      }
    }

    .login-footer {
      text-align: center;
      margin-top: 1.5rem;
      color: #666;
      font-size: 0.9rem;
    }

    .logo-container {
      display: flex;
      justify-content: center;
      margin-bottom: 1.5rem;
      perspective: 1000px;
    }

    .logo {
      width: 80px;
      height: 80px;
      border-radius: 50%;
      object-fit: cover;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
      transform-origin: center;
      animation: rotate 5s linear infinite !important;
    }
    
    /* 为logo容器添加脉冲效果，避免动画冲突 */
    .logo-container {
      animation: pulse 3s ease-in-out infinite;
    }

    .logo:hover {
      box-shadow: 0 6px 25px rgba(0, 0, 0, 0.3);
    }

    /* 平滑过渡类 */
    .transition-all {
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* 缩放动画 */
    @keyframes scaleIn {
      from {
        transform: scale(0.95);
        opacity: 0;
      }
      to {
        transform: scale(1);
        opacity: 1;
      }
    }

    /* 错误消息滑入动画增强 */
    @keyframes slideIn {
      from {
        opacity: 0;
        transform: translateY(-10px) translateX(-10px);
      }
      to {
        opacity: 1;
        transform: translateY(0) translateX(0);
      }
    }

    /* 弹跳效果 */
    @keyframes bounce {
      0%, 20%, 50%, 80%, 100% {
        transform: translateY(0);
      }
      40% {
        transform: translateY(-10px);
      }
      60% {
        transform: translateY(-5px);
      }
    }

    /* 输入框聚焦时的弹跳效果 */
    .form-input:focus {
      animation: bounce 0.5s ease;
    }

    /* 加载动画增强 */
    .loading-spinner {
      display: none;
      width: 20px;
      height: 20px;
      border: 3px solid rgba(255, 255, 255, 0.3);
      border-radius: 50%;
      border-top-color: white;
      animation: spin 1s linear infinite;
      margin: 0 auto;
    }

    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }

    /* 按钮内容容器 */
    .button-content {
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 0.75rem;
      transition: gap 0.3s ease;
    }
    
    /* 响应式设计 - 中等屏幕 (平板竖屏) */
    @media (max-width: 768px) {
      .login-container {
        max-width: 90%;
        margin: 2rem auto;
        padding: 2rem;
      }
      
      .login-title {
        font-size: 2rem;
      }
      
      .form-input {
        font-size: 1rem;
      }
      
      .login-button {
        font-size: 1rem;
        padding: 1rem 1.5rem;
      }
    }

    /* 响应式设计 - 小屏幕 (大屏手机) */
    @media (max-width: 480px) {
      .login-container {
        margin: 1rem;
        padding: 1.75rem;
        border-radius: 15px;
      }

      .login-title {
        font-size: 1.8rem;
      }
      
      .login-subtitle {
        font-size: 0.95rem;
      }

      .form-input {
        padding: 1rem 1rem 1rem 3rem;
        font-size: 0.95rem;
      }
      
      .input-icon {
        font-size: 1rem;
        left: 12px;
      }
      
      .password-toggle {
        right: 12px;
        font-size: 1.1rem;
        padding: 6px;
      }
      
      .login-button {
        font-size: 1rem;
        padding: 1rem 1.5rem;
      }
      
      .error-message {
        font-size: 0.9rem;
        padding: 0.875rem;
        padding-left: 2.25rem;
      }
      
      .input-hint {
        font-size: 0.8rem;
      }
    }
    
    /* 响应式设计 - 极小屏幕 (小屏手机) */
    @media (max-width: 360px) {
      .login-container {
        margin: 0.75rem;
        padding: 1.5rem;
        border-radius: 12px;
      }
      
      .login-header {
        margin-bottom: 1.5rem;
      }
      
      .logo {
        width: 70px;
        height: 70px;
      }
      
      .login-title {
        font-size: 1.6rem;
      }
      
      .form-group {
        margin-bottom: 1.25rem;
      }
      
      .form-input {
        padding: 0.9rem 0.9rem 0.9rem 2.75rem;
        font-size: 0.9rem;
      }
      
      .login-button {
        margin-top: 1.25rem;
        padding: 0.9rem 1.25rem;
      }
      
      .login-footer {
        font-size: 0.8rem;
      }
    }
    
    /* 高对比度和可访问性支持 */
    @media (prefers-contrast: high) {
      .login-container {
        background: white;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
      }
      
      .form-input {
        border: 2px solid #333;
        background: white;
      }
    }
    
    /* 减少动画支持 */
    @media (prefers-reduced-motion: reduce) {
      *,
      *::before,
      *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
      }
      
      .logo {
        animation: none;
      }
      
      body {
        animation: none;
      }
    }
  </style>
</head>
<body style="animation: pageLoad 1s ease-out;">
  <!-- 动态背景容器 -->
  <div class="bg-container"></div>
  <div id="particles-js"></div>
  <div class="login-container">
    <div class="login-header">
      <div class="logo-container">
        <img src="tu/T.png" alt="VIP追剧神器" class="logo">
      </div>
      <h1 class="login-title">VIP追剧神器</h1>
      <p class="login-subtitle">请登录以继续访问</p>
    </div>
    
    <div id="error-message" class="error-message"></div>
    
    <form id="login-form" class="login-form">
      <div class="form-group">
        <label for="username">用户名 (8位数字+英文)</label>
        <div class="input-wrapper">
            <span class="input-icon">👤</span>
            <input type="text" id="username" name="username" class="form-input" placeholder="8位数字+英文组合" required>
          </div>
      </div>
      
      <div class="form-group">
        <label for="password">密码 (数字+大小写字母)</label>
        <div class="input-wrapper">
            <span class="input-icon">🔒</span>
            <input type="password" id="password" name="password" class="form-input" placeholder="包含数字和大小写字母" required>
            <span class="password-toggle" onclick="togglePasswordVisibility()">👁️</span>
          </div>
      </div>
      
      <button type="submit" id="login-button" class="login-button transition-all">
        <div class="button-content">
          <span id="button-text">登录</span>
          <div id="loading-spinner" class="loading-spinner"></div>
        </div>
      </button>
    </form>
    
    <div class="login-footer">
      <p>还没有账号？ <a href="#" id="register-link" style="color: #4a90e2; text-decoration: none; font-weight: bold; transition: color 0.3s ease;">立即注册</a></p>
      © 2025 VIP追剧神器 | 仅供学习使用
    </div>
    
    <!-- 注册模态框 -->
    <div id="register-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.7); z-index: 1000; justify-content: center; align-items: center; animation: fadeIn 0.3s ease;">
      <div class="register-container" style="background: rgba(255, 255, 255, 0.95); border-radius: 20px; padding: 2.5rem; box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2); width: 100%; max-width: 420px; backdrop-filter: blur(15px); animation: slideInUp 0.6s ease-out; position: relative;">
        <button id="close-modal" style="position: absolute; top: 15px; right: 15px; background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #666; transition: color 0.3s ease;">×</button>
        
        <div class="login-header">
          <h1 class="login-title">账号注册</h1>
          <p class="login-subtitle">创建账号以使用VIP追剧神器</p>
        </div>
        
        <div id="register-error-message" class="error-message"></div>
        
        <form id="register-form" class="login-form">
          <div class="form-group">
            <label for="register-username">用户名 (8位数字+英文)</label>
            <div class="input-wrapper">
              <span class="input-icon">👤</span>
              <input type="text" id="register-username" name="username" class="form-input" placeholder="8位数字+英文组合" required>
            </div>
          </div>
          
          <div class="form-group">
            <label for="register-password">密码 (数字+大小写字母)</label>
            <div class="input-wrapper">
              <span class="input-icon">🔒</span>
              <input type="password" id="register-password" name="password" class="form-input" placeholder="包含数字和大小写字母" required>
          <span class="password-toggle" onclick="toggleRegisterPasswordVisibility()">👁️</span>
        </div>
          </div>
          
          <button type="submit" id="register-button" class="login-button transition-all">
            <div class="button-content">
              <span id="register-button-text">注册</span>
              <div id="register-loading-spinner" class="loading-spinner"></div>
            </div>
          </button>
        </form>
      </div>
    </div>
  </div>

  <!-- 粒子效果脚本 -->
  <script>
    // 简单的粒子效果实现
    document.addEventListener('DOMContentLoaded', function() {
      const particlesJS = document.getElementById('particles-js');
      const canvas = document.createElement('canvas');
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      particlesJS.appendChild(canvas);
      
      const ctx = canvas.getContext('2d');
      const particlesArray = [];
      
      // 创建粒子
      function createParticles() {
        for (let i = 0; i < 50; i++) {
          particlesArray.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            size: Math.random() * 3 + 1,
            speedX: Math.random() * 0.5 - 0.25,
            speedY: Math.random() * 0.5 - 0.25,
            opacity: Math.random() * 0.5 + 0.2
          });
        }
      }
      
      // 绘制粒子
      function drawParticles() {
        for (let i = 0; i < particlesArray.length; i++) {
          const particle = particlesArray[i];
          ctx.fillStyle = `rgba(255, 255, 255, ${particle.opacity})`;
          ctx.beginPath();
          ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      
      // 更新粒子位置
      function updateParticles() {
        for (let i = 0; i < particlesArray.length; i++) {
          const particle = particlesArray[i];
          particle.x += particle.speedX;
          particle.y += particle.speedY;
          
          // 边界检测
          if (particle.x < 0 || particle.x > canvas.width) {
            particle.speedX *= -1;
          }
          if (particle.y < 0 || particle.y > canvas.height) {
            particle.speedY *= -1;
          }
        }
      }
      
      // 动画循环
      function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        updateParticles();
        drawParticles();
        requestAnimationFrame(animate);
      }
      
      // 窗口大小调整
      window.addEventListener('resize', function() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
      });
      
      // 初始化
      createParticles();
      animate();
    });
  </script>
  
  <script>
    // 检查URL参数中是否有错误信息
    window.addEventListener('load', function() {
      const urlParams = new URLSearchParams(window.location.search);
      const error = urlParams.get('error');
      if (error) {
        showError(error);
      }
    });

    // 密码显示/隐藏切换
    function togglePasswordVisibility() {
      const passwordInput = document.getElementById('password');
      const passwordToggle = document.querySelector('.password-toggle');
      
      if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        passwordToggle.textContent = '👁️‍🗨️';
      } else {
        passwordInput.type = 'password';
        passwordToggle.textContent = '👁️';
      }
    }
    
    // 注册密码显示/隐藏切换
    function toggleRegisterPasswordVisibility() {
      const passwordInput = document.getElementById('register-password');
      const passwordToggle = passwordInput.parentElement.querySelector('.password-toggle');
      
      if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        passwordToggle.textContent = '👁️‍🗨️';
      } else {
        passwordInput.type = 'password';
        passwordToggle.textContent = '👁️';
      }
    }
    
    // 显示错误消息
    function showError(message) {
      const errorElement = document.getElementById('error-message');
      errorElement.textContent = message;
      errorElement.style.display = 'block';
      
      // 5秒后自动隐藏错误消息
      setTimeout(() => {
        errorElement.style.display = 'none';
      }, 5000);
    }
    
    // 显示注册错误消息
    function showRegisterError(message) {
      const errorElement = document.getElementById('register-error-message');
      errorElement.textContent = message;
      errorElement.style.display = 'block';
      
      // 5秒后自动隐藏错误消息
      setTimeout(() => {
        errorElement.style.display = 'none';
      }, 5000);
    }
    
    // 打开注册模态框
    document.getElementById('register-link').addEventListener('click', function(e) {
      e.preventDefault();
      document.getElementById('register-modal').style.display = 'flex';
      // 隐藏登录错误消息
      document.getElementById('error-message').style.display = 'none';
    });
    
    // 关闭注册模态框
    document.getElementById('close-modal').addEventListener('click', function() {
      document.getElementById('register-modal').style.display = 'none';
      // 清除表单和错误消息
      document.getElementById('register-form').reset();
      document.getElementById('register-error-message').style.display = 'none';
    });
    
    // 点击模态框外部关闭
    document.getElementById('register-modal').addEventListener('click', function(e) {
      if (e.target === this) {
        this.style.display = 'none';
        // 清除表单和错误消息
        document.getElementById('register-form').reset();
        document.getElementById('register-error-message').style.display = 'none';
      }
    });
    
    // 用户名验证函数 - 8位数且必须包含数字和英文（英文不区分大小写）
    function validateUsername(username) {
      // 检查长度是否为8
      if (username.length !== 8) {
        return '用户名必须为8位';
      }
      
      // 检查是否包含数字
      const hasNumber = /\d/.test(username);
      // 检查是否包含英文（不区分大小写）
      const hasLetter = /[a-zA-Z]/.test(username);
      
      if (!hasNumber || !hasLetter) {
        return '用户名必须包含数字和字母';
      }
      
      return ''; // 验证通过
    }
    
    // 密码验证函数 - 至少6位，必须包含数字和字母
    function validatePassword(password) {
      // 检查长度是否至少为6位
      if (password.length < 6) {
        return '密码长度至少为6位';
      }
      
      // 检查是否包含数字
      const hasNumber = /\d/.test(password);
      // 检查是否包含字母
      const hasLetter = /[a-zA-Z]/.test(password);
      
      if (!hasNumber || !hasLetter) {
        return '密码必须包含数字和字母';
      }
      
      return ''; // 验证通过
    }
    
    // 为登录表单添加验证和提交事件
    document.getElementById('login-form').addEventListener('submit', function(e) {
      e.preventDefault();
      
      const username = document.getElementById('username').value;
      const password = document.getElementById('password').value;
      
      // 清除之前的错误消息
      document.getElementById('error-message').style.display = 'none';
      
      // 验证用户名
      const usernameError = validateUsername(username);
      if (usernameError) {
        showError(usernameError);
        return;
      }
      
      // 验证密码
      const passwordError = validatePassword(password);
      if (passwordError) {
        showError(passwordError);
        return;
      }
      
      // 显示加载状态
      const loginButton = document.getElementById('login-button');
      const buttonText = document.getElementById('button-text');
      const loadingSpinner = document.getElementById('loading-spinner');
      
      loginButton.disabled = true;
      buttonText.textContent = '登录中';
      loadingSpinner.style.display = 'block';
      
      // 发送登录请求
      fetch('/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      })
      .then(response => {
        if (!response.ok) {
          // 检查响应是否为JSON
          const contentType = response.headers.get('content-type');
          if (contentType && contentType.includes('application/json')) {
            return response.json().then(data => {
              throw new Error(data.message || '登录失败');
            });
          } else {
            // 如果不是JSON响应，返回文本
            return response.text().then(text => {
              throw new Error(text || '登录失败');
            });
          }
        }
        return response.json();
      })
      .then(data => {
        // 登录成功，跳转到首页
        window.location.href = '/index.html';
      })
      .catch(error => {
        // 显示错误消息
        showError(error.message || '登录失败，请重试');
      })
      .finally(() => {
        // 恢复按钮状态
        loginButton.disabled = false;
        buttonText.textContent = '登录';
        loadingSpinner.style.display = 'none';
      });
    });
    
    // 为注册表单添加验证和提交事件
    document.getElementById('register-form').addEventListener('submit', function(e) {
      e.preventDefault();
      
      const username = document.getElementById('register-username').value;
      const password = document.getElementById('register-password').value;
      
      // 清除之前的错误消息
      document.getElementById('register-error-message').style.display = 'none';
      
      // 验证用户名
      const usernameError = validateUsername(username);
      if (usernameError) {
        showRegisterError(usernameError);
        return;
      }
      
      // 验证密码
      const passwordError = validatePassword(password);
      if (passwordError) {
        showRegisterError(passwordError);
        return;
      }
      
      // 显示加载状态
      const registerButton = document.getElementById('register-button');
      const buttonText = document.getElementById('register-button-text');
      const loadingSpinner = document.getElementById('register-loading-spinner');
      
      registerButton.disabled = true;
      buttonText.textContent = '注册中';
      loadingSpinner.style.display = 'block';
      
      // 发送注册请求
      fetch('/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      })
      .then(response => {
        if (!response.ok) {
          // 检查响应是否为JSON
          const contentType = response.headers.get('content-type');
          if (contentType && contentType.includes('application/json')) {
            return response.json().then(data => {
              throw new Error(data.message || '注册失败');
            });
          } else {
            // 如果不是JSON响应，返回文本
            return response.text().then(text => {
              throw new Error(text || '注册失败');
            });
          }
        }
        return response.json();
      })
      .then(data => {
        // 注册成功，关闭模态框并显示登录成功消息
        document.getElementById('register-modal').style.display = 'none';
        document.getElementById('register-form').reset();
        
        // 显示成功消息
        const successMessage = document.createElement('div');
        successMessage.className = 'error-message';
        successMessage.style.backgroundColor = '#e8f5e9';
        successMessage.style.color = '#2e7d32';
        successMessage.style.borderLeft = '4px solid #2e7d32';
        successMessage.style.display = 'block';
        successMessage.innerHTML = '<span style="margin-right: 0.5rem;">✅</span> 注册成功，请登录';
        
        // 替换错误消息元素
        const errorElement = document.getElementById('error-message');
        errorElement.parentNode.replaceChild(successMessage, errorElement);
        
        // 5秒后恢复错误消息元素
        setTimeout(() => {
          successMessage.parentNode.replaceChild(errorElement, successMessage);
          errorElement.style.display = 'none';
        }, 5000);
      })
      .catch(error => {
        // 显示错误消息
        showRegisterError(error.message || '注册失败，请重试');
      })
      .finally(() => {
        // 恢复按钮状态
        registerButton.disabled = false;
        buttonText.textContent = '注册';
        loadingSpinner.style.display = 'none';
      });
    });
    
    // 为输入框添加焦点事件
    const inputs = document.querySelectorAll('.form-input');
    inputs.forEach(input => {
      input.addEventListener('focus', function() {
        this.parentElement.previousElementSibling.style.color = '#4a90e2';
        this.parentElement.querySelector('.input-icon').style.color = '#4a90e2';
      });
      
      input.addEventListener('blur', function() {
        this.parentElement.previousElementSibling.style.color = '';
        this.parentElement.querySelector('.input-icon').style.color = '';
      });
    });
    
    // 为登录表单添加回车键提交
    document.getElementById('login-form').addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        document.getElementById('login-button').click();
      }
    });
    
    // 为注册表单添加回车键提交
    document.getElementById('register-form').addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        document.getElementById('register-button').click();
      }
    });
    
    // 添加ESC键关闭模态框
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        const registerModal = document.getElementById('register-modal');
        if (registerModal.style.display === 'flex') {
          registerModal.style.display = 'none';
          document.getElementById('register-form').reset();
          document.getElementById('register-error-message').style.display = 'none';
        }
      }
    });
  </script>
</body>
</html>
        """
        
    print("返回嵌入式登录页面")
    return login_html, 200, {'Content-Type': 'text/html'}

@app.route('/<path:filename>.html')
def serve_html_file(filename):
    # 通用HTML文件处理路由
    print(f"尝试提供HTML文件: {filename}.html")
    # 对于index.html，先检查登录状态
    if filename == 'index' and 'user_id' not in session:
        print("访问首页但未登录，重定向到登录页面")
        return redirect('/login.html')
    try:
        # 尝试读取请求的HTML文件
        file_path = f"{filename}.html"
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"成功读取{filename}.html文件")
        return content, 200, {'Content-Type': 'text/html'}
    except Exception as e:
        print(f"读取{filename}.html文件失败: {str(e)}")
        # 返回404页面
        return """
        <html>
        <head><title>404 - 页面未找到</title></head>
        <body>
            <h1>页面未找到</h1>
            <p>抱歉，您请求的页面不存在或无法访问。</p>
            <p><a href="/login.html">返回登录页面</a></p>
        </body>
        </html>
        """, 404, {'Content-Type': 'text/html'}


# 登录接口
@app.route('/login', methods=['POST'])
def login():
    print("接收到登录请求")
    try:
        print("开始处理登录请求...")
        # 获取请求数据
        data = request.get_json()
        print(f"登录请求数据: {data}")
        
        if not data:
            print("调试: 请求数据为空或不是JSON格式")
            return jsonify({'success': False, 'error': '无效的请求数据'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        print(f"调试: 尝试登录的用户名为: {username}")
        print(f"调试: 密码长度: {len(password) if password else 0}字符")
        
        if not username or not password:
            print(f"调试: 登录失败 - 用户名或密码为空 (用户名存在: {bool(username)}, 密码存在: {bool(password)})")
            return jsonify({'success': False, 'error': '用户名和密码不能为空'}), 400
        
        # 哈希密码用于比对
        print("调试: 正在计算密码哈希值...")
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        print(f"调试: 密码哈希值(前10位): {hashed_password[:10]}...")
        
        # 获取数据库连接
        print("调试: 尝试建立数据库连接...")
        connection = get_db_connection()
        print("调试: 数据库连接成功")
        
        try:
            print("调试: 开始执行数据库操作...")
            with connection.cursor() as cursor:
                print(f"调试: 执行SQL查询用户 - SELECT id, username, password FROM users WHERE username = '{username}'")
                cursor.execute("SELECT id, username, password FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
                
                print(f"调试: 查询结果 - 用户是否存在: {user is not None}")
                if user:
                    print(f"调试: 找到用户 - ID: {user['id']}, 用户名: {user['username']}")
                    print(f"调试: 数据库中的密码哈希(前10位): {user['password'][:10]}...")
                    
                    # 检查密码是否匹配
                    print("调试: 正在验证密码...")
                    password_match = (user['password'] == hashed_password)
                    print(f"调试: 密码匹配结果: {password_match}")
                    
                    if password_match:
                        print(f"调试: 登录成功 - 用户: {username} (ID: {user['id']})")
                        # 登录成功，设置会话
                        session['user_id'] = user['id']
                        session['username'] = user['username']
                        # 设置会话永久有效（直到浏览器关闭）
                        session.permanent = True
                        print(f"调试: 会话设置完成 - user_id: {user['id']}, username: {user['username']}")
                        return jsonify({'success': True, 'message': '登录成功', 'username': user['username']})
                    else:
                        print(f"调试: 登录失败 - 密码不匹配 (用户: {username})")
                        return jsonify({'success': False, 'error': '用户名或密码错误'}), 401
                else:
                    print(f"调试: 登录失败 - 用户 '{username}' 不存在")
                    # 如果用户不存在，查询所有用户看有哪些可用
                    print("调试: 查询所有可用用户...")
                    cursor.execute("SELECT username FROM users")
                    all_users = cursor.fetchall()
                    print(f"调试: 数据库中存在的用户列表: {[u['username'] for u in all_users]}")
                    return jsonify({'success': False, 'error': '用户名或密码错误'}), 401
        finally:
            print("调试: 关闭数据库连接")
            connection.close()
            print("调试: 数据库连接已关闭")
            
    except Exception as e:
        print(f"调试: 登录过程中发生异常: {str(e)}")
        import traceback
        print(f"调试: 异常详情:")
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'服务器错误: {str(e)}'}), 500

# 登出接口
@app.route('/logout')
def logout():
    # 清除会话
    session.clear()
    return redirect('/login.html')

# 注册接口
@app.route('/register', methods=['POST'])
def register():
    try:
        print("收到注册请求")
        data = request.get_json()
        if not data:
            print("无效的请求数据：不是JSON格式")
            return jsonify({'success': False, 'error': '无效的请求数据'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        print(f"尝试注册的用户名: {username}")
        
        # 验证输入
        if not username or not password:
            print("用户名或密码为空")
            return jsonify({'success': False, 'error': '用户名和密码不能为空'}), 400
        
        # 验证用户名格式（8位数且包含数字和英文）
        if len(username) != 8:
            print("用户名长度不是8位")
            return jsonify({'success': False, 'error': '用户名必须是8位字符'}), 400
        
        if not any(char.isdigit() for char in username) or not any(char.isalpha() for char in username):
            print("用户名不符合要求：必须包含数字和英文")
            return jsonify({'success': False, 'error': '用户名必须同时包含数字和英文'}), 400
        
        if not all(char.isalnum() for char in username):
            print("用户名包含非法字符：只能包含数字和英文")
            return jsonify({'success': False, 'error': '用户名只能包含数字和英文字母'}), 400
        
        # 验证密码格式（包含数字和大小写字母）
        if not any(char.isdigit() for char in password):
            print("密码不符合要求：必须包含数字")
            return jsonify({'success': False, 'error': '密码必须包含数字'}), 400
        
        if not any(char.islower() for char in password) or not any(char.isupper() for char in password):
            print("密码不符合要求：必须包含大小写字母")
            return jsonify({'success': False, 'error': '密码必须同时包含大小写字母'}), 400
        
        if len(password) < 6:
            print("密码长度不足6位")
            return jsonify({'success': False, 'error': '密码长度不能少于6位'}), 400
        
        # 哈希密码
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        print("密码哈希完成")
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 检查用户名是否已存在
                print("检查用户名是否已存在")
                cursor.execute("SELECT COUNT(*) AS count FROM users WHERE username = %s", (username,))
                result = cursor.fetchone()
                
                if result and result['count'] > 0:
                    print("用户名已存在")
                    return jsonify({'success': False, 'error': '用户名已存在，请选择其他用户名'}), 400
                
                # 插入新用户
                print("插入新用户")
                cursor.execute(
                    "INSERT INTO users (username, password) VALUES (%s, %s)",
                    (username, hashed_password)
                )
                connection.commit()
                print(f"用户 {username} 注册成功")
                
                return jsonify({'success': True, 'message': '注册成功，请登录'})
        finally:
            connection.close()
            
    except Exception as e:
        print(f"注册错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'服务器错误: {str(e)}'}), 500

# @app.route('/platform/<platform>')
# def platform(platform):
#     # 获取视频平台URL
#     url = video_service.get_platform_url(platform)
#     return jsonify({'url': url})

# @app.route('/play', methods=['POST'])
# def play():
#     # 生成VIP视频播放地址
#     if request.json is None:
#         return jsonify({'error': 'Invalid JSON data'}), 400
#     
#     video_url = request.json.get('video_url', '')
#     result = video_service.get_play_url(video_url)
#     
#     # 检查result是否为字典
#     if isinstance(result, dict):
#         # 返回完整的结果字典
#         return jsonify(result)
#     else:
#         # 向后兼容：如果结果不是字典，则按旧格式返回
#         return jsonify({'play_url': result})

# @app.route('/tvplay', methods=['POST'])
# def tvplay():
#     # 通过B站TV版接口获取VIP和付费视频播放地址
#     if request.json is None:
#         return jsonify({'error': 'Invalid JSON data'}), 400
#     
#     # 获取请求参数
#     avid = request.json.get('avid', '')
#     cid = request.json.get('cid', '')
#     quality = request.json.get('quality', 116)  # 默认1080P高码率
#     sessdata = request.json.get('sessdata', '')  # 可选的SESSDATA参数
#     
#     # 验证必要参数
#     if not avid or not cid:
#         return jsonify({'error': 'Missing required parameters: avid and cid'}), 400
#     
#     # 如果提供了SESSDATA，则设置它
#     if sessdata:
#         video_service.set_sessdata(sessdata)
#     
#     # 调用TV版解析服务获取播放地址
#     result = video_service.get_tv_play_url(avid, cid, quality)
#     
#     # 根据结果返回响应
#     if result.get('success'):
#         return jsonify({
#             'success': True,
#             'play_url': result.get('play_url'),
#             'quality': result.get('quality')
#         })
#     else:
#         return jsonify({
#             'success': False,
#             'error': result.get('error', 'Unknown error')
#         }), 400

# @app.route('/group')
# def group():
#     # 获取企鹅群链接
#     url = video_service.get_group_url()
#     return jsonify({'url': url})

# @app.route('/decrypt', methods=['POST'])
# def decrypt():
#     """
#     AES解密接口
#     """
#     try:
#         if request.json is None:
#             return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
#         
#         # 获取解密参数
#         encrypted_data = request.json.get('data', '')
#         key = request.json.get('key', '')
#         iv = request.json.get('iv', None)
#         mode = request.json.get('mode', 'CBC')
#         
#         # 验证必要参数
#         if not encrypted_data or not key:
#             return jsonify({'success': False, 'error': 'Missing required parameters: data and key'}), 400
#         
#         # 执行解密
#         try:
#             decrypted_data = video_service.decrypt_aes(encrypted_data, key, iv, mode)
#             # 将解密结果转换为base64以便在JSON中传输
#             decrypted_b64 = base64.b64encode(decrypted_data).decode('utf-8')
#             
#             return jsonify({
#                 'success': True,
#                 'decrypted_data': decrypted_b64,
#                 'message': '解密成功'
#             })
#         except Exception as e:
#             return jsonify({
#                 'success': False,
#                 'error': f'解密失败: {str(e)}'
#             }), 400
#     except Exception as e:
#         return jsonify({
#             'success': False,
#             'error': f'服务器错误: {str(e)}'
#         }), 500

# @app.route('/check_ffmpeg')
# def check_ffmpeg():
#     """
#     检查FFmpeg是否安装
#     """
#     try:
#         is_installed = video_service.check_ffmpeg_installed()
#         return jsonify({
#             'success': True,
#             'ffmpeg_installed': is_installed,
#             'message': 'FFmpeg已安装' if is_installed else 'FFmpeg未安装，请安装后重试'
#         })
#     except Exception as e:
#         return jsonify({
#             'success': False,
#             'error': f'检查FFmpeg状态失败: {str(e)}'
#         }), 500

# @app.route('/convert_video', methods=['POST'])
# def convert_video():
#     """
#     视频格式转换接口
#     """
#     try:
#         if request.json is None:
#             return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
#         
#         # 获取转换参数
#         input_file = request.json.get('input_file', '')
#         output_file = request.json.get('output_file', '')
#         codec = request.json.get('codec', 'copy')
#         
#         # 验证必要参数
#         if not input_file or not output_file:
#             return jsonify({'success': False, 'error': 'Missing required parameters: input_file and output_file'}), 400
#         
#         # 执行转换
#         result = video_service.convert_video_format(input_file, output_file, codec)
#         
#         if result.get('success'):
#             return jsonify(result)
#         else:
#             return jsonify(result), 400
#     except Exception as e:
#         return jsonify({
#             'success': False,
#             'error': f'服务器错误: {str(e)}'
#         }), 500

# @app.route('/set_bilibili_cookies', methods=['POST'])
# def set_bilibili_cookies():
#     """
#     设置B站Cookie
#     """
#     try:
#         if request.json is None:
#             return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
#         
#         cookies = request.json.get('cookies', '')
#         
#         if not cookies:
#             return jsonify({'success': False, 'error': 'Missing required parameter: cookies'}), 400
#         
#         # 设置Cookie
#         result = video_service.set_bilibili_cookies(cookies)
#         
#         if result:
#             return jsonify({
#                 'success': True,
#                 'message': 'B站Cookie设置成功'
#             })
#         else:
#             return jsonify({
#                 'success': False,
#                 'error': 'B站Cookie设置失败'
#             }), 400
#     except Exception as e:
#         return jsonify({
#             'success': False,
#             'error': f'服务器错误: {str(e)}'
#         }), 500

# @app.route('/get_video_info', methods=['POST'])
# def get_video_info():
#     """
#     使用bilibili-api获取视频详细信息
#     """
#     try:
#         if request.json is None:
#             return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
#         
#         bvid = request.json.get('bvid', '')
#         aid = request.json.get('aid', '')
#         
#         # 验证必要参数
#         if not bvid and not aid:
#             return jsonify({'success': False, 'error': 'Missing required parameter: bvid or aid'}), 400
#         
#         # 获取视频信息
#         result = video_service.get_video_info_with_api(bvid=bvid, aid=aid)
#         
#         return jsonify(result)
#     except Exception as e:
#         return jsonify({
#             'success': False,
#             'error': f'服务器错误: {str(e)}'
#         }), 500

# @app.route('/check_api_status')
# def check_api_status():
#     """
#     检查API状态
#     """
#     try:
#         result = video_service.check_api_status()
#         return jsonify(result)
#     except Exception as e:
#         return jsonify({
#             'success': False,
#             'error': f'检查API状态失败: {str(e)}'
#         }), 500

# 注释掉依赖缺失模块的路由函数
'''
@app.route('/excel_analysis')
def excel_analysis_page():
    # 提供Excel分析工具页面
    try:
        with open('excel_analysis.html', 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f'Error loading Excel analysis page: {str(e)}', 500

@app.route('/analyze_excel', methods=['POST'])
def analyze_excel():
    # 处理Excel文件上传和分析
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '请选择要上传的文件'})
        
        file = request.files['file']
        
        # 检查文件是否为空
        if file.filename == '':
            return jsonify({'success': False, 'error': '请选择有效的文件'})
        
        # 读取文件内容
        file_content = file.read()
        
        # 加载并分析文件
        load_result = excel_analyzer.load_file(file_content, file.filename)
        
        if not load_result['success']:
            return jsonify({'success': False, 'error': load_result['error']})
        
        df = load_result['data']
        info = load_result['info']
        
        # 执行数据分析
        analysis_result = excel_analyzer.analyze_data(df)
        
        if not analysis_result['success']:
            return jsonify({'success': False, 'error': analysis_result['error']})
        
        analysis = analysis_result['analysis']
        
        # 生成可视化
        viz_result = excel_analyzer.generate_visualizations(df, analysis)
        
        if not viz_result['success']:
            return jsonify({'success': False, 'error': viz_result['error']})
        
        visualizations = viz_result['visualizations']
        
        # 获取推荐建议
        recommendations = excel_analyzer.get_recommendations(analysis)
        
        # 返回完整结果
        return jsonify({
            'success': True,
            'info': info,
            'analysis': analysis,
            'visualizations': visualizations,
            'recommendations': recommendations
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'分析过程中出现错误: {str(e)}'})
'''

@app.route('/pdf_to_html')
@login_required
def pdf_to_html_page():
    # 提供PDF转HTML工具页面
    try:
        with open('pdf_to_html.html', 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f'Error loading PDF to HTML page: {str(e)}', 500


@app.route('/convert_pdf_to_html', methods=['POST'])
@login_required
def convert_pdf_to_html():
    # 处理PDF文件上传和转换
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '请选择要上传的PDF文件'})
        
        file = request.files['file']
        
        # 检查文件是否为空
        if file.filename == '':
            return jsonify({'success': False, 'error': '请选择有效的PDF文件'})
        
        # 检查文件类型
        if file.filename and not file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': '请上传PDF格式的文件'})
        
        # 创建临时目录和文件
        with tempfile.TemporaryDirectory() as temp_dir:
            if not file.filename:
                return jsonify({'success': False, 'error': '文件名无效'})
            temp_pdf_path = Path(temp_dir) / file.filename
            temp_html_path = Path(temp_dir) / f"{Path(file.filename).stem}.html"
            
            # 保存上传的PDF文件
            file.save(temp_pdf_path)
            
            # 执行PDF转HTML转换
            try:
                # 注释掉缺失的函数调用
                # pdf_to_html(str(temp_pdf_path), str(temp_html_path))
                
                # 读取生成的HTML内容
                with open(temp_html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # 返回转换结果
                return jsonify({
                    'success': True,
                    'filename': f"{Path(file.filename).stem}.html",
                    'html_content': html_content,
                    'message': 'PDF转HTML转换成功！'
                })
                
            except Exception as e:
                return jsonify({'success': False, 'error': f'PDF转HTML转换失败: {str(e)}'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'处理过程中出现错误: {str(e)}'})

'''@app.route('/document_converter')
def document_converter_page():
    # 提供文档转换工具页面
    try:
        file_path = os.path.join(current_dir, 'document_converter.html')
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f'Error loading document converter page: {str(e)}', 500

@app.route('/convert_document', methods=['POST'])
def convert_document():
    # 处理文档转换请求
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '请选择要上传的文件'})
        
        file = request.files['file']
        
        # 检查文件是否为空
        if file.filename == '':
            return jsonify({'success': False, 'error': '请选择有效的文件'})
        
        # 获取目标格式
        target_format = request.form.get('format')
        if not target_format:
            return jsonify({'success': False, 'error': '请选择目标格式'})
        
        # 检查目标格式是否支持
        supported_formats = ['.pdf', '.docx', '.xlsx', '.pptx']
        if target_format not in supported_formats:
            return jsonify({'success': False, 'error': f'不支持的目标格式: {target_format}'})
        
        # 创建临时目录和文件
        with tempfile.TemporaryDirectory() as temp_dir:
            if not file.filename:
                return jsonify({'success': False, 'error': '文件名无效'})
            temp_input_path = Path(temp_dir) / file.filename
            
            # 保存上传的文件
            file.save(temp_input_path)
            
            # 执行文档转换
            try:
                success, output_path, message = document_converter.convert_document(
                    str(temp_input_path), target_format
                )
                
                if not success:
                    return jsonify({'success': False, 'error': message})
                
                # 读取转换后的文件
                if output_path is None:
                    return jsonify({'success': False, 'error': '转换失败，输出路径为空'})
                
                with open(output_path, 'rb') as f:
                    converted_file_data = f.read()
                
                # 返回转换结果
                return jsonify({
                    'success': True,
                    'message': message,
                    'filename': os.path.basename(output_path) if output_path else 'converted_file',
                    'file_data': converted_file_data.decode('latin1')  # 使用latin1编码避免二进制问题
                })
                
            except Exception as e:
                return jsonify({'success': False, 'error': f'文档转换失败: {str(e)}'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'处理过程中出现错误: {str(e)}'})
'''

# 处理静态文件请求 - 排除login.html不需要验证
@app.route('/<path:filename>')
def serve_file(filename):
    # 允许直接访问CSS、JS和图片文件
    if filename.endswith('.css') or filename.endswith('.js') or \
       filename.endswith('.png') or filename.endswith('.jpg') or filename.endswith('.jpeg') or filename.endswith('.gif'):
        return send_from_directory('.', filename)
    # 其他文件需要登录才能访问
    if 'user_id' not in session:
        return redirect('/login.html')
    return send_from_directory('.', filename)

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': '接口不存在'}), 404

@app.route('/proxy_video', methods=['GET', 'OPTIONS'])
@login_required
def proxy_video():
    """
    视频代理路由，用于解决net::ERR_BLOCKED_BY_ORB错误
    通过服务器转发视频请求，避免浏览器直接访问B站视频服务器
    """
    try:
        # 处理预检请求
        if request.method == 'OPTIONS':
            return Response(
                '',
                headers={
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS',
                    'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, Range',
                    'Access-Control-Max-Age': '86400',
                    'Access-Control-Expose-Headers': 'Content-Length, Content-Range, Accept-Ranges'
                }
            )
        
        # 获取目标视频URL
        target_url = request.args.get('url', '')
        if not target_url:
            return jsonify({'success': False, 'error': '缺少目标URL参数'}), 400
        
        # 验证URL是否为B站视频地址
        if 'bilibili.com' not in target_url and 'bilivideo.com' not in target_url:
            return jsonify({'success': False, 'error': '只支持代理B站视频地址'}), 400
        
        logging.info(f"代理请求: {target_url[:200]}..." if len(target_url) > 200 else f"代理请求: {target_url}")
        
        # 创建请求头，添加更多浏览器头信息模拟真实请求
        headers = {
            'User-Agent': request.headers.get('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'),
            'Accept': 'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'identity',  # 不使用压缩，避免解压问题
            'Connection': 'keep-alive',
            'Referer': 'https://www.bilibili.com/',
            'Origin': 'https://www.bilibili.com',
            'DNT': '1',
            'Sec-Fetch-Dest': 'video',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'cross-site'
        }
        
        # 特别处理Range请求头，这对视频播放至关重要
        range_header = request.headers.get('Range')
        if range_header:
            headers['Range'] = range_header
            logging.info(f"处理Range请求: {range_header}")
        
        # 配置请求会话以获得更好的连接复用
        session = requests.Session()
        session.headers.update(headers)
        
        # 流式请求原始视频，增加连接超时和读取超时
        try:
            response = session.get(target_url, stream=True, timeout=(10, 60), allow_redirects=True)
            
            # 获取响应状态码和头信息
            status_code = response.status_code
            response_headers_dict = dict(response.headers)
            
            logging.info(f"代理响应状态码: {status_code}")
            
            # 允许200(完整内容)和206(部分内容)状态码
            if status_code not in [200, 206]:
                logging.error(f"代理请求失败，状态码: {status_code}, 响应头: {response_headers_dict}")
                return jsonify({'success': False, 'error': f'Failed to fetch video, status code: {status_code}'}), status_code
            
            # 构建返回给客户端的响应头
            response_headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, Range',
                'Access-Control-Expose-Headers': 'Content-Length, Content-Range, Accept-Ranges',
                'Accept-Ranges': 'bytes',
            }
            
            # 复制必要的响应头
            for header in ['Content-Type', 'Content-Length', 'Content-Range', 'Last-Modified', 'ETag']:
                if header in response_headers_dict:
                    response_headers[header] = response_headers_dict[header]
            
            # 确保内容类型设置正确
            if 'Content-Type' not in response_headers:
                response_headers['Content-Type'] = 'video/mp4'
            
            # 创建流式响应生成器
            def generate():
                try:
                    # 使用更大的chunk_size提高传输效率
                    for chunk in response.iter_content(chunk_size=32768):
                        if chunk:
                            yield chunk
                except Exception as e:
                    logging.error(f"流式传输异常: {str(e)}")
            
            # 返回流式响应
            return Response(
                generate(),
                status=status_code,
                headers=response_headers,
                mimetype=response_headers.get('Content-Type', 'video/mp4')
            )
        except requests.exceptions.ConnectionError:
            logging.error("代理请求连接错误")
            return jsonify({'success': False, 'error': 'Connection error, please try again later'}), 502
        except requests.exceptions.Timeout:
            logging.error("代理请求超时")
            return jsonify({'success': False, 'error': 'Request timeout, please try again later'}), 504
    
    except requests.exceptions.RequestException as e:
        logging.error(f"代理请求失败: {str(e)}")
        return jsonify({'success': False, 'error': f'代理请求失败: {str(e)}'}), 502
    except Exception as e:
        logging.error(f"代理处理异常: {str(e)}")
        return jsonify({'success': False, 'error': f'代理处理异常: {str(e)}'}), 500

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500

if __name__ == '__main__':
    # 确保用户表存在
    try:
        ensure_user_table_exists()
    except Exception as e:
        print(f"数据库初始化警告: {str(e)}")
        # 继续启动应用，但记录警告
    
    # 检查是否存在index.html文件，如果不存在则创建一个简单版本
    if not os.path.exists('index.html'):
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write('''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VIP追剧神器 - 加载中...</title>
    <style>
        body {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f0f0f0;
            font-family: Arial, sans-serif;
        }
        .loading {
            text-align: center;
            color: #333;
        }
    </style>
</head>
<body>
    <div class="loading">
        <h2>正在准备VIP追剧神器...</h2>
        <p>请运行程序，然后刷新此页面</p>
    </div>
</body>
</html>''')
    
    # 如果1.html是主页，确保它存在并包含Excel分析工具的链接
    if os.path.exists('1.html'):
        try:
            with open('1.html', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否已经包含Excel分析工具的链接
            if 'Excel智能分析工具' not in content:
                # 在链接列表中添加Excel分析工具链接
                updated_content = content.replace(
                    '<a href="5.html" class="home-subtitle" target="blank" style="color: #bc267d; text-decoration: none;">点击进入：文档转换工具</a><br>',
                    '<a href="5.html" class="home-subtitle" target="blank" style="color: #bc267d; text-decoration: none;">点击进入：文档转换工具</a><br>\n   <br>\n   <br>\n   <a href="excel_analysis.html" class="home-subtitle" target="blank" style="color: #bc267d; text-decoration: none;">点击进入：Excel智能分析工具</a><br>'
                )
                with open('1.html', 'w', encoding='utf-8') as f:
                    f.write(updated_content)
        except Exception as e:
            print(f"Warning: Could not update 1.html: {e}")
    
    # 生产环境启动
    # 确保用户表存在并创建默认管理员
    ensure_user_table_exists()
    
    # 生产环境中不需要直接运行，由WSGI服务器加载
    # 以下代码仅在直接运行main.py时执行
    if __name__ == '__main__':
        print("视频播放服务已启动，访问 http://localhost:5000/login.html 登录")
        print("默认管理员账户：admin / admin123")
        print("按 Ctrl+C 可以停止服务")
        # 注意：生产环境应使用WSGI服务器如gunicorn或uwsgi
        # 此处为了演示，仍使用Flask内置服务器
        app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
