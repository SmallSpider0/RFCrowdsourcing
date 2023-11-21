"""
ContractInterface Class
Initialization
__init__(self, provider_url: str, contract_address: str, contract_abi: list)

Initializes a new instance of the ContractInterface class.

Parameters:
provider_url (str): The URL of the Ethereum node provider.
contract_address (str): The Ethereum address of the deployed contract.
contract_abi (list): The Application Binary Interface (ABI) of the contract.
Returns: An instance of ContractInterface.
Sending Transactions
send_transaction(self, function_name: str, account: str, private_key: str, *args, **kwargs)

Sends a transaction to a specific function of the smart contract.

Parameters:
function_name (str): The name of the contract function to be called.
account (str): The Ethereum address from which the transaction is made.
private_key (str): The private key of the account, used to sign the transaction.
args (variable): Positional arguments to be passed to the function.
kwargs (variable): Keyword arguments to be passed to the function.
Returns: The transaction hash (HexBytes) of the sent transaction.
Calling Read-Only Functions
call_function(self, function_name: str, *args, **kwargs)

Calls a read-only function of the smart contract and returns its result.

Parameters:
function_name (str): The name of the read-only contract function to be called.
args (variable): Positional arguments to be passed to the function.
kwargs (variable): Keyword arguments to be passed to the function.
Returns: The result returned by the function call, automatically parsed into a corresponding Python data type based on the ABI.
Listening for Events
listen_for_events(self, event_name: str, event_handler, is_async=False)

Listens for events emitted by the smart contract and handles them with the provided event_handler function.

Parameters:
event_name (str): The name of the event to listen for.
event_handler (function): The function to handle the events. This function should take two parameters: the raw event data and the parsed event data.
is_async (bool, optional): If set to True, the event listener will run in a separate thread.
Returns: None. The events are handled asynchronously by the event_handler.
"""

# 系统库
from web3 import Web3
from eth_abi import decode
from threading import Thread
import json
import time
from hexbytes import HexBytes


class ContractInterface:
    def __init__(
        self,
        provider_url: str,
        contract_address: str,
        contract_abi: list,
        bc_account: str,
        bc_private_key: str,
    ):
        """
        Initializes the ContractInterface instance.

        :param provider_url: URL of the Ethereum node provider.
        :param contract_address: Ethereum address of the deployed contract.
        :param contract_abi: ABI of the contract.
        :param bc_account: Account of the blockchain user.
        :param bc_private_key: Private key of the blockchain user.
        """
        self.web3 = Web3(Web3.HTTPProvider(provider_url))
        self.contract = self.web3.eth.contract(
            address=contract_address, abi=contract_abi
        )
        self.bc_account = bc_account
        self.bc_private_key = bc_private_key

    def send_transaction(self, function_name: str, *args, **kwargs):
        """
        Sends a transaction to a specified function of the smart contract.

        :param function_name: Name of the contract function to call.
        :param account: Ethereum address from which the transaction is made.
        :param private_key: Private key of the account to sign the transaction.
        :param args: Positional arguments to pass to the function.
        :param kwargs: Keyword arguments to pass to the function.

        :return: Transaction hash of the sent transaction.
        """
        # Automatically convert argument types based on function ABI
        function_abi = None
        for abi in self.contract.abi:
            if abi.get("type") == "function" and abi.get("name") == function_name:
                function_abi = abi
                break

        if not function_abi:
            raise ValueError(f"No function named {function_name} in contract ABI")

        converted_args = []
        for i, arg in enumerate(args):
            arg_type = function_abi["inputs"][i]["type"]
            # Convert string-represented bytes data to HexBytes
            if arg_type.startswith("bytes") and isinstance(arg, str):
                converted_arg = HexBytes(arg)
            else:
                converted_arg = arg
            converted_args.append(converted_arg)

        # Create and send transaction
        func = getattr(self.contract.functions, function_name)(
            *converted_args, **kwargs
        )
        txn = func.build_transaction(
            {
                "from": self.bc_account,
                "nonce": self.web3.eth.get_transaction_count(self.bc_account),
                "gas": 2000000,
                "gasPrice": self.web3.to_wei("10", "gwei"),
            }
        )
        signed_txn = self.web3.eth.account.sign_transaction(txn, self.bc_private_key)
        txn_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        return txn_hash

    def call_function(self, function_name: str, *args, **kwargs):
        """
        Calls a read-only function of the smart contract and returns its result.

        :param function_name: Name of the read-only contract function to call.
        :param args: Positional arguments to pass to the function.
        :param kwargs: Keyword arguments to pass to the function.

        :return: The result returned by the function call.
        """
        func = getattr(self.contract.functions, function_name)(*args, **kwargs)
        result = func.call()
        return result

    def listen_for_events(
        self, event_name: str, event_handler, is_async=False
    ):
        """
        Listens for events emitted by the smart contract and handles them with the provided event_handler function.

        :param event_name: Complete event name.
        :param event_handler: Function to handle the events.
        :param is_async: If True, runs the listener in a separate thread.

        :return: None
        """
        # 创建事件过滤器
        event_filter = eval(f"self.contract.events.{event_name}.create_filter(fromBlock='0x0')")       
        if is_async:
            worker = Thread(
                target=self.__log_loop,
                args=(event_filter, event_handler, 1),
                daemon=True,
            )
            worker.start()
        else:
            self.__log_loop(event_filter, event_handler, 1)

    def __log_loop(self, event_filter, event_handler, poll_interval):
        """
        Internal method to continuously check for new events and handle them.

        :param event_filter: Web3 event filter object.
        :param event_handler: Function to handle the events.
        :param poll_interval: Time interval to wait between polls.

        :return: None
        """
        while True:
            for event in event_filter.get_new_entries():
                event_handler(event, event['args'])
            time.sleep(poll_interval)

if __name__ == "__main__":
    # 测试参数定义
    provider_url = "http://127.0.0.1:8545"
    account = "0xe7B44655990857181d5fCfaaAe3471B2B911CaB4"
    private_key = "0x5ddfd9257c762b7b23f65844dac651b8469c01b1b14291ffde2a9017d15453c5"

    # 合约部署
    from utils.tools import deploy_smart_contract

    contract_address, contract_abi = deploy_smart_contract(
        "SimpleContract", provider_url, account, private_key
    )

    # 合约对象初始化
    contract_interface = ContractInterface(
        provider_url, contract_address, contract_abi, account, private_key
    )

    # 监听事件
    def handle_integer_received(raw_event, args):
        print(args['value'])

    contract_interface.listen_for_events(
        "IntegerReceived", handle_integer_received, is_async=True
    )

    # 发送交易
    contract_interface.send_transaction("receiveInteger", 123)

    lastReceivedInteger = contract_interface.call_function("lastReceivedInteger")
    print(lastReceivedInteger)

    # 使用异步模式监听事件时 主程序可以运行其它代码
    for _ in range(10):
        time.sleep(1)
