import pickle
from utils.network import listen_on_port, connect_to, sendLine, recvLine
from base_node import BaseNode
import threading


# TODO：需要实现重加密证明的交互式验证（与requester交互）参考论文开源项目 实现多轮交互
class Randomizer(BaseNode):
    def __init__(
        self,
        ipfs_url,
        provider_url,
        contract_address,
        contract_abi,
        requester_pk_file,
        proving_server_port,
        id=0,
    ):
        # 其它参数初始化
        self.proving_server_port = proving_server_port
        self.id = id
        self.old_alpha_primes = {}

        # 基类初始化
        super().__init__(
            ipfs_url, provider_url, contract_address, contract_abi, requester_pk_file
        )

    def daemon_start(self):
        # 1.启动事件监听器
        # TODO:智能合约完成后 修改为监听正确的事件
        self.contract_interface.listen_for_events(
            "IntegerReceived(uint256)", self.__handle_event, True
        )

        # 2.启动重加密ZKP验证服务
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
        sendLine(conn, e_prime)

        # 2.接收验证者发送的挑战c，并构造和发送beta
        c = recvLine(conn)
        beta = self.encryptor.proveReEncrypt_3(c, alpha_prime, alpha_tmp)
        sendLine(conn, beta)

        print('successed handled:', commit)

    def __handle_event(self, raw_event, args):
        # 1.监听event，等待前一顺位的Randomizers提交重加密结果
        print(args)
        # TODO：实现等待的逻辑

        # 2.根据智能合约中存储的pointer，从分布式文件存储服务下载回答密文
        # TODO：修改为从event的参数中获取文件指针
        file = pickle.loads(
            self.fetch_ipfs("QmXokoNNjhwggF5gLZSX5RhQbFSKchUZfBQY6zkaLnEmnc")
        )
        ciphertext = self.encryptor.createCiphertext(file)

        # 3.进行重加密
        # TODO:测试完成后改回随机生成
        # alpha_prime = self.encryptor.genAlpha()
        alpha_prime = 2333
        new_ciphertext = self.encryptor.reEncrypt(ciphertext, alpha_prime)

        # 4.提交重加密结果
        file_hash = self.submit_ipfs(pickle.dumps(str(new_ciphertext)))
        print(file_hash)

        # 5.将重加密结果的承诺和文件指针上传至区块链
        # TODO：实现该逻辑

        # 6.在本地保存一份结果 用于后续验证
        commit = self._generate_commitment(new_ciphertext)
        self.old_alpha_primes[commit] = alpha_prime
        print(commit)


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

    # randomizer对象初始化
    randomizer = Randomizer(
        ipfs_url, web3_url, contract_address, contract_abi, "tmp/keypairs/pk.pkl", 10000
    )

    # 启动守护程序
    randomizer.daemon_start()

    # 模拟前一顺位的Randomizers提交重加密结果
    # account = "0xe7B44655990857181d5fCfaaAe3471B2B911CaB4"
    # private_key = "0x5ddfd9257c762b7b23f65844dac651b8469c01b1b14291ffde2a9017d15453c5"
    # randomizer.contract_interface.send_transaction(
    #     "receiveInteger", account, private_key, 123
    # )

    # 异步监听时可以做其他事
    time.sleep(1000000)
