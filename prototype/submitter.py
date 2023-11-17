# 添加当前路径至解释器，确保单元测试时可正常import其它文件
import os
import sys

current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 基于顶层包的import
from utils.network import listen_on_port, connect_to, sendLine, recvLine
from prototype.base_node import BaseNode
from utils import log
from task.task_interface import SubTaskInterface

# 系统库
import threading

class Submitter(BaseNode):
    # 构造函数
    def __init__(
        self,
        ipfs_url,
        provider_url,
        contract_address,
        contract_abi,
        requester_pk_file,
        requester_ip,
        requester_task_pull_port,
        subtask_cls: SubTaskInterface,
    ):
        # 初始化其它参数
        self.requester_ip = requester_ip
        self.requester_task_pull_port = requester_task_pull_port
        self.subtask_cls = subtask_cls

        # 基类初始化
        super().__init__(
            ipfs_url,
            provider_url,
            contract_address,
            contract_abi,
            requester_pk_file,
        )

    # 启动守护程序
    def daemon_start(self):
        # 创建并启动一个新线程来运行主循环
        thread = threading.Thread(target=self.__main_loop)
        thread.start()

    # submitter的主循环
    def __main_loop(self):
        while True:
            subtask = self.pull_task()
            log.debug(f"【Submitter】task received: {str(subtask)}")
            if subtask == None:
                break
            answer = subtask.execute()
            log.debug(f"【Submitter】answer generated: {str(answer)}")
            self.submit_answer(answer)

    # 从requester拉取众包任务
    def pull_task(self):
        def handler(conn):
            subtask_str = recvLine(conn)
            return subtask_str
        subtask_str = connect_to(handler, self.requester_task_pull_port, self.requester_ip)
        if subtask_str == "None":
            return None
        else:
            return self.subtask_cls.from_str(subtask_str)

    # 提交回答（完成任务后调用）
    def submit_answer(self, answer):
        # 调用函数从回答中提取出内容，并加密和获取承诺
        answer_cipher = self.encryptor.encrypt(int(str(answer)))
        answer_commit = self._generate_commitment(answer_cipher)
        # 上传区块链和IPFS
        filehash = self.submit_ipfs(str(answer_cipher))
        self.__submit_commit(answer_commit, filehash)
        log.debug(f"【Submitter】successed submitted answer: {filehash}")

    def __submit_commit(self, commit, filehash):
        # 上传密文至区块链
        # TODO：实现
        pass


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
        SimpleSubtask
    )

    submitter.daemon_start()