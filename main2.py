# 导入测试所需的包
from prototype.utils.config import Config

# 系统库
import json
import time

config = Config()

# 测试参数定义
ipfs_url = config.get_config("app").get("ipfs_url")
web3_url = config.get_config("app").get("web3_url")
contract_address = config.get_config("smart_contract").get("address")
contract_abi_path = config.get_config("smart_contract").get("abi_path")
with open(contract_abi_path) as file:
    contract_abi = json.loads(file.read())

# ------------------
# 1.初始化 submitter
# ------------------
from prototype.task.simple_task import SimpleSubtask
from prototype.submitter import Submitter

account = config.get_config("test").get("account")
private_key = config.get_config("test").get("private_key")

TASK_PULL_IP = "localhost"
TASK_PULL_PORT = 11111
# submitter对象初始化
submitter = Submitter(
    ipfs_url,
    web3_url,
    contract_address,
    contract_abi,
    "tmp/keypairs/pk.pkl",
    TASK_PULL_IP,
    TASK_PULL_PORT,
    account,
    private_key,
    SimpleSubtask,
)


# ------------------
# 2.初始化 requester
# ------------------
TASK_PULL_PORT = 11111
from prototype.task.simple_task import SimpleTask
from prototype.requester import Requester

task = SimpleTask("This is a simple task", list(range(100)), 4)

randomizer_list = [(10000, "localhost")]

# requester对象初始化
requester = Requester(
    ipfs_url,
    web3_url,
    contract_address,
    contract_abi,
    "tmp/keypairs/pk.pkl",
    "tmp/keypairs/sk.pkl",
    randomizer_list,
    task,
    TASK_PULL_PORT,
)

requester.daemon_start()
time.sleep(1)
submitter.daemon_start()

# ------------------
# 3.初始化 randomizer
# ------------------
from prototype.randomizer import Randomizer

PROVING_SERVER_PORT = 10000
# randomizer对象初始化
randomizer = Randomizer(
    ipfs_url,
    web3_url,
    contract_address,
    contract_abi,
    "tmp/keypairs/pk.pkl",
    PROVING_SERVER_PORT,
    id=0,
)