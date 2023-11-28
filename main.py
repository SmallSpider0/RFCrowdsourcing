from prototype.utils.config import Config
from prototype.requester import Requester
from prototype.submitter import Submitter
from prototype.randomizer import Randomizer
from prototype.task.cifar10_tagging import CIFAR10Task
from prototype.task.simple_task import SimpleTask
from prototype.utils.tools import deploy_smart_contract

# 系统库
import json
import random

# 大规模测试
# SUBMITTER_NUM = 100  # 提交者数量
# RANDOMIZER_NUM = 20  # 重加密者数量
# SUBTASK_NUM = 100  # 子任务数量
# RE_ENC_NUM = 3  # 子任务需要的重加密次数

# 标准测试
SUBMITTER_NUM = 5 #提交者数量
RANDOMIZER_NUM = 10 #重加密者数量
SUBTASK_NUM = 20 #子任务数量
RE_ENC_NUM = 2 #子任务需要的重加密次数

# 最小系统
# SUBMITTER_NUM = 1 #提交者数量
# RANDOMIZER_NUM = 1 #重加密者数量
# SUBTASK_NUM = 10 #子任务数量
# RE_ENC_NUM = 1 #子任务需要的重加密次数


config = Config()
ipfs_url = config.get_config("app").get("ipfs_url")
web3_url = config.get_config("app").get("web3_url")

# Requester提供任务获取的接口
REQUESTER_TASK_PULL_IP = "localhost"
REQUESTER_TASK_PULL_PORT = config.get_config("requester").get("task_pull_port")

# 各Randomizer提供ZKP验证的接口
RANDOMIZER_PROVING_SERVER_PORT_BASE = config.get_config("randomizer").get("proving_server_port_base")
randomizer_list = []
for id in range(RANDOMIZER_NUM):
    randomizer_list.append((RANDOMIZER_PROVING_SERVER_PORT_BASE + id, "localhost"))

# ------------------
# 1.给各节点分配区块链账户
# ------------------
accounts_path = config.get_config("test").get("account_path")
with open(accounts_path, "r") as f:
    accounts = json.load(f)
random.shuffle(accounts)

# Requester的地址和私钥
requester_account = (accounts[0][0], accounts[0][1])

# Submitter的地址和私钥
submitter_accounts = []
for i in range(2, SUBMITTER_NUM + 2):
    account = accounts[i - 1][0]
    private_key = accounts[i - 1][1]
    submitter_accounts.append((account, private_key))

# Randomizer的地址和私钥
randomizer_accounts = []
for i in range(SUBMITTER_NUM + 2, SUBMITTER_NUM + RANDOMIZER_NUM + 2):
    account = accounts[i - 1][0]
    private_key = accounts[i - 1][1]
    randomizer_accounts.append((account, private_key))

# ------------------
# 2.合约部署
# ------------------
contract_address, contract_abi = deploy_smart_contract(
    "CrowdsourcingContract",
    web3_url,
    requester_account[0],
    requester_account[1],
    SUBTASK_NUM,
    RE_ENC_NUM,
)

# ------------------
# 3.初始化 requester和任务
# ------------------
# task = SimpleTask("This is a simple task", list(range(1, 1001)), SUBTASK_NUM)
task = CIFAR10Task("CIFAR10 tagging", SUBTASK_NUM)
requester = Requester(
    ipfs_url,
    web3_url,
    contract_address,
    contract_abi,
    requester_account[0],
    requester_account[1],
    "tmp/keypairs/pk.pkl",
    "tmp/keypairs/sk.pkl",
    randomizer_list,
    task,
    REQUESTER_TASK_PULL_PORT,
)

# ------------------
# 4.初始化 randomizer
# ------------------
randomizers = []
for id in range(RANDOMIZER_NUM):
    randomizers.append(
        Randomizer(
            ipfs_url,
            web3_url,
            contract_address,
            contract_abi,
            randomizer_accounts[id][0],
            randomizer_accounts[id][1],
            "tmp/keypairs/pk.pkl",
            RANDOMIZER_PROVING_SERVER_PORT_BASE + id,
            id,
        )
    )

# ------------------
# 5.初始化 submitter
# ------------------
submitters = []
for id in range(SUBMITTER_NUM):
    submitters.append(
        Submitter(
            ipfs_url,
            web3_url,
            contract_address,
            contract_abi,
            submitter_accounts[id][0],
            submitter_accounts[id][1],
            "tmp/keypairs/pk.pkl",
            REQUESTER_TASK_PULL_IP,
            REQUESTER_TASK_PULL_PORT,
            task.SUBTASK_CLS,
            id,
        )
    )

# ------------------
# 6.启用所有节点
# ------------------

# 启动
requester.run()

# 启动
for randomizer in randomizers:
    randomizer.run()

# 等待注册交易执行完成
import time
time.sleep(20)

# 启动
for submitter in submitters:
    submitter.run()