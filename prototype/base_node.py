# 添加当前路径至解释器，确保单元测试时可正常import其它文件
import os
import sys
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 基于顶层包的import
from contract import ContractInterface
from utils.elgamal_encryptor import ElgamalEncryptor
import ipfshttpclient

# 系统库
import uuid
import os
import hashlib
import pickle


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
        return pickle.loads(file_content)

    def submit_ipfs(self, object):
        # 向分布式文件存储服务上传python对象
        uuid.uuid1()
        tmp_file = f"tmp/{uuid.uuid1()}"
        with open(tmp_file, "wb") as f:
            f.write(pickle.dumps(object))
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