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

# 系统库
import time
import json
import random
import threading
from prototype.utils.config import Config

# TODO：实现自动远程部署（本地测试使用命令行开启新的进程实现）
class SystemInterface:
    def __init__(
        self,
        task,
        server_callback,
        submitter_num,
        randomizer_num,
        subtask_num,
        re_enc_num,
    ):
        # 其它参数
        self.task = task
        self.server_callback = server_callback
        self.SUBMITTER_NUM = submitter_num
        self.RANDOMIZER_NUM = randomizer_num
        self.RANDOMIZER_REGISTERED = 0
        self.SUBTASK_NUM = subtask_num
        self.RE_ENC_NUM = re_enc_num
        self.config = Config()

        # 所有节点
        self.requester = None
        self.randomizers = None
        self.submitters = None

        # 从配置文件读取参数
        self.ipfs_url = self.config.get_config("app").get("ipfs_url")
        self.web3_url = self.config.get_config("app").get("web3_url")

        # 【Client】参数
        self.CLIENT_PORT = self.config.get_config("client").get("serving_port")
        self.CLIENT_IP = self.config.get_config("client").get("ip")

        # 【Requester】参数
        self.REQUESTER_IP = self.config.get_config("requester").get("ip")
        self.REQUESTER_TASK_PULL_PORT = self.config.get_config("requester").get(
            "task_pull_port"
        )
        self.REUQESTER_SERVING_PORT = self.config.get_config("requester").get(
            "serving_port"
        )

        # 【Randomizer】参数
        self.RANDOMIZER_IP = self.config.get_config("randomizer").get("ip")
        self.RANDOMIZER_PROVING_SERVER_PORT_BASE = self.config.get_config(
            "randomizer"
        ).get("proving_server_port_base")
        self.RANDOMIZER_SERVING_PORT_BASE = self.config.get_config("randomizer").get(
            "serving_port_base"
        )

        # 【Submitter】参数
        self.SUBMITTER_IP = self.config.get_config("submitter").get("ip")
        self.SUBMITTER_SERVING_PORT_BASE = self.config.get_config("submitter").get(
            "serving_port_base"
        )

        # 保存Randomizer的参数提供给Requester
        self.randomizer_list = []
        for id in range(self.RANDOMIZER_NUM):
            self.randomizer_list.append(
                (self.RANDOMIZER_PROVING_SERVER_PORT_BASE + id, self.RANDOMIZER_IP)
            )

    def run(self):
        # 1.启动用于接收各节点信息的服务端
        self.__server_start()
        # 2.给各节点分配测试地址
        (
            requester_account,
            submitter_accounts,
            randomizer_accounts,
        ) = self.__assign_bc_accounts()
        # 3.部署智能合约
        contract_address, contract_abi = self.__deploy_contract(requester_account)
        # 4.初始化所有节点
        self.requester, self.randomizers, self.submitters = self.__init_all_nodes(
            contract_address,
            contract_abi,
            requester_account,
            randomizer_accounts,
            submitter_accounts,
        )
        # 5.启动所有节点的守护程序
        self.__start_all_nodes()

    # def stop(self):
    #     self.requester.stop()
    #     for randomizer in self.randomizers:
    #         randomizer.stop()
    #     for submitter in self.submitters:
    #         submitter.stop()
    #     log.info(f"【Client】all nodes stoped  ...")
        
    def __server_start(self):
        def server(conn, addr):
            instruction = recvLine(conn)
            # 先处理系统请求
            if instruction == "event/RANDOMIZER_REGISTERED":
                self.RANDOMIZER_REGISTERED += 1
            # 处理用户请求
            else:
                self.server_callback(instruction, conn, addr)

        # 启动服务器
        threading.Thread(
            target=listen_on_port,
            args=(server, self.CLIENT_PORT),
        ).start()

    def __start_all_nodes(self):
        # ------------------
        # 启动所有节点
        # ------------------
        self.requester.run()
        for randomizer in self.randomizers:
            randomizer.run()

        # 等待randomizer注册交易执行完成
        log.info(f"【Client】waiting for randomizers registering ...")
        while True:
            if self.RANDOMIZER_REGISTERED == self.RANDOMIZER_NUM:
                break
            time.sleep(1)

        for submitter in self.submitters:
            submitter.run()

    def __assign_bc_accounts(self):
        # ------------------
        # 1.给各节点分配区块链账户
        # ------------------
        accounts_path = self.config.get_config("app").get("account_path")
        with open(accounts_path, "r") as f:
            accounts = json.load(f)
        random.shuffle(accounts)

        # Requester的地址和私钥
        requester_account = (accounts[0][0], accounts[0][1])

        # Submitter的地址和私钥
        submitter_accounts = []
        for i in range(2, self.SUBMITTER_NUM + 2):
            account = accounts[i - 1][0]
            private_key = accounts[i - 1][1]
            submitter_accounts.append((account, private_key))

        # Randomizer的地址和私钥
        randomizer_accounts = []
        for i in range(
            self.SUBMITTER_NUM + 2, self.SUBMITTER_NUM + self.RANDOMIZER_NUM + 2
        ):
            account = accounts[i - 1][0]
            private_key = accounts[i - 1][1]
            randomizer_accounts.append((account, private_key))
        return requester_account, submitter_accounts, randomizer_accounts

    def __deploy_contract(self, requester_account):
        # ------------------
        # 合约部署
        # ------------------
        contract_address, contract_abi = deploy_smart_contract(
            "CrowdsourcingContract",
            self.web3_url,
            requester_account[0],
            requester_account[1],
            self.SUBTASK_NUM,
            self.RE_ENC_NUM,
        )
        return contract_address, contract_abi

    def __init_all_nodes(
        self,
        contract_address,
        contract_abi,
        requester_account,
        randomizer_accounts,
        submitter_accounts,
    ):
        # ------------------
        # 初始化 requester
        # ------------------
        requester = Requester(
            self.CLIENT_PORT,
            self.CLIENT_IP,
            self.REUQESTER_SERVING_PORT,
            self.ipfs_url,
            self.web3_url,
            contract_address,
            contract_abi,
            requester_account[0],
            requester_account[1],
            "tmp/keypairs/pk.pkl",
            "tmp/keypairs/sk.pkl",
            self.randomizer_list,
            self.task,
            self.REQUESTER_TASK_PULL_PORT,
        )

        # ------------------
        # 初始化 randomizer
        # ------------------
        randomizers = []
        for id in range(self.RANDOMIZER_NUM):
            randomizers.append(
                Randomizer(
                    self.CLIENT_PORT,
                    self.CLIENT_IP,
                    self.RANDOMIZER_SERVING_PORT_BASE + id,
                    self.ipfs_url,
                    self.web3_url,
                    contract_address,
                    contract_abi,
                    randomizer_accounts[id][0],
                    randomizer_accounts[id][1],
                    "tmp/keypairs/pk.pkl",
                    self.RANDOMIZER_PROVING_SERVER_PORT_BASE + id,
                    id,
                )
            )

        # ------------------
        # 初始化 submitter
        # ------------------
        submitters = []
        for id in range(self.SUBMITTER_NUM):
            submitters.append(
                Submitter(
                    self.CLIENT_PORT,
                    self.CLIENT_IP,
                    self.SUBMITTER_SERVING_PORT_BASE + id,
                    self.ipfs_url,
                    self.web3_url,
                    contract_address,
                    contract_abi,
                    submitter_accounts[id][0],
                    submitter_accounts[id][1],
                    "tmp/keypairs/pk.pkl",
                    self.REQUESTER_IP,
                    self.REQUESTER_TASK_PULL_PORT,
                    self.task.SUBTASK_CLS,
                    id,
                )
            )
        return requester, randomizers, submitters

    def call_requester(self, data, need_ret=True):
        def handler(conn):
            sendLine(conn, data)
            if need_ret:
                ret = recvLine(conn)
                return ret

        return connect_to(handler, self.REUQESTER_SERVING_PORT, self.REQUESTER_IP)

    def call_randomizer(self, id, data, need_ret=True):
        def handler(conn):
            sendLine(conn, data)
            if need_ret:
                ret = recvLine(conn)
                return ret

        return connect_to(
            handler, self.RANDOMIZER_SERVING_PORT_BASE + id, self.RANDOMIZER_IP
        )

    def call_submitter(self, id, data, need_ret=True):
        def handler(conn):
            sendLine(conn, data)
            if need_ret:
                ret = recvLine(conn)
                return ret

        return connect_to(
            handler, self.SUBMITTER_SERVING_PORT_BASE + id, self.SUBMITTER_IP
        )

if __name__ == "__main__":
    from prototype.task.cifar10_tagging import CIFAR10Task

    def server(instruction, conn, addr):
        if instruction == "event/TASK_END":
            print("event/TASK_END")

    # 启动分布式系统
    task = CIFAR10Task("CIFAR10 tagging", 10)
    system = SystemInterface(
        task, server, submitter_num=1, randomizer_num=5, subtask_num=10, re_enc_num=1
    )
    system.run()

    # for id in range(1):
    #     system.call_submitter(id, "start", False)

    system.stop()
