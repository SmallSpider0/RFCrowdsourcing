import uuid
import os
import hashlib
from web3 import Web3
from contract import ContractInterface
from utils.elgamalEncryptor import ElgamalEncryptor

try:
    from . import ipfshttpclient  # 尝试相对导入
except ImportError:
    import ipfshttpclient  # 回退到绝对导入

# 节点的基类（Requester、Randomizer、Submitter）
class BaseNode:
    def __init__(
        self,
        ipfs_url,
        provider_url,
        contract_address,
        contract_abi,
        requester_pk_file,
        requester_sk_file = None,
    ):
        # 初始化区块链交互模块
        self.contract_interface = ContractInterface(
            provider_url, contract_address, contract_abi
        )

        # 初始化密码学模块
        self.encryptor = ElgamalEncryptor(public_key_file=requester_pk_file, private_key_file = requester_sk_file)

        # 初始化IPFS交互模块
        self.ipfs_client = ipfshttpclient.connect(ipfs_url)

    def fetch_ipfs(self, file_pointer):
        # 从分布式文件存储服务获取文件
        download_path = "tmp/IPFS_downloads"
        self.ipfs_client.get(file_pointer, download_path)
        with open(f"{download_path}/{file_pointer}", "rb") as f:
            file_content = f.read()
        return file_content

    def submit_ipfs(self, binary_content):
        # 向分布式文件存储服务上传文件
        uuid.uuid1()
        tmp_file = f"tmp/{uuid.uuid1()}"
        with open(tmp_file, "wb") as f:
            f.write(binary_content)
        file_hash = self.ipfs_client.add(tmp_file)["Hash"]
        # 删除临时文件
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
        return file_hash
    
    # 生成数据的承诺，这里用sha256哈希作为例子
    def _generate_commitment(self, *args):
        tmp = ""
        for arg in args:
            tmp+=str(arg)
        # 创建哈希对象
        hash_obj = hashlib.new("sha256")
        # 更新哈希对象，这里需要确保数据是字节串
        hash_obj.update(tmp.encode())
        # 获取十六进制格式的哈希值
        return hash_obj.hexdigest()