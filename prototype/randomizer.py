from web3 import Web3
from contract import ContractInterface
from utils.elgamalEncryptor import ElgamalEncryptor

class Randomizer:
    # 输入Requester的公钥
    def __init__(self, provider_url, contract_address, contract_abi, requester_pk_file , id = 0):
        self.id = id
        self.web3 = Web3(Web3.HTTPProvider(web3_url))
        self.contract_interface = ContractInterface(provider_url, contract_address, contract_abi)
        self.elgamal_encryptor = ElgamalEncryptor(public_key_file=requester_pk_file)

    def listen_for_requests(self):
        self.contract_interface.listen_for_events("IntegerReceived(uint256)", self.handle_event)

    def handle_event(self, raw_event, args):
        # 1.监听event，等待前一顺位的Randomizers提交重加密结果
        # 2.根据智能合约中存储的pointer，从分布式文件存储服务下载回答密文
        # 3.调用__re_encryption进行重加密
        # 4.调用__submit_results提交重加密结果
        print(args)

    def fetch_ciphertext(self, file_pointer):
        # 实现从分布式文件存储服务获取密文的逻辑
        # 您需要填充这个方法的内容
        pass

    def perform_reencryption(self, ciphertext):
        # 使用elgamal_encryptor对ciphertext进行重加密
        # 并生成NIZKP（您将实现该逻辑）
        reencrypted_ciphertext = self.elgamal_encryptor.re_encrypt(ciphertext)
        nizkp = self.elgamal_encryptor.generate_nizkp()
        return reencrypted_ciphertext, nizkp

    def upload_results(self, reencrypted_ciphertext, nizkp):
        # 将重加密结果和NIZKP上传到分布式数据库
        # 获取新的文件指针并计算承诺，上传到区块链
        # 您需要根据您的分布式文件存储和区块链系统实现此逻辑
        pass




if __name__=="__main__":
    # 导入测试所需的包
    import json

    # 测试参数定义
    web3_url = "http://127.0.0.1:8545"
    contract_address = "0xd7357e2A30760f94971bC8Eb10f5dd0D1cFdB6Ae" 
    with open("solidity/contract-abi.json") as file:
        contract_abi = json.loads(file.read()) # 智能合约ABI

    # randomizer对象初始化
    randomizer = Randomizer(web3_url, contract_address, contract_abi, 'tmp/keypairs/requester_pk.pkl')

    # 启动监听
    randomizer.listen_for_requests()