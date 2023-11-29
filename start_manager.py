# 添加当前路径至解释器，确保单元测试时可正常import其它文件
import os
import sys

current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
# 基于顶层包的import
from prototype.remore_manager import Manager

# 系统库
import argparse

def main():
    parser = argparse.ArgumentParser(
        prog="manager",  # 程序名
        description="manager of the RF-Crowdsourcing nodes",  # 描述
    )
    # 【端口号】
    parser.add_argument("-p", "--port", default="7777", type=int)

    # 解析参数
    args = parser.parse_args()
    port = args.port

    # 启动管理器
    manager = Manager(port)
    manager.run()
    print(f"Manager started at port {port}")

if __name__ == '__main__':
    main()