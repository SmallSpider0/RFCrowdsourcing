from utils.network import listen_on_port, connect_to, sendLine, recvLine
import threading
from base_node import BaseNode


class Requester(BaseNode):
    # 构造函数
    def __init__(
        self,
        ipfs_url,
        provider_url,
        contract_address,
        contract_abi,
        requester_pk_file,
        requester_sk_file,
        randomizer_list,
    ):
        # 其它参数初始化
        self.randomizer_list = randomizer_list

        # 基类初始化
        super().__init__(
            ipfs_url,
            provider_url,
            contract_address,
            contract_abi,
            requester_pk_file,
            requester_sk_file,
        )

    # 启动守护程序
    def daemon_start(self):
        # 1.启动监听器，监听特定事件
        # TODO:智能合约完成后 修改为监听正确的事件
        self.contract_interface.listen_for_events(
            "IntegerReceived(uint256)", self.__handle_event, True
        )

        # 2.启动奖励发放器，执行随机延迟的奖励发放

        # 3.启动重加密ZKP验证服务
        # TODO:修改为请求Randomizers验证
        # return connect_to(handler, self.requester_port, self.requester_ip)

    def listen_for_requests(self, is_async=False):
        # IntegerReceived(uint256)仅作测试用
        self.contract_interface.listen_for_events(
            "IntegerReceived(uint256)", self.__handle_event, is_async
        )

    def __handle_event(self, raw_event, args):
        # 1.监听event，等待最后顺位的Randomizers提交重加密结果
        # TODO：实现
        print(args)

        # 2.根据智能合约中存储的pointer，从分布式文件存储服务下载重加密结果
        # TODO：改成从智能合约和IPFS获取
        file = pickle.loads(
            randomizer.fetch_ipfs("QmXokoNNjhwggF5gLZSX5RhQbFSKchUZfBQY6zkaLnEmnc")
        )
        ciphertext = randomizer.encryptor.createCiphertext(file)

        file = pickle.loads(
            randomizer.fetch_ipfs("QmQnyNdwiLzE6LAQBXcX6ZvAk9gn6tpM38rz1U4JjeowjP")
        )
        ciphertext_new = randomizer.encryptor.createCiphertext(file)
        data = [
            {
                "address": "0xe7B44655990857181d5fCfaaAe3471B2B911CaB4",
                "ciphertext": ciphertext,
                "new_ciphertext": ciphertext_new,
            },
        ]

        # 3.调用__verify_re_encryption验证重加密结果
        rets = []
        for item in data:
            valid = self.verify_re_encryption(
                item["address"], item["ciphertext"], item["new_ciphertext"]
            )
            rets.append(valid)
        print(rets)

        # 4.调用__answer_collection解密重加密结果并保存
        # TODO：实现
        # self.__answer_collection()

    # TODO:思考如何获取密文和重加密结果
    def verify_re_encryption(self, randomizer_addr, ciphertext, new_ciphertext):
        commit = self._generate_commitment(new_ciphertext)

        def handler(conn):
            # 0.发送对特定重加密结果的验证请求
            sendLine(conn, commit)
            # 1.接收证明者发送的e'
            e_prime = recvLine(conn)

            # 2.验证者发送一个挑战c
            c = self.encryptor.proveReEncrypt_2()
            sendLine(conn, c)

            # 3.接收证明者返回的beta，并返回验证结果
            beta = recvLine(conn)
            conn.close()
            return e_prime, c, beta

        randomizer_port, randomizer_ip = self.randomizer_list[randomizer_addr]
        e_prime, c, beta = connect_to(handler, randomizer_port, randomizer_ip)
        valid = self.encryptor.verifyReEncrypt(
            new_ciphertext, ciphertext, e_prime, c, beta
        )
        return valid

    # 【内部函数】解密提交并保存，供后续奖励发放模块处理
    def __answer_collection(self, submissions):
        # 1.使用自己的私钥解密submissions中的回答
        # 2.将解密结果放入队列，供后续处理
        pass

    # 【内部函数】由奖励发放器调用，评估结果并处理奖励发放相关事宜
    def __evaluation(self, submissions):
        # 1.评估提交的正确性并保存正确的提交
        # 2.给诚实的参与者计算奖励
        # 3.使用随机延迟奖励发放算法给参与者发放奖励
        pass


if __name__ == "__main__":
    # 导入测试所需的包
    import json
    import time
    import pickle

    # 测试参数定义
    ipfs_url = "/ip4/127.0.0.1/tcp/5001"
    web3_url = "http://127.0.0.1:8545"
    contract_address = "0xd7357e2A30760f94971bC8Eb10f5dd0D1cFdB6Ae"
    with open("solidity/contract-abi.json") as file:
        contract_abi = json.loads(file.read())  # 智能合约ABI

    randomizer_list = {
        "0xe7B44655990857181d5fCfaaAe3471B2B911CaB4": (10000, "localhost")
    }

    # requester对象初始化
    randomizer = Requester(
        ipfs_url,
        web3_url,
        contract_address,
        contract_abi,
        "tmp/keypairs/pk.pkl",
        "tmp/keypairs/sk.pkl",
        randomizer_list,
    )
    # file = pickle.loads(
    #     randomizer.fetch_ipfs("QmXokoNNjhwggF5gLZSX5RhQbFSKchUZfBQY6zkaLnEmnc")
    # )
    # ciphertext = randomizer.encryptor.createCiphertext(file)

    # file = pickle.loads(
    #     randomizer.fetch_ipfs("QmQnyNdwiLzE6LAQBXcX6ZvAk9gn6tpM38rz1U4JjeowjP")
    # )
    # ciphertext_new = randomizer.encryptor.createCiphertext(file)

    # print(randomizer.verify_re_encryption("0xe7B44655990857181d5fCfaaAe3471B2B911CaB4",ciphertext,ciphertext_new))

    # 启动异步监听
    randomizer.listen_for_requests(True)

    # 模拟前一顺位的Randomizers提交重加密结果
    account = "0xe7B44655990857181d5fCfaaAe3471B2B911CaB4"
    private_key = "0x5ddfd9257c762b7b23f65844dac651b8469c01b1b14291ffde2a9017d15453c5"
    randomizer.contract_interface.send_transaction(
        "receiveInteger", account, private_key, 123
    )

    # 异步监听时可以做其他事
    time.sleep(1000000)
