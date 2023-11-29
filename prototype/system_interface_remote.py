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

# 系统库
import time
import json
import random
import threading
import pickle


# TODO：实现自动远程部署（本地测试使用命令行开启新的进程实现）
class SystemInterfaceRemote:
    def __init__(
        self,
        task_name,
        server_callback,
        submitter_num,
        randomizer_num,
        subtask_num,
        re_enc_num,
        server_list,
    ):
        # 其它参数
        self.task_name = task_name
        self.server_callback = server_callback
        self.SUBMITTER_NUM = submitter_num
        self.RANDOMIZER_NUM = randomizer_num
        self.RANDOMIZER_REGISTERED = 0
        self.SUBTASK_NUM = subtask_num
        self.RE_ENC_NUM = re_enc_num

        # 可用的服务器列表（包含IP和认证方式）
        self.server_list = server_list

        # 所有节点参数
        self.requester_para = None
        self.randomizers_para = []
        self.submitters_para = []

        # 节点IP
        self.REQUESTER_IP = None
        self.SUBMITTER_IP = None
        self.RANDOMIZER_IP = []

        # 【通用参数】
        self.config = Config()
        self.MANAGER_PORT_BASE = self.config.get_config("app").get("manager_port_base")
        self.ipfs_url = self.config.get_config("app").get("ipfs_url")
        self.web3_url = self.config.get_config("app").get("web3_url")
        public_key_file = self.config.get_config("app").get("public_key_file")
        private_key_file = self.config.get_config("app").get("private_key_file")
        with open(public_key_file, "rb") as f:
            self.public_key_str = pickle.load(f)
        with open(private_key_file, "rb") as f:
            self.private_key_str = pickle.load(f)

        # 【Client】参数
        self.CLIENT_PORT = self.config.get_config("client").get("serving_port")
        self.CLIENT_IP = self.config.get_config("client").get("ip")

        # 【Requester】参数
        # self.REQUESTER_IP = self.config.get_config("requester").get("ip")
        self.REQUESTER_TASK_PULL_PORT = self.config.get_config("requester").get(
            "task_pull_port"
        )
        self.REUQESTER_SERVING_PORT = self.config.get_config("requester").get(
            "serving_port"
        )

        # 【Randomizer】参数
        # self.RANDOMIZER_IP = self.config.get_config("randomizer").get("ip")
        self.RANDOMIZER_PROVING_SERVER_PORT_BASE = self.config.get_config(
            "randomizer"
        ).get("proving_server_port_base")
        self.RANDOMIZER_SERVING_PORT_BASE = self.config.get_config("randomizer").get(
            "serving_port_base"
        )

        # 【Submitter】参数
        # self.SUBMITTER_IP = self.config.get_config("submitter").get("ip")
        self.SUBMITTER_SERVING_PORT_BASE = self.config.get_config("submitter").get(
            "serving_port_base"
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

        # 4.给服务器分配节点
        self.__assign_node_to_server()

        # 5.初始化所有节点
        self.__init_all_nodes(
            contract_address,
            contract_abi,
            requester_account,
            randomizer_accounts,
            submitter_accounts,
        )

        # 6.启动所有服务器的管理进程
        self.__start_manager()

        # 7.与各服务器管理进程通信，启动所有节点的守护程序
        self.__start_all_nodes()

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
            handler, self.RANDOMIZER_SERVING_PORT_BASE + id, self.RANDOMIZER_IP[id]
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

    def __assign_node_to_server(self):
        # ------------------
        # 将节点分配至服务器（管理节点）
        # ------------------

        # 节点分配方式：
        # 服务器0：
        # 基础环境，包括私有链+IPFS

        for i in range(len(self.server_list)):
            server_list[i]["manager_port"] = self.MANAGER_PORT_BASE + i

        # 【分配】Requester（一台服务器，为了体现轻量性，限制只使用一个CPU核心）
        self.server_list[0]["role"] = ("Requester", 1)
        self.REQUESTER_IP = self.server_list[0]["ip"]

        # 【分配】Submitter（一台服务器，模拟所有的submitter）
        self.server_list[1]["role"] = ("Submitter", self.SUBMITTER_NUM)
        self.SUBMITTER_IP = self.server_list[1]["ip"]

        # 【分配】Randomizer（分布在多台服务器上（每个节点独享一个CPU核心），【并模拟网络延迟】）
        assignd = 0
        for server in self.server_list[2:]:
            if assignd + server["cpu_cores"] <= self.RANDOMIZER_NUM:
                cnt = server["cpu_cores"]
                server["role"] = ("Randomizer", cnt)
                self.RANDOMIZER_IP[assignd : assignd + cnt] = [server["ip"]] * cnt
                assignd += cnt
            else:
                cnt = self.RANDOMIZER_NUM - assignd
                server["role"] = ("Randomizer", cnt)
                self.RANDOMIZER_IP[assignd : assignd + cnt] = [server["ip"]] * cnt
                break

    def __start_all_nodes(self):
        # --------------------------------------
        # 向各服务器上的管理进程发送请求，启动所有节点
        # --------------------------------------
        randomizer_id = 0
        for server in self.server_list:
            if not "role" in server:
                break
            role = server["role"]
            # 【Requester】
            if role[0] == "Requester":
                ret = self.__call_manager(
                    "start/REQUESTER", self.requester_para, server
                )
            # 【Submitter】
            elif role[0] == "Submitter":
                ret = self.__call_manager(
                    "start/SUBMITTERS", self.submitters_para, server
                )
            # 【Randomizer】
            elif role[0] == "Randomizer":
                para_batch = []
                for _ in range(role[1]):
                    para_batch.append(self.randomizers_para[randomizer_id])
                    randomizer_id += 1
                ret = self.__call_manager(
                    "start/RANDOMIZERS",
                    para_batch,
                    server,
                )

        # 等待Randomizer注册完成
        log.info(f"【Client】waiting for randomizers registering ...")
        while True:
            if self.RANDOMIZER_REGISTERED == self.RANDOMIZER_NUM:
                break
            time.sleep(1)
        log.info(f"【Client】all randomizers registered")

    # 连接远程服务器并启动管理进程
    def __start_manager(self):
        # TODO:需要确定如何实现
        for server in self.server_list:
            pass

    # 与管理进程进行通信
    def __call_manager(self, instructioin, data, server):
        def handler(conn):
            sendLine(conn, instructioin)
            sendLine(conn, data)
            ret = recvLine(conn)
            return ret

        return connect_to(handler, server["manager_port"], server["ip"])

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
        # 初始化 requester参数
        # ------------------
        randomizer_list = []
        for id in range(self.RANDOMIZER_NUM):
            randomizer_list.append(
                (self.RANDOMIZER_PROVING_SERVER_PORT_BASE + id, self.RANDOMIZER_IP[id])
            )
        self.requester_para = {
            "task_name": self.task_name,
            "subtask_num": self.SUBTASK_NUM,
            "CLIENT_PORT": self.CLIENT_PORT,
            "client_ip": self.CLIENT_IP,
            "REUQESTER_SERVING_PORT": self.REUQESTER_SERVING_PORT,
            "ipfs_url": self.ipfs_url,
            "web3_url": self.web3_url,
            "contract_address": contract_address,
            "contract_abi": contract_abi,
            "bc_account": requester_account[0],
            "bc_private_key": requester_account[1],
            "requester_pk_str": self.public_key_str,
            "requester_sk_str": self.private_key_str,
            "randomizer_list": randomizer_list,
            "REQUESTER_TASK_PULL_PORT": self.REQUESTER_TASK_PULL_PORT,
        }

        # ------------------
        # 初始化 submitter参数
        # ------------------
        for id in range(self.SUBMITTER_NUM):
            self.submitters_para.append(
                {
                    "task_name": self.task_name,
                    "CLIENT_PORT": self.CLIENT_PORT,
                    "client_ip": self.CLIENT_IP,
                    "serving_port": self.SUBMITTER_SERVING_PORT_BASE + id,
                    "ipfs_url": self.ipfs_url,
                    "web3_url": self.web3_url,
                    "contract_address": contract_address,
                    "contract_abi": contract_abi,
                    "bc_account": submitter_accounts[id][0],
                    "bc_private_key": submitter_accounts[id][1],
                    "requester_pk_str": self.public_key_str,
                    "REQUESTER_IP": self.REQUESTER_IP,
                    "REQUESTER_TASK_PULL_PORT": self.REQUESTER_TASK_PULL_PORT,
                    "id": id,
                }
            )

        # ------------------
        # 初始化 randomizer参数
        # ------------------
        for id in range(self.RANDOMIZER_NUM):
            self.randomizers_para.append(
                {
                    "CLIENT_PORT": self.CLIENT_PORT,
                    "client_ip": self.CLIENT_IP,
                    "serving_port": self.RANDOMIZER_SERVING_PORT_BASE + id,
                    "ipfs_url": self.ipfs_url,
                    "web3_url": self.web3_url,
                    "contract_address": contract_address,
                    "contract_abi": contract_abi,
                    "bc_account": randomizer_accounts[id][0],
                    "bc_private_key": randomizer_accounts[id][1],
                    "requester_pk_str": self.public_key_str,
                    "PROVING_SERVER_PORT": self.RANDOMIZER_PROVING_SERVER_PORT_BASE
                    + id,
                    "id": id,
                }
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


if __name__ == "__main__":

    def server(instruction, conn, addr):
        if instruction == "event/TASK_END":
            print("event/TASK_END")

    server_list = [
        {
            "name": "test1",
            "ip": "localhost",
            "auth": {"type": "local", "data": None},
            "cpu_cores": 4,
        },
        {
            "name": "test2",
            "ip": "localhost",
            "auth": {"type": "local", "data": None},
            "cpu_cores": 4,
        },
        {
            "name": "test3",
            "ip": "localhost",
            "auth": {"type": "local", "data": None},
            "cpu_cores": 10,
        },
        {
            "name": "test4",
            "ip": "localhost",
            "auth": {"type": "local", "data": None},
            "cpu_cores": 10,
        },
        # {
        #     "ip": "10.12.36.34",
        #     "auth": {"type": "psw", "data": {"user": "root", "password": "root"}},
        #     "roles": (0, 1, 0),
        # },
    ]

    # 启动分布式系统
    system = SystemInterfaceRemote(
        "CIFAR10Task",
        server,
        submitter_num=10,
        randomizer_num=10,
        subtask_num=10,
        re_enc_num=2,
        server_list=server_list,
    )
    system.run()

    for id in range(1):
        system.call_submitter(id, "start", False)