# 添加当前路径至解释器，确保单元测试时可正常import其它文件
import os
import sys

current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 基于顶层包的import
from prototype.nodes.requester import Requester
from prototype.nodes.submitter import Submitter
from prototype.nodes.randomizer import Randomizer
from prototype.utils import log
from prototype.utils.tools import deploy_smart_contract
from prototype.utils.network import listen_on_port, connect_to, sendLine, recvLine
from prototype.task.cifar10_tagging import CIFAR10Task

# 系统库
import time
import json
import random
import threading


# TODO: 启动一个服务器 接收客户端的请求 并启停对应的节点 用于远程部署
# 功能：接收（节点类型、节点参数列表）

# TODO: 实现使用ssh自动进行远程部署


class Manager:
    def __init__(self, port):
        self.port = port

        # 所有节点
        self.requester = None
        self.randomizers = []
        self.submitters = []

    def run(self):
        # 1.启动用于接收客户端请求的服务端
        self.__server_start()

    def __server_start(self):
        def server(conn, addr):
            instruction = recvLine(conn)
            paras = recvLine(conn)
            if instruction == "start/REQUESTER":
                self.__start_requester(paras)
            elif instruction == "start/RANDOMIZERS":
                self.__start_randomizers(paras)
            elif instruction == "start/SUBMITTERS":
                self.__start_submitters(paras)
            # TODO：需要根据实际情况返回
            sendLine(conn, "success")
            conn.close()

        # 启动服务器
        threading.Thread(
            target=listen_on_port,
            args=(server, self.port),
        ).start()

    def __start_requester(self, paras):
        # ------------------
        # 初始化 requester
        # ------------------
        if paras["task_name"] == "CIFAR10Task":
            self.task = CIFAR10Task("CIFAR10 tagging", paras["subtask_num"])
        self.requester = Requester(
            paras["CLIENT_PORT"],
            paras["client_ip"],
            paras["REUQESTER_SERVING_PORT"],
            paras["ipfs_url"],
            paras["web3_url"],
            paras["contract_address"],
            paras["contract_abi"],
            paras["bc_account"],
            paras["bc_private_key"],
            paras["requester_pk_str"],
            paras["requester_sk_str"],
            paras["randomizer_list"],
            self.task,
            paras["REQUESTER_TASK_PULL_PORT"],
        )
        self.requester.start()

    def __start_randomizers(self, paras_list):
        # ------------------
        # 初始化 randomizer
        # ------------------
        randomizers_batch = []
        for paras in paras_list:
            randomizers_batch.append(
                Randomizer(
                    paras["CLIENT_PORT"],
                    paras["client_ip"],
                    paras["serving_port"],
                    paras["ipfs_url"],
                    paras["web3_url"],
                    paras["contract_address"],
                    paras["contract_abi"],
                    paras["bc_account"],
                    paras["bc_private_key"],
                    paras["requester_pk_str"],
                    paras["PROVING_SERVER_PORT"],
                    paras["id"],
                )
            )
        for randomizer in randomizers_batch:
            randomizer.start()
        self.randomizers += randomizers_batch

    def __start_submitters(self, paras_list):
        if paras_list[0]["task_name"] == "CIFAR10Task":
            task = CIFAR10Task
        submitters_batch = []
        for paras in paras_list:
            submitters_batch.append(
                Submitter(
                    paras["CLIENT_PORT"],
                    paras["client_ip"],
                    paras["serving_port"],
                    paras["ipfs_url"],
                    paras["web3_url"],
                    paras["contract_address"],
                    paras["contract_abi"],
                    paras["bc_account"],
                    paras["bc_private_key"],
                    paras["requester_pk_str"],
                    paras["REQUESTER_IP"],
                    paras["REQUESTER_TASK_PULL_PORT"],
                    task.SUBTASK_CLS(),
                    paras["id"],
                )
            )
        for submitter in submitters_batch:
            submitter.start()
        self.submitters += submitters_batch


if __name__ == "__main__":
    manager = Manager(7777)
    manager.run()

    # TODO：思考完整流程是否有缺陷
    # 1.使用ssh等方法在服务器上启动管理器进程
    # 2.使用system_interface类与各管理器进程交互，自动搭建实验环境
    # 目的：overall 系统性能评估

    # TODO：实现多进程启动节点（先查出是什么原因导致无法启动多进程）
