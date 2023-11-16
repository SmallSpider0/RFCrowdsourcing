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
    ):
        # 初始化其它参数
        self.requester_ip = requester_ip
        self.requester_task_pull_port = requester_task_pull_port

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
        self.__main_loop()

    # submitter的主循环
    def __main_loop(self):
        while True:
            subtask = self.pull_task()
            if subtask == None:
                break
            answer = subtask.execute()
            self.submit_answers(answer)

    # 从requester拉取众包任务
    def pull_task(self):
        def handler(conn):
            subtask = recvLine(conn)
            return subtask
        subtask = connect_to(handler, self.requester_task_pull_port, self.requester_ip)
        return subtask

    # 提交回答（完成任务后调用）
    def submit_answer(self, answer):
        # 调用函数从回答中提取出内容，并加密和获取承诺
        answer_cipher = self.encryptor.encrypt(str(answer))
        answer_commit = self._generate_commitment(answer_cipher)

        # 上传区块链和IPFS
        filehash = self.submit_ipfs(str(answer_cipher))
        self.__submit_commit(answer_commit, filehash)
        

    def __submit_commit(self, commit, filehash):
        # 上传密文至区块链、
        # TODO：实现
        pass

if __name__ == "__main__":
    # 导入测试所需的包
    import json
    import time

    # 测试参数定义
    ipfs_url = "/ip4/127.0.0.1/tcp/5001"
    web3_url = "http://127.0.0.1:8545"
    contract_address = "0xd7357e2A30760f94971bC8Eb10f5dd0D1cFdB6Ae"
    with open("solidity/contract-abi.json") as file:
        contract_abi = json.loads(file.read())  # 智能合约ABI

    # requester对象初始化
    randomizer = Submitter(
        ipfs_url,
        web3_url,
        contract_address,
        contract_abi,
        "tmp/keypairs/pk.pkl",
        "localhost",
        11111,
    )
