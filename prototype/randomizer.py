from web3 import Web3
from contract import ContractInterface
from utils.elgamalEncryptor import ElgamalEncryptor
from utils.network import listen_on_port, connect_to, sendLine, recvLine
import pickle

try:
    from . import ipfshttpclient  # 尝试相对导入
except ImportError:
    import ipfshttpclient  # 回退到绝对导入


# TODO：需要实现重加密证明的交互式验证（与requester交互）参考论文开源项目 实现多轮交互
class Randomizer:
    def __init__(
        self,
        ipfs_url,
        provider_url,
        contract_address,
        contract_abi,
        requester_pk_file,
        requester_ip,
        requester_port,
        id=0,
    ):
        # 其它参数初始化
        self.requester_ip = requester_ip
        self.requester_port = requester_port
        self.id = id

        # 初始化区块链交互模块
        self.web3 = Web3(Web3.HTTPProvider(web3_url))
        self.contract_interface = ContractInterface(
            provider_url, contract_address, contract_abi
        )

        # 初始化密码学模块
        self.encryptor = ElgamalEncryptor(public_key_file=requester_pk_file)

        # 初始化IPFS交互模块
        self.ipfs_client = ipfshttpclient.connect(ipfs_url)

    def listen_for_requests(self, is_async=False):
        # IntegerReceived(uint256)仅作测试用
        self.contract_interface.listen_for_events(
            "IntegerReceived(uint256)", self.__handle_event, is_async
        )

    def prove(self, alpha_prime):
        # 与Requester交互式验证重加密ZKP
        # 证明ciphertext使用alpha_prime重加密得到new_ciphertext
        def handler(conn):
            # 1.证明者发送e_prime，并保存alpha_tmp
            e_prime, alpha_tmp = self.encryptor.proveReEncrypt_1()
            sendLine(conn, str(e_prime))
            # 2.接收验证者发送的挑战c，并构造和发送beta
            c = recvLine(conn)
            beta = self.encryptor.proveReEncrypt_3(c, alpha_prime, alpha_tmp)
            sendLine(conn, str(beta))
            # 3.接收验证结果（是否通过）
            ret = recvLine(conn)
            return ret

        return connect_to(handler, self.requester_port, self.requester_ip)

    def __handle_event(self, raw_event, args):
        # 1.监听event，等待前一顺位的Randomizers提交重加密结果
        print(args)
        # TODO：实现等待的逻辑

        # 2.根据智能合约中存储的pointer，从分布式文件存储服务下载回答密文
        # TODO：修改为从event的参数中获取文件指针
        file = pickle.loads(
            self.__fetch_ipfs("QmR7sAkVj6SVPL7dzCUU5bJZbPRNB18WWwK1yuDsTGFKha")
        )
        ciphertext = self.encryptor.createCiphertext(file)

        # 3.进行重加密
        alpha_prime = self.encryptor.genAlpha()
        new_ciphertext = self.encryptor.reEncrypt(ciphertext, alpha_prime)

        # 4.提交重加密结果
        file_hash = self.__submit_ipfs(pickle.dumps(new_ciphertext))
        print(file_hash)

        # 5.将重加密结果的承诺和文件指针上传至区块链
        # TODO：实现该逻辑

    def __fetch_ipfs(self, file_pointer):
        # 从分布式文件存储服务获取文件
        download_path = "tmp/IPFS_downloads"
        self.ipfs_client.get(file_pointer, download_path)
        with open(f"{download_path}/{file_pointer}", "rb") as f:
            file_content = f.read()
        return file_content

    def __submit_ipfs(self, binary_content):
        # 向分布式文件存储服务上传文件
        tmp_file = f"tmp/{self.id}-ipfs_tmp"
        with open(tmp_file, "wb") as f:
            f.write(binary_content)
        file_hash = self.ipfs_client.add(tmp_file)["Hash"]
        return file_hash


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
        ipfs_url, web3_url, contract_address, contract_abi, "tmp/keypairs/pk.pkl"
    )

    # 启动异步监听
    randomizer.listen_for_requests(True)

    # 模拟前一顺位的Randomizers提交重加密结果
    account = "0xe7B44655990857181d5fCfaaAe3471B2B911CaB4"
    private_key = "0x5ddfd9257c762b7b23f65844dac651b8469c01b1b14291ffde2a9017d15453c5"
    randomizer.contract_interface.send_transaction(
        "receiveInteger", account, private_key, 123
    )

    # 异步监听时可以做其他事
    for _ in range(3):
        time.sleep(1)
