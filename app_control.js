// app_control.js - 应用程序控制脚本

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', function() {
    // 初始化背景图片轮播效果
    initBackgroundSlideshow();
    
    // 初始化按钮交互效果
    initButtonEffects();
    
    // 初始化移动端适配
    initMobileAdaptation();
});

// 背景图片轮播效果
function initBackgroundSlideshow() {
    const images = document.querySelectorAll('.bg');
    if (images.length === 0) return;
    
    let currentIndex = 0;
    const intervalTime = 5000; // 每张图片显示5秒
    
    // 初始化第一张图片
    images[currentIndex].classList.add('active');
    
    // 轮播函数
    function startSlideshow() {
        setInterval(() => {
            // 移除当前图片的active类
            images[currentIndex].classList.remove('active');
            
            // 更新索引
            currentIndex = (currentIndex + 1) % images.length;
            
            // 添加新图片的active类
            images[currentIndex].classList.add('active');
        }, intervalTime);
    }
    
    startSlideshow();
}

// 按钮交互效果
function initButtonEffects() {
    // 为所有按钮添加悬停效果
    const buttons = document.querySelectorAll('button, .btn');
    buttons.forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            this.style.opacity = '0.9';
        });
        
        btn.addEventListener('mouseleave', function() {
            this.style.opacity = '1';
        });
        
        // 移动端触摸效果
        btn.addEventListener('touchstart', function() {
            this.style.opacity = '0.9';
        });
        
        btn.addEventListener('touchend', function() {
            this.style.opacity = '1';
        });
        
        btn.addEventListener('touchcancel', function() {
            this.style.opacity = '1';
        });
    });
}

// 移动端适配
function initMobileAdaptation() {
    // 移动端屏幕旋转检测
    window.addEventListener('orientationchange', function() {
        // 延迟执行以确保屏幕尺寸已更新
        setTimeout(() => {
            // 更新背景图片尺寸
            const images = document.querySelectorAll('.bg');
            images.forEach(img => {
                img.style.backgroundSize = 'cover';
            });
        }, 300);
    });
    
    // 修复iOS上的视口问题
    if (navigator.userAgent.match(/iPhone|iPad|iPod/i)) {
        window.addEventListener('scroll', function() {
            // 防止iOS上的视口缩放问题
            document.body.style.position = 'fixed';
            setTimeout(() => {
                document.body.style.position = '';
            }, 10);
        });
    }
    
    // 窗口大小调整事件
    window.addEventListener('resize', function() {
        // 更新背景图片尺寸
        const images = document.querySelectorAll('.bg');
        images.forEach(img => {
            img.style.backgroundSize = 'cover';
        });
    });
}

// 简单的工具函数
function showMessage(message, type = 'info') {
    // 创建消息元素
    const messageEl = document.createElement('div');
    messageEl.className = `message ${type}`;
    messageEl.textContent = message;
    
    // 添加样式
    messageEl.style.position = 'fixed';
    messageEl.style.top = '20px';
    messageEl.style.left = '50%';
    messageEl.style.transform = 'translateX(-50%)';
    messageEl.style.padding = '12px 24px';
    messageEl.style.borderRadius = '4px';
    messageEl.style.color = 'white';
    messageEl.style.zIndex = '9999';
    messageEl.style.opacity = '0';
    messageEl.style.transition = 'opacity 0.3s';
    
    // 根据类型设置背景色
    if (type === 'success') {
        messageEl.style.backgroundColor = 'rgba(46, 204, 113, 0.9)';
    } else if (type === 'error') {
        messageEl.style.backgroundColor = 'rgba(231, 76, 60, 0.9)';
    } else {
        messageEl.style.backgroundColor = 'rgba(52, 152, 219, 0.9)';
    }
    
    // 添加到页面
    document.body.appendChild(messageEl);
    
    // 显示消息
    setTimeout(() => {
        messageEl.style.opacity = '1';
    }, 10);
    
    // 3秒后隐藏消息
    setTimeout(() => {
        messageEl.style.opacity = '0';
        setTimeout(() => {
            document.body.removeChild(messageEl);
        }, 300);
    }, 3000);
}

// 简单的表单验证函数
function validateForm(form) {
    const inputs = form.querySelectorAll('input[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.style.borderColor = '#e74c3c';
            
            // 添加错误提示
            let errorEl = input.nextElementSibling;
            if (!errorEl || !errorEl.classList.contains('error-message')) {
                errorEl = document.createElement('div');
                errorEl.className = 'error-message';
                errorEl.style.color = '#e74c3c';
                errorEl.style.fontSize = '12px';
                errorEl.style.marginTop = '4px';
                input.parentNode.appendChild(errorEl);
            }
            errorEl.textContent = '此字段不能为空';
            
            // 输入时清除错误状态
            input.addEventListener('input', function() {
                if (this.value.trim()) {
                    this.style.borderColor = '';
                    const error = this.nextElementSibling;
                    if (error && error.classList.contains('error-message')) {
                        error.textContent = '';
                    }
                }
            });
        }
    });
    
    return isValid;
}

// 简单的AJAX请求函数
function ajaxRequest(url, options = {}) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        
        xhr.open(options.method || 'GET', url);
        
        // 设置默认请求头
        if (options.method && options.method.toUpperCase() === 'POST') {
            xhr.setRequestHeader('Content-Type', 'application/json');
        }
        
        // 设置自定义请求头
        if (options.headers) {
            Object.keys(options.headers).forEach(header => {
                xhr.setRequestHeader(header, options.headers[header]);
            });
        }
        
        xhr.onload = function() {
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    resolve(JSON.parse(xhr.responseText));
                } catch (e) {
                    resolve(xhr.responseText);
                }
            } else {
                reject(new Error(`请求失败: ${xhr.status} ${xhr.statusText}`));
            }
        };
        
        xhr.onerror = function() {
            reject(new Error('网络错误'));
        };
        
        // 发送请求数据
        if (options.data) {
            xhr.send(JSON.stringify(options.data));
        } else {
            xhr.send();
        }
    });
}

// 将函数绑定到window对象上，以便在页面中直接使用
window.showMessage = showMessage;
window.validateForm = validateForm;
window.ajaxRequest = ajaxRequest;
