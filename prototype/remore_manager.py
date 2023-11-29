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
from prototype.utils.config import Config
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
        # 其它参数
        self.config = Config()
        self.port = port

        # 所有节点
        self.requester = None
        self.randomizers = None
        self.submitters = None

        # 从配置文件读取参数
        self.ipfs_url = self.config.get_config("app").get("ipfs_url")
        self.web3_url = self.config.get_config("app").get("web3_url")

        # 【Client】参数
        self.CLIENT_PORT = self.config.get_config("client").get("serving_port")

        # 【Requester】参数
        self.REQUESTER_TASK_PULL_PORT = self.config.get_config("requester").get(
            "task_pull_port"
        )
        self.REUQESTER_SERVING_PORT = self.config.get_config("requester").get(
            "serving_port"
        )

        # 【Randomizer】参数
        self.RANDOMIZER_PROVING_SERVER_PORT_BASE = self.config.get_config(
            "randomizer"
        ).get("proving_server_port_base")
        self.RANDOMIZER_SERVING_PORT_BASE = self.config.get_config("randomizer").get(
            "serving_port_base"
        )

        # 【Submitter】参数
        self.SUBMITTER_SERVING_PORT_BASE = self.config.get_config("submitter").get(
            "serving_port_base"
        )

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
            self.task = CIFAR10Task("CIFAR10 tagging", paras["total_submitter_num"])
        self.requester = Requester(
            self.CLIENT_PORT,
            paras["client_ip"],
            self.REUQESTER_SERVING_PORT,
            self.ipfs_url,
            self.web3_url,
            paras["contract_address"],
            paras["contract_abi"],
            paras["bc_account"],
            paras["bc_private_key"],
            "tmp/keypairs/pk.pkl",
            "tmp/keypairs/sk.pkl",
            paras["randomizer_list"],
            self.task,
            self.REQUESTER_TASK_PULL_PORT,
        )
        self.requester.run()

    def __start_randomizers(self, paras):
        # ------------------
        # 初始化 randomizer
        # ------------------

        for id in paras["ids"]:
            self.randomizers.append(
                Randomizer(
                    self.CLIENT_PORT,
                    paras["client_ip"],
                    self.RANDOMIZER_SERVING_PORT_BASE + id,
                    self.ipfs_url,
                    self.web3_url,
                    paras["contract_address"],
                    paras["contract_abi"],
                    paras["bc_account"],
                    paras["bc_private_key"],
                    "tmp/keypairs/pk.pkl",
                    self.RANDOMIZER_PROVING_SERVER_PORT_BASE + id,
                    id,
                )
            )
        for randomizer in self.randomizers:
            randomizer.run()

    def __start_submitters(self, paras):
        for id in paras["ids"]:
            self.submitters.append(
                Submitter(
                    self.CLIENT_PORT,
                    paras["client_ip"],
                    self.SUBMITTER_SERVING_PORT_BASE + id,
                    self.ipfs_url,
                    self.web3_url,
                    paras["contract_address"],
                    paras["contract_abi"],
                    paras["bc_account"],
                    paras["bc_private_key"],
                    "tmp/keypairs/pk.pkl",
                    self.REQUESTER_IP,
                    self.REQUESTER_TASK_PULL_PORT,
                    self.task.SUBTASK_CLS,
                    id,
                )
            )


if __name__ == "__main__":
    from prototype.utils.network import listen_on_port, connect_to, sendLine, recvLine
    import time

    server = MyServer(50000)
    server.run()

    # 合约部署
    from prototype.utils.tools import deploy_smart_contract
    provider_url = "http://127.0.0.1:8545"
    account = "0x9A82f98d6083c30632A22a9e93a9dfA8B054C929"
    private_key = "0x11408f483264dcc0b831b0b95ffbfddc19d9a3ae98fc289baa5592d5b1e1d331"
    contract_address, contract_abi = deploy_smart_contract(
        "CrowdsourcingContract", provider_url, account, private_key, 10, 2
    )

    paras = {
        "task_name" : "CIFAR10Task",
        "total_submitter_num": 10,
        "client_ip": "localhost",
        "contract_address": contract_address,
        "contract_abi": contract_abi,
        "bc_account": account,
        "bc_private_key": private_key,
        "randomizer_list": []
    }

    def handler(conn):
        sendLine(conn, "start/REQUESTER")
        sendLine(conn, paras)


    connect_to(handler, 50000)

    # TODO：思考完整流程是否有缺陷
    # 1.使用ssh等方法在服务器上启动管理器进程
    # 2.使用system_interface类与各管理器进程交互，自动搭建实验环境
    # 目的：overall 系统性能评估

    # TODO：修改客户端，实现调用该服务器方便测试
    # TODO：实现多进程启动节点（先查出是什么原因导致无法启动多进程）
