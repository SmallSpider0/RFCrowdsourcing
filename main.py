from prototype.utils.config import Config

config = Config()


# 外部服务相关参数
ipfs_url = config.get_config("app").get("ipfs_url")
web3_url = config.get_config("app").get("web3_url")
# contract_address = config.get_config("smart_contract").get("address")
# contract_abi_path = config.get_config("smart_contract").get("abi_path")

# 给节点分配秘钥

SUBMITTER_NUM = 3 #提交者数量
RANDOMIZER_NUM = 5 #重加密者数量
SUBTASK_NUM = 10 #子任务数量
RE_ENC_NUM = 3 #子任务需要的重加密次数

accounts = config.get_config("test")

# Requester的地址和私钥
requester_account = (accounts.get("account1"), accounts.get("sk1"))

# Submitter的地址和私钥
submitter_accounts = []
for i in range(2, SUBMITTER_NUM + 2):
    account = accounts.get(f"account{i}")
    private_key = accounts.get(f"sk{i}")
    submitter_accounts.append((account, private_key))


# Randomizer的地址和私钥
randomizer_accounts = []
for i in range(SUBMITTER_NUM + 2, SUBMITTER_NUM + RANDOMIZER_NUM + 2):
    account = accounts.get(f"account{i}")
    private_key = accounts.get(f"sk{i}")
    randomizer_accounts.append((account, private_key))

REQUESTER_TASK_PULL_IP = "localhost"
REQUESTER_TASK_PULL_PORT = 10000
RANDOMIZER_PROVING_SERVER_PORT_BASE = 11000


# 合约部署
from prototype.utils.tools import deploy_smart_contract

contract_address, contract_abi = deploy_smart_contract(
    "CrowdsourcingContract", web3_url, requester_account[0], requester_account[1], SUBTASK_NUM, RE_ENC_NUM
)

# with open(contract_abi_path) as file:
#     contract_abi = json.loads(file.read())

# ------------------
# 1.初始化 requester
# ------------------
from prototype.requester import Requester
from prototype.task.simple_task import SimpleTask

task = SimpleTask("This is a simple task", list(range(100)), SUBTASK_NUM)

randomizer_list = []
for id in range(RANDOMIZER_NUM):
    randomizer_list.append((RANDOMIZER_PROVING_SERVER_PORT_BASE + id, "localhost"))

# requester对象初始化
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
# 2.初始化 randomizer
# ------------------
from prototype.randomizer import Randomizer

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
# 3.初始化 submitter
# ------------------
from prototype.task.simple_task import SimpleSubtask
from prototype.submitter import Submitter


# submitter对象初始化
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
            SimpleSubtask,
            id,
        )
    )


# 启动
requester.daemon_start()

# 启动
for randomizer in randomizers:
    randomizer.daemon_start()

# 启动
for submitter in submitters:
    submitter.daemon_start()
