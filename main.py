# -*- coding: utf-8 -*-
"""
搜韵网收录诗文出处循证系统 - 标准主入口 (main.py)
--------------------------------------------------
支持直接双击运行或命令行运行：
    python main.py
"""
import sys
import os

# 锁定项目根目录与 src 目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT_DIR, 'src')

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

if __name__ == '__main__':
    # 动态载入并启动核心服务
    from src.server import main
    main()
