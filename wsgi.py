# WSGI入口点文件，用于在生产环境中部署Flask应用
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 从主应用文件中导入Flask应用实例
from main import app as application

# 应用实例的别名必须为application，这是大多数WSGI服务器的默认期望
if __name__ == "__main__":
    # 仅用于测试，生产环境中由WSGI服务器负责调用
    application.run()