from prototype.contract import ContractInterface
from prototype.utils.config import Config

# 系统库
import json
import hashlib

config = Config()

# 初始化合约接口
provider_url = config.get_config("app").get("web3_url")
contract_address = config.get_config("smart_contract").get("address")
contract_abi_path = config.get_config("smart_contract").get("abi_path")
with open(contract_abi_path) as file:
    contract_abi = json.loads(file.read())  # 智能合约ABI
contract = ContractInterface(provider_url, contract_address, contract_abi)

# Submitter的地址和私钥
accounts = config.get_config("test")
submitter_account = accounts.get("account1")
submitter_private_key = accounts.get("sk1")

# Randomizer的地址和私钥
randomizer_accounts = [
    (accounts.get("account2"), accounts.get("sk2")),
    (accounts.get("account3"), accounts.get("sk3")),
    (accounts.get("account4"), accounts.get("sk4")),
    (accounts.get("account5"), accounts.get("sk5")),
]

def main():
    # 重置合约状态（仅用于测试）
    tx_hash = contract.send_transaction(
            "reset",
            submitter_account,
            submitter_private_key,
    )
    print(f"Contracet successuflly Resetted: {tx_hash.hex()}")

    # 模拟Randomizer注册
    for account, private_key in randomizer_accounts:
        tx_hash = contract.send_transaction("registerRandomizer", account, private_key)
        print(f"Randomizer Registration Tx Hash: {tx_hash.hex()}")

    # 模拟Submitter提交子任务答案
    for i in range(4):  # 四个子任务
        commit = generate_commit()  # 生成commit的逻辑
        filehash = generate_filehash()
        vrf_output, vrf_proof = generate_vrf(submitter_account)  # 生成VRF输出和证明的逻辑
        tx_hash = contract.send_transaction(
            "submitSubTaskAnswer",
            submitter_account,
            submitter_private_key,
            i,
            commit,
            filehash,
            vrf_output,
            vrf_proof,
        )
        print(f"SubTask {i} Answer Submission Tx Hash: {tx_hash.hex()}")

    # 模拟Randomizer进行重加密
    for sub_task_id in range(4):
        encrypt_in_order(sub_task_id)

    # 获取子任务最终结果
    for i in range(4):
        final_result = contract.call_function("getSubTaskFinalResult", i)
        print(f"Final result for SubTask {i}: {final_result}")

def get_selected_randomizers_order(sub_task_id):
    return contract.call_function("getSelectedRandomizers", sub_task_id)

def encrypt_in_order(sub_task_id):
    # 获取子任务的Randomizer顺序
    # 假设我们有一种方法来获取这个顺序
    selected_randomizers = get_selected_randomizers_order(sub_task_id)

    for randomizer_id in selected_randomizers:
        randomizer_account, randomizer_private_key = randomizer_accounts[randomizer_id]
        new_commit = generate_commit()  # 生成新的commit
        new_filehash = generate_filehash()
        tx_hash = contract.send_transaction(
            "encryptSubTaskAnswer",
            randomizer_account,
            randomizer_private_key,
            sub_task_id,
            new_commit,
            new_filehash,
        )
        print(
            f"SubTask {sub_task_id} Encryption by {randomizer_account} Tx Hash: {tx_hash.hex()}"
        )


def generate_commit():
    # 生成commit的逻辑
    return "0x6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b"


def generate_filehash():
    # 生成commit的逻辑
    return "Qmc961Q9K1ThVSkemw9tSLPNZCKLhBcpT38b6RkBdF18CC"


from Crypto.Hash import keccak
def generate_vrf(account_address):
    # 使用keccak256生成VRF输出
    k = keccak.new(digest_bits=256)
    k.update(account_address.encode())
    vrf_output = k.digest()

    # 将VRF输出转换为整数
    vrf_output_int = int.from_bytes(vrf_output, byteorder='big') % (2**256)

    # 生成预期的VRF证据 - 使用账户地址和VRF输出整数
    k = keccak.new(digest_bits=256)
    k.update(account_address.encode() + vrf_output)
    expected_proof = k.digest()

    return (vrf_output_int, expected_proof)



if __name__ == "__main__":
    main()
