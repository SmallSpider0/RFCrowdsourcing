from solcx import compile_standard
import solcx
from web3 import Web3
from web3.middleware import geth_poa_middleware
import re
import json
import paramiko

def ssh_command(server, command):
    # 创建 SSHClient 实例
    ssh = paramiko.SSHClient()
    # 自动添加策略，保存服务器的主机名和密钥信息
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # 连接到服务器
        ssh.connect(server["ip"], 22, server["user"], server["password"])

        # 执行命令
        stdin, stdout, stderr = ssh.exec_command(command)

        # 读取输出
        result = stdout.read()
        if not result:
            result = stderr.read()
        return result.decode()

    finally:
        # 关闭连接
        ssh.close()

def split_array(arr, n):
    """将数组拆分为最多n个相同大小的分片，最后一个分片大小可以不同。

    :param arr: 要拆分的数组。
    :param n: 分片的数量。
    :return: 包含分片的列表。
    """
    # 计算每个分片的大致大小
    size = len(arr) // n
    # 如果数组大小不能被n整除，最后一个分片需要增加一个元素
    size += 1 if len(arr) % n > 0 else 0

    # 生成分片
    return [arr[i : i + size] for i in range(0, len(arr), size)]


def find_next_element(array, element):
    """Find the next element in an array relative to a given element.

    :param array (list): The list in which to search for the next element.
    :param element (any): The element whose successor is to be found.
    :return: The element immediately following the given element in the array.
    """
    try:
        index = array.index(element)
        if index < len(array) - 1:
            return array[index + 1]
        else:
            return None  # 或其他适当的值，表示没有下一个元素
    except ValueError:
        return None  # 元素不在数组中

def process_accounts(inputfile, outputfile):
    """将Ganache导出的测试账户文件转成本项目所需的格式"""
    with open(inputfile, 'r') as f:
        keys = json.load(f)

    output = []
    for k,v in keys["private_keys"].items():
        output.append((Web3.to_checksum_address(k),v))

    with open(outputfile, 'w') as f:
        f.write(json.dumps(output))

def deploy_smart_contract(contract_name, web3_url, account, private_key, *args):
    # 1.读取solidity文件夹中合约源码并编译 得到字节码和ABI
    file_path = "solidity/"
    with open(file_path + contract_name + '.sol', "r") as file:
        source = file.read()

    pattern = r'pragma\s+solidity\s+\^([0-9]+\.[0-9]+\.[0-9]+);'
    match = re.search(pattern, source)
    version = match.group(1)
    # 安装并切换到指定版本的Solidity编译器
    solcx.install_solc(version)
    solcx.set_solc_version(version)

    compiled_sol = compile_standard(
        {
            "language": "Solidity",
            "sources": {file_path: {"content": source}},
            "settings": {
                "outputSelection": {"*": {"*": ["metadata", "evm.bytecode", "abi"]}}
            },
        }
    )
    contract_interface = compiled_sol["contracts"][file_path][contract_name]
    bytecode = contract_interface["evm"]["bytecode"]["object"]

    # abi写入文件
    with open(file_path+contract_name+'.json', 'w') as f:
        f.write(json.dumps(contract_interface["abi"], indent=4))

    # 连接私有链节点
    w3 = Web3(Web3.HTTPProvider(web3_url))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0) # 兼容POA

    # 创建合约类
    Contract = w3.eth.contract(abi=contract_interface["abi"], bytecode=bytecode)

    # 构建部署事务
    transaction = Contract.constructor(*args).build_transaction(
        {
            "from": account,
            "gas": 5000000,
            "gasPrice": 0,
            "nonce": w3.eth.get_transaction_count(
                account
            ),
        }
    )

    # 使用账号0xd815AE3BAfA1A7e3B1b1Ac096152c56b1a9BA97d的私钥签署交易
    signed_txn = w3.eth.account.sign_transaction(
        transaction,
        private_key,
    )
    txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    # 获取交易收据以确认
    tx_receipt = w3.eth.wait_for_transaction_receipt(txn_hash)

    print(f"deply {contract_name} gasUsed", tx_receipt["gasUsed"])

    # 获取合约地址
    return (tx_receipt["contractAddress"], contract_interface["abi"])