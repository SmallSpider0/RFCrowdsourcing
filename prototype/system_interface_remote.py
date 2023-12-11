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
from prototype.utils.tools import deploy_smart_contract, ssh_command
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
        public_key_file,
        private_key_file,
    ):
        # 其它参数
        self.config = Config()
        self.task_name = task_name
        self.server_callback = server_callback
        self.SUBMITTER_NUM = submitter_num
        self.RANDOMIZER_NUM = randomizer_num
        self.RANDOMIZER_REGISTERED = 0
        self.SUBTASK_NUM = subtask_num
        self.RE_ENC_NUM = re_enc_num

        # 可用的服务器列表（包含IP和认证方式）
        server_list_path = self.config.get_config("app").get("server_list_path")
        with open(server_list_path, "r") as f:
            server_list = json.load(f)
        self.server_list = server_list

        # 所有节点参数
        self.requester_para = None
        self.randomizers_para = []
        self.submitters_para = []

        # 节点IP
        self.REQUESTER_IP = None
        self.SUBMITTER_IP = None
        self.RANDOMIZER_IP = []

        # 实验用参数
        self.times = {}

        # 【通用参数】
        self.MANAGER_PORT_BASE = self.config.get_config("app").get("manager_port_base")
        self.ipfs_url = self.config.get_config("app").get("ipfs_url")
        self.web3_url = self.config.get_config("app").get("web3_url")
        with open(public_key_file, "rb") as f:
            self.public_key_str = pickle.load(f)
        with open(private_key_file, "rb") as f:
            self.private_key_str = pickle.load(f)

        # 【Client】参数
        self.manager_start_command = self.config.get_config("client").get(
            "manager_start_command"
        )
        self.envs_start_command = self.config.get_config("client").get(
            "envs_start_command"
        )
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
        # self.start_manager()

        # 7.与各服务器管理进程通信，启动所有节点的守护程序
        self.__start_all_nodes()

    # 部署区块链环境
    def start_envs(self):
        server = self.server_list[0]
        log.info(f"【Client】deploying enviroment on server {server['name']}...")
        # 环境部署在列表中第一台服务器上
        ret = ssh_command(server, self.envs_start_command)
        log.info(f"【Client】enviroment deployed success...")

    # 连接远程服务器并启动管理进程
    def start_manager(self, local=0):
        def ssh_command_with_thread(server, command):
            # 这里执行 SSH 命令
            ret = ssh_command(server, command)

        if local == 0:
            for server in self.server_list:
                server["ip"] = self.server_list[0]["ip"]
        else:
            if local == 1:
                threads = []
                log.info("【Client】deploying manager on local server ...")
                server = self.server_list[0]
                thread = threading.Thread(
                    target=ssh_command_with_thread,
                    args=(server, self.manager_start_command),
                )
                threads.append(thread)
                for server in self.server_list:
                    server["ip"] = self.server_list[0]["ip"]
            elif local == 2:
                for server in self.server_list[1:]:
                    log.info(f"【Client】deploying manager on server {server['name']}...")
                    thread = threading.Thread(
                        target=ssh_command_with_thread,
                        args=(server, self.manager_start_command),
                    )
                    threads.append(thread)

            # 启动所有线程
            for thread in threads:
                thread.start()

            # 等待所有线程完成
            for thread in threads:
                thread.join()

        log.info("【Client】manager deployed success...")

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

    def __server_start(self):
        def server(conn, addr):
            instruction = recvLine(conn)
            # 先处理系统请求
            if instruction == "event/RANDOMIZER_REGISTERED":
                self.RANDOMIZER_REGISTERED += 1
            # 处理用户请求
            else:
                self.server_callback(instruction, conn, addr)
                if instruction == "event/TASK_END":
                    return "STOP"

        # 启动服务器
        threading.Thread(
            target=listen_on_port,
            args=(server, self.CLIENT_PORT, False),
        ).start()

    def __assign_node_to_server(self):
        # ------------------
        # 将节点分配至服务器（管理节点）
        # ------------------

        # 节点分配方式：
        # 服务器0：
        # 基础环境，包括私有链+IPFS

        # 【分配】Requester（一台服务器，为了体现轻量性，限制只使用一个CPU核心）
        self.server_list[1]["role"] = ("Requester", 1)
        self.REQUESTER_IP = self.server_list[1]["ip"]

        # 【分配】Submitter（一台服务器，模拟所有的submitter）
        self.server_list[2]["role"] = ("Submitter", self.SUBMITTER_NUM)
        self.SUBMITTER_IP = self.server_list[2]["ip"]

        # 【分配】Randomizer（分布在多台服务器上（每个节点独享一个CPU核心），【并模拟网络延迟】）
        assignd = 0
        for server in self.server_list[3:]:
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
                continue
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
        self.times["inited"] = time.time()

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
        log.info(f"【Client】deploying smart contract ...")
        contract_address, contract_abi = deploy_smart_contract(
            "CrowdsourcingContract",
            self.web3_url,
            requester_account[0],
            requester_account[1],
            self.SUBTASK_NUM * 3,
            self.RE_ENC_NUM,
        )
        log.info(f"【Client】smart contract success deployed...")
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
    st = time.time()

    def server(instruction, conn, addr):
        if instruction == "event/TASK_END":
            print("event/TASK_END")
            print("dur", time.time() - st)

    # TODO：执行命令 配置内网穿透（服务器1上）
    SUBMITTER_NUM = 10
    RANDOMIZER_NUM = 20
    SUBTASK_NUM = 100
    RE_ENC_NUM = 2

    # 启动分布式系统
    system = SystemInterfaceRemote(
        "CIFAR10Task", server, SUBMITTER_NUM, RANDOMIZER_NUM, SUBTASK_NUM, RE_ENC_NUM
    )
    system.start_manager()
    system.run()

    for id in range(SUBMITTER_NUM):
        system.call_submitter(id, "start", False)
