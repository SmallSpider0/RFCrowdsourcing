# 添加当前路径至解释器，确保单元测试时可正常import其它文件
import os
import sys

current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 基于顶层包的import
from prototype.requester import Requester
from prototype.submitter import Submitter
from prototype.randomizer import Randomizer
from prototype.utils.tools import deploy_smart_contract

# 系统库
import json
import random
import time
from prototype.utils.config import Config


class SystemInit:
    def __init__(self, task, submitter_num, randomizer_num, subtask_num, re_enc_num):
        # 其它参数
        self.task = task
        self.SUBMITTER_NUM = submitter_num
        self.RANDOMIZER_NUM = randomizer_num
        self.SUBTASK_NUM = subtask_num
        self.RE_ENC_NUM = re_enc_num
        self.config = Config()

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

    def __start_all_nodes(self, requester, randomizers, submitters):
        # ------------------
        # 启动所有节点
        # ------------------
        requester.run()
        for randomizer in randomizers:
            randomizer.run()
        time.sleep(20)  # 等待randomizer注册交易执行完成
        for submitter in submitters:
            submitter.run()

    def run(self):
        # 1.给各节点分配测试地址
        (
            requester_account,
            submitter_accounts,
            randomizer_accounts,
        ) = self.__assign_bc_accounts()
        # 2.部署智能合约
        contract_address, contract_abi = self.__deploy_contract(requester_account)
        # 3.初始化所有节点
        requester, randomizers, submitters = self.__init_all_nodes(
            contract_address,
            contract_abi,
            requester_account,
            randomizer_accounts,
            submitter_accounts,
        )
        # 4.启动所有节点的守护程序
        self.__start_all_nodes(requester, randomizers, submitters)


if __name__ == "__main__":
    from prototype.task.cifar10_tagging import CIFAR10Task

    task = CIFAR10Task("CIFAR10 tagging", 10)
    system = SystemInit(task, 1, 1, 10, 1)
    system.run()