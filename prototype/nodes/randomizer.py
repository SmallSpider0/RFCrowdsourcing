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
from prototype.utils.tools import find_next_element

# 系统库
import threading
import time
import queue
from multiprocessing import Queue, Process


class Randomizer(Process, BaseNode):
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
        proving_server_port,
        id=0,
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
            "proving_server_port": proving_server_port,
            "id": id
        }

    def __my_init(self):
        # 其它参数初始化
        self.proving_server_port = self.init_paras["proving_server_port"]
        self.id = self.init_paras["id"]
        self.old_alpha_primes = {}

        # 初始化用于存储子任务被选中Randomizers的字典
        self.selectedRandomizers = {}
        self.task_queue = Queue()  # 待处理的事件队列

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

        # 启动功能
        self.daemon_start()

        # 服务器功能定义
        def server(conn, addr):
            instruction = recvLine(conn)
            if instruction == "get/gas_cost":
                sendLine(conn, self.contract_interface.total_gas_cost)
            conn.close()

        # 启动服务器
        threading.Thread(
            target=listen_on_port,
            args=(server, self.serving_port),
        ).start()
        log.info(f"【Randomizer】serving started")

    def daemon_start(self):
        # 0.注册
        self.contract_interface.send_transaction_receipt(
            lambda _, receipt: self.emit_event("RANDOMIZER_REGISTERED"),
            "registerRandomizer",
            self.id,
        )
        log.debug(f"【Randomizer】{self.id} registrated")

        # 1.启动事件监听器
        # 监听SubTaskAnswerSubmitted事件，如果发现自己被选中了，则保存该task被选中的Randomizer列表
        self.contract_interface.listen_for_events(
            "SubTaskAnswerSubmitted", self.__handle_SubTaskAnswerSubmitted, True
        )
        # 监听SubTaskAnswerEncrypted事件，如果发现自己前一个Randomizer完成了重加密，则自己进行重加密
        self.contract_interface.listen_for_events(
            "SubTaskAnswerEncrypted", self.__handle_SubTaskAnswerEncrypted, True
        )

        # 2.启动事件处理服务
        threading.Thread(target=self.__task_handler_daemon).start()

        # 3.启动重加密ZKP验证服务
        threading.Thread(
            target=listen_on_port,
            args=(self.__proving_server, self.proving_server_port),
        ).start()

    # 接收Requester的请求：重加密结果的唯一id（例如区块链上的哈希），要求证明有效性
    # Randomizer应该在重加密后保存相关结果用于提供证明
    def __proving_server(self, conn, addr):
        # 与Requester交互式验证重加密ZKP
        # 证明ciphertext使用alpha_prime重加密得到new_ciphertext

        # 0.证明者接收验证请求，并从本地获取验证所需的信息
        commit = recvLine(conn)
        alpha_prime = self.old_alpha_primes[commit]

        # 1.证明者发送e_prime，并保存alpha_tmp
        e_prime, alpha_tmp = self.encryptor.proveReEncrypt_1()
        sendLine(conn, str(e_prime))

        # 2.接收验证者发送的挑战c，并构造和发送beta
        c = recvLine(conn)
        beta = self.encryptor.proveReEncrypt_3(c, alpha_prime, alpha_tmp)
        sendLine(conn, beta)

        log.debug(f"【Randomizer】{self.id} successed handled ZKP verification")

    def __task_handler_daemon(self):
        while True:
            event_name, args = self.task_queue.get()
            # 使用subTaskId作为索引来存储事件数据
            if args["subTaskId"] not in self.selectedRandomizers:
                ret = self.contract_interface.call_function(
                    "getSelectedRandomizers", args["subTaskId"]
                )
                if self.id in ret:
                    self.selectedRandomizers[args["subTaskId"]] = ret
                else:
                    self.selectedRandomizers[args["subTaskId"]] = None
            if event_name == "SubTaskAnswerSubmitted":
                # 仅当自己被选中才执行后续操作
                if self.selectedRandomizers[args["subTaskId"]] != None:
                    # 如果自己是第一顺位，则进行重加密
                    if self.id == self.selectedRandomizers[args["subTaskId"]][0]:
                        self.__perform_re_encryption(
                            args["subTaskId"], args["filehash"]
                        )
            elif event_name == "SubTaskAnswerEncrypted":
                # 根据args['subTaskId']判断是否和自己有关，若有关则从self.event_data取出任务信息
                if self.selectedRandomizers[args["subTaskId"]] != None:
                    # 获取args['randomizerId'] 在selectedRandomizers中的位置，如果在自己id的前一位，则进行重加密
                    if self.id == find_next_element(
                        self.selectedRandomizers[args["subTaskId"]],
                        args["randomizerId"],
                    ):
                        self.__perform_re_encryption(
                            args["subTaskId"], args["filehash"]
                        )

    def __handle_SubTaskAnswerSubmitted(self, raw_event, args):
        self.task_queue.put(("SubTaskAnswerSubmitted", args))

    def __handle_SubTaskAnswerEncrypted(self, raw_event, args):
        self.task_queue.put(("SubTaskAnswerEncrypted", args))

    def __perform_re_encryption(self, task_id, filehash):
        # 1.根据智能合约中存储的pointer，从分布式文件存储服务下载回答密文
        file = self.fetch_ipfs(filehash)
        ciphertexts = [self.encryptor.createCiphertext(c) for c in file]

        # 2.进行重加密
        alpha_prime = self.encryptor.genAlpha()
        new_ciphertexts = self.encryptor.reEncrypt(ciphertexts, alpha_prime)

        # 3.提交重加密结果
        file_hash = self.submit_ipfs([str(c) for c in new_ciphertexts])

        # 4.在本地保存一份结果 用于后续验证
        commit = self._generate_commitment(new_ciphertexts)
        self.old_alpha_primes[commit] = alpha_prime

        # 5.将重加密结果的承诺和文件指针上传至区块链
        self.contract_interface.send_transaction(
            "encryptSubTaskAnswer",
            task_id,
            commit,
            file_hash,
        )
        log.info(f"【Randomizer】{self.id} successfully handeled task {task_id}")


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

    PORT = 10000
    # randomizer对象初始化
    randomizer = Randomizer(
        ipfs_url, web3_url, contract_address, contract_abi, "tmp/keypairs/pk.pkl", PORT
    )

    # 启动守护程序
    randomizer.daemon_start()

    # 模拟触发event
    account = "0xe7B44655990857181d5fCfaaAe3471B2B911CaB4"
    private_key = "0x5ddfd9257c762b7b23f65844dac651b8469c01b1b14291ffde2a9017d15453c5"
    randomizer.contract_interface.send_transaction("receiveInteger", 123)

    # 异步监听时可以做其他事
    time.sleep(1000000)
