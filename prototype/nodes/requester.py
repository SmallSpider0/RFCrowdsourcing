# 添加当前路径至解释器，确保单元测试时可正常import其它文件
import os
import sys

current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 基于顶层包的import
from prototype.utils.network import listen_on_port, connect_to, sendLine, recvLine
from prototype.nodes.base_node import BaseNode
from prototype.task.task_interface import TaskInterface
from prototype.utils import log

# 系统库
import threading
import queue
import time
from multiprocessing import Queue, Process


class Requester(Process, BaseNode):
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
        requester_sk_str,
        randomizer_list,
        task: TaskInterface,
        task_pull_serving_port,
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
            "requester_sk_str": requester_sk_str,
            "randomizer_list": randomizer_list,
            "task": task,
            "task_pull_serving_port": task_pull_serving_port,
        }

    def __my_init(self):
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
            self.init_paras["requester_sk_str"],
        )

        # 其它参数初始化
        self.randomizer_list = self.init_paras["randomizer_list"]
        self.task_pull_serving_port = self.init_paras["task_pull_serving_port"]
        self.task = self.init_paras["task"]
        self.randomizer_of_subtasks = {}  # subtaskid->使用的Randomizer列表
        self.answers_of_subtasks = Queue()  # 解密后的回答对象
        self.task_queue = Queue()  # 待处理的事件队列

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
        log.info(f"【Requester】serving started")

    # 启动守护程序
    def daemon_start(self):
        # 1.启动监听器，监听特定事件
        # 调用getSubTaskFinalResult收集回答（全部重加密结果 文件hash+承诺）并处理
        self.contract_interface.listen_for_events(
            "SubTaskEncryptionCompleted", self.__handle_SubTaskEncryptionCompleted, True
        )
        # 监听SubTaskAnswerSubmitted
        # TODO：启动计时器（如果超时需要惩罚Randomizer）
        self.contract_interface.listen_for_events(
            "SubTaskAnswerSubmitted", self.__handle_SubTaskAnswerSubmitted, True
        )

        # 2.启动事件处理服务
        threading.Thread(target=self.__task_handler_daemon).start()

        # 3.启动任务获取服务
        threading.Thread(
            target=listen_on_port,
            args=(self.__task_pull_server, self.task_pull_serving_port),
        ).start()

        # 4.启动奖励发放器，执行随机延迟的奖励发放
        threading.Thread(target=self.__reward_dist_daemon).start()

    def __task_pull_server(self, conn, addr):
        # 生成一个新的task 并返回
        # 如果没有新的subtask了则返回None
        subtask = self.task.get_subtasks()
        st = time.time()
        sendLine(conn, str(subtask))  # 将任务序列化后发送
        # print("send time", time.time()-st)

    def __task_handler_daemon(self):
        while True:
            event_name, args = self.task_queue.get()
            if event_name == "SubTaskEncryptionCompleted":
                # TODO：异常返回值处理 + 重加密者奖惩
                # 1.从合约获取以完成任务的 提交+全部重加密结果文件哈希和承诺
                results = []
                sub_task_id = args["subTaskId"]
                ret = self.contract_interface.call_function(
                    "getSubTaskFinalResult", sub_task_id
                )
                # 获取初始提交
                results.append({"commit": ret[0], "filehash": ret[1]})
                # 获取所有重加密结果
                for encryption_result in ret[2]:
                    results.append(
                        {
                            "commit": encryption_result[0],
                            "filehash": encryption_result[1],
                        }
                    )

                # 2. 从IPFS获取密文，并验证承诺
                ciphertext_list = []
                for result in results:
                    # 获取密文
                    file = self.fetch_ipfs(result["filehash"])
                    ciphertexts = [self.encryptor.createCiphertext(c) for c in file]

                    # 验证承诺
                    commit = self._generate_commitment(ciphertexts)
                    if commit != result["commit"]:
                        continue
                    ciphertext_list.append(ciphertexts)

                # 3.调用__verify_re_encryption验证重加密结果
                verification_results = []
                id_order = ret[3]
                for i in range(1, len(ciphertext_list)):
                    valid = self.__verify_re_encryption(
                        id_order[i - 1], ciphertext_list[i - 1], ciphertext_list[i]
                    )
                    verification_results.append(valid)
                log.debug(
                    f"【Requester】ZKP {sub_task_id} verification results {verification_results}"
                )

                # 4.调用__answer_collection解密重加密结果并保存
                self.__answer_collection(sub_task_id, ciphertext_list[0])

    def __handle_SubTaskAnswerSubmitted(self, raw_event, args):
        self.task_queue.put(("SubTaskAnswerSubmitted", args))

    def __handle_SubTaskEncryptionCompleted(self, raw_event, args):
        self.task_queue.put(("SubTaskEncryptionCompleted", args))

    def __verify_re_encryption(self, randomizer_id, ciphertext, new_ciphertext):
        def handler(conn):
            # 0.发送对特定重加密结果的验证请求
            commit = self._generate_commitment(new_ciphertext)
            sendLine(conn, commit)

            # 1.接收证明者发送的e'
            e_prime_str = recvLine(conn)
            e_prime = self.encryptor.createCiphertext(e_prime_str)

            # 2.验证者发送一个挑战c
            c = self.encryptor.proveReEncrypt_2()
            sendLine(conn, c)

            # 3.接收证明者返回的beta，并返回验证结果
            beta = recvLine(conn)
            conn.close()
            return e_prime, c, beta

        randomizer_port, randomizer_ip = self.randomizer_list[randomizer_id]
        e_prime, c, beta = connect_to(handler, randomizer_port, randomizer_ip)
        valid = self.encryptor.verifyReEncrypt(
            new_ciphertext, ciphertext, e_prime, c, beta
        )
        return valid

    # 解密提交并保存，供后续奖励发放模块处理
    def __answer_collection(self, subTaskId, ciphertexts):
        # 1.使用自己的私钥解密submissions中的回答
        ans_content = self.encryptor.decrypt(ciphertexts)
        answer_obj = self.task.ANSWER_CLS().from_encoding(ans_content)

        # 2.将解密结果放入队列，供后续处理
        self.answers_of_subtasks.put((subTaskId, answer_obj))
        log.debug(f"【Requester】results {subTaskId} decrypted")

    # 奖励发放器守护进程，评估结果并处理奖励发放相关事宜
    # TODO：完成随机延迟的奖励发放
    def __reward_dist_daemon(self):
        # 1.评估提交的正确性并保存正确的提交
        # 2.给诚实的参与者计算奖励
        # 3.使用随机延迟奖励发放算法给参与者发放奖励
        received_task_num = 0
        answers = []
        while True:
            received_task_num += 1
            if received_task_num > self.task.subtasks_num:
                break
            subTaskId, answer_obj = self.answers_of_subtasks.get()
            answers.append(answer_obj)

        indexes, answer = self.task.evaluation(answers)
        log.info(f"【Requester】final answer generated {answer} ")
        self.emit_event("TASK_END", self.encryptor.totaltime)


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

    randomizer_list = {
        "0xe7B44655990857181d5fCfaaAe3471B2B911CaB4": (10000, "localhost")
    }

    TASK_PULL_PORT = 11111
    from task.simple_task import SimpleTask

    task = SimpleTask("This is a simple task", list(range(100)), 10)

    # requester对象初始化
    requester = Requester(
        ipfs_url,
        web3_url,
        contract_address,
        contract_abi,
        "tmp/keypairs/pk.pkl",
        "tmp/keypairs/sk.pkl",
        randomizer_list,
        task,
        TASK_PULL_PORT,
    )
    # file = requester.fetch_ipfs("Qmc961Q9K1ThVSkemw9tSLPNZCKLhBcpT38b6RkBdF18CC")
    # ciphertext = requester.encryptor.createCiphertext(file)

    # file = requester.fetch_ipfs("QmS7yQ99Tdr3wZLfYjuBtwY6autHG21Lbcjmktuv4VGoCE")
    # ciphertext_new = requester.encryptor.createCiphertext(file)

    # print(requester.verify_re_encryption("0xe7B44655990857181d5fCfaaAe3471B2B911CaB4",ciphertext,ciphertext_new))

    # 启动异步监听
    requester.daemon_start()

    # 模拟前一顺位的Randomizers提交重加密结果
    # account = "0xe7B44655990857181d5fCfaaAe3471B2B911CaB4"
    # private_key = "0x5ddfd9257c762b7b23f65844dac651b8469c01b1b14291ffde2a9017d15453c5"
    # randomizer.contract_interface.send_transaction(
    #     "receiveInteger", 123
    # )

    # 异步监听时可以做其他事
    time.sleep(1000000)
