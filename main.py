# TODO：实现多进程模拟各个模块运行
# TODO：评估每个角色需要智能合约进行哪些交互，并完成智能合约的开发与测试

# 导入测试所需的包
import json

# 测试参数定义
ipfs_url = "/ip4/127.0.0.1/tcp/5001"
web3_url = "http://127.0.0.1:8545"
contract_address = "0xd7357e2A30760f94971bC8Eb10f5dd0D1cFdB6Ae"
with open("solidity/contract-abi.json") as file:
    contract_abi = json.loads(file.read())  # 智能合约ABI

# ------------------
# 1.初始化 submitter
# ------------------
from prototype.task.simple_task import SimpleSubtask
from prototype.submitter import Submitter

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
    SimpleSubtask,
)

# ------------------
# 2.初始化 requester
# ------------------
TASK_PULL_PORT = 11111
from prototype.task.simple_task import SimpleTask
from prototype.requester import Requester

task = SimpleTask("This is a simple task", list(range(100)), 1)

randomizer_list = {"0xe7B44655990857181d5fCfaaAe3471B2B911CaB4": (10000, "localhost")}

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

# ------------------
# 3.初始化 randomizer
# ------------------
from prototype.randomizer import Randomizer

PORT = 10000
# randomizer对象初始化
randomizer = Randomizer(
    ipfs_url, web3_url, contract_address, contract_abi, "tmp/keypairs/pk.pkl", PORT
)

# 启动3个节点
nodes = [randomizer, requester, submitter]
for _ in nodes:
    _.daemon_start()

# 发送交易 触发event
account = "0xe7B44655990857181d5fCfaaAe3471B2B911CaB4"
private_key = "0x5ddfd9257c762b7b23f65844dac651b8469c01b1b14291ffde2a9017d15453c5"
randomizer.contract_interface.send_transaction(
    "receiveInteger", account, private_key, 123
)