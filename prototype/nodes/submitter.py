# 添加当前路径至解释器，确保单元测试时可正常import其它文件
import os
import sys

current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 基于顶层包的import
from prototype.utils.network import listen_on_port, connect_to, sendLine, recvLine
from prototype.nodes.base_node import BaseNode
from prototype.utils import log
from prototype.task.task_interface import SubTaskInterface

# 系统库
import threading
import random
from multiprocessing import Process

class Submitter(BaseNode, Process):
    # 构造函数
    def __init__(
        self,
        client_port,
        client_ip,
        serving_port,
        ipfs_url,
        provider_url,
        contract_address,
        contract_abi,
        bc_account,
        bc_private_key,
        requester_pk_str,
        requester_ip,
        requester_task_pull_port,
        subtask_cls: SubTaskInterface,
        id,
    ):
        Process.__init__(self)
        self.init_paras = {
            "client_port": client_port,
            "client_ip": client_ip,
            "serving_port": serving_port,
            "ipfs_url": ipfs_url,
            "provider_url": provider_url,
            "contract_address": contract_address,
            "contract_abi": contract_abi,
            "bc_account": bc_account,
            "bc_private_key": bc_private_key,
            "requester_pk_str": requester_pk_str,
            "requester_ip": requester_ip,
            "requester_task_pull_port": requester_task_pull_port,
            "subtask_cls": subtask_cls,
            "id": id,
        }

    def __my_init(self):
        # 初始化其它参数
        self.id = self.init_paras["id"]
        self.requester_ip = self.init_paras["requester_ip"]
        self.requester_task_pull_port = self.init_paras["requester_task_pull_port"]
        self.subtask_cls = self.init_paras["subtask_cls"]

        # 基类初始化
        BaseNode.__init__(
            self,
            self.init_paras["client_port"],
            self.init_paras["client_ip"],
            self.init_paras["serving_port"],
            self.init_paras["ipfs_url"],
            self.init_paras["provider_url"],
            self.init_paras["contract_address"],
            self.init_paras["contract_abi"],
            self.init_paras["bc_account"],
            self.init_paras["bc_private_key"],
            self.init_paras["requester_pk_str"],
        )

    # 外部控制接口启动
    def run(self):
        # 初始化
        self.__my_init()

        # 服务器功能定义
        def server(conn, addr):
            instruction = recvLine(conn)
            # 节点启动
            if instruction == "start":
                self.daemon_start()
            # 获取总gas开销
            elif instruction == "get/gas_cost":
                sendLine(conn, self.contract_interface.total_gas_cost)
            conn.close()

        # 启动服务器
        threading.Thread(
            target=listen_on_port,
            args=(server, self.serving_port),
        ).start()
        log.info(f"【Submitter】serving started")

    # 启动守护程序
    def daemon_start(self):
        # 创建并启动一个新线程来运行主循环
        thread = threading.Thread(target=self.__main_loop)
        thread.start()

    # submitter的主循环
    def __main_loop(self):
        while True:
            self.subtask = self.pull_task()
            log.debug(f"【Submitter】{self.id} task received")
            if self.subtask == None:
                break
            answer = self.subtask.execute()
            self.submit_answer(answer)
            log.info(
                f"【Submitter】{self.id} successed submitted answer of task {self.subtask.id}"
            )

    # 从requester拉取众包任务
    def pull_task(self):
        def handler(conn):
            subtask_str = recvLine(conn)
            conn.close()
            return subtask_str

        subtask_str = connect_to(
            handler, self.requester_task_pull_port, self.requester_ip
        )
        if subtask_str == "None":
            return None
        else:
            return self.subtask_cls.from_str(subtask_str)

    # 提交回答（完成任务后调用）
    def submit_answer(self, answer):
        # 调用函数从回答中提取出内容，并加密和获取承诺
        answer_ciphers = self.encryptor.encrypt(answer.encode())
        answer_commit = self._generate_commitment(answer_ciphers)
        # 上传区块链和IPFS
        filehash = self.submit_ipfs([str(c) for c in answer_ciphers])
        self.__submit_commit(answer_commit, filehash)

    def __submit_commit(self, commit, filehash):
        # 上传密文至区块链
        # TODO：实现基于VRF的随机数生成
        vrf_output = random.randint(1, 1000)
        self.contract_interface.send_transaction(
            "submitSubTaskAnswer", self.subtask.id, commit, filehash, vrf_output
        )


if __name__ == "__main__":
    # 导入测试所需的包
    import json

    # 测试参数定义
    ipfs_url = "/ip4/127.0.0.1/tcp/5001"
    web3_url = "http://127.0.0.1:8545"
    contract_address = "0xd7357e2A30760f94971bC8Eb10f5dd0D1cFdB6Ae"
    with open("solidity/contract-abi.json") as file:
        contract_abi = json.loads(file.read())  # 智能合约ABI

    from task.simple_task import SimpleSubtask

    TASK_PULL_IP = "localhost"
    TASK_PULL_PORT = 11111
    # submitter对象初始化
    submitter = Submitter(
        ipfs_url,
        web3_url,
        contract_address,
        contract_abi,
        "tmp/keypairs/pk.pkl",
        TASK_PULL_IP,
        TASK_PULL_PORT,
        SimpleSubtask,
    )

    submitter.daemon_start()
