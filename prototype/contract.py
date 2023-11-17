'''
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
'''

# 系统库
from web3 import Web3
from eth_abi import decode
from threading import Thread
import json
import time
from hexbytes import HexBytes

class ContractInterface:
    def __init__(self, provider_url: str, contract_address: str, contract_abi: list):
        """
        Initializes the ContractInterface instance.

        :param provider_url: URL of the Ethereum node provider.
        :param contract_address: Ethereum address of the deployed contract.
        :param contract_abi: ABI of the contract.
        """
        self.web3 = Web3(Web3.HTTPProvider(provider_url))
        self.contract = self.web3.eth.contract(
            address=contract_address, abi=contract_abi
        )

    def send_transaction(
        self, function_name: str, account: str, private_key: str, *args, **kwargs
    ):
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
            if abi.get('type') == 'function' and abi.get('name') == function_name:
                function_abi = abi
                break
        
        if not function_abi:
            raise ValueError(f"No function named {function_name} in contract ABI")

        converted_args = []
        for i, arg in enumerate(args):
            arg_type = function_abi['inputs'][i]['type']
            # Convert string-represented bytes data to HexBytes
            if arg_type.startswith("bytes") and isinstance(arg, str):
                converted_arg = HexBytes(arg)
            else:
                converted_arg = arg
            converted_args.append(converted_arg)

        # Create and send transaction
        func = getattr(self.contract.functions, function_name)(*converted_args, **kwargs)
        txn = func.build_transaction(
            {
                "from": account,
                "nonce": self.web3.eth.get_transaction_count(account),
                "gas": 2000000,
                "gasPrice": self.web3.to_wei("10", "gwei"),
            }
        )
        signed_txn = self.web3.eth.account.sign_transaction(txn, private_key)
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

    def listen_for_events(self, event_signature_or_name: str, event_handler, is_async=False):
        """
        Listens for events emitted by the smart contract and handles them with the provided event_handler function.

        :param event_signature_or_name: Complete event signature or event name.
        :param event_handler: Function to handle the events.
        :param is_async: If True, runs the listener in a separate thread.

        :return: None
        """
        # 检查是否包含括号，以确定是否为完整事件签名
        if "(" in event_signature_or_name:
            # 完整事件签名
            event_signature = event_signature_or_name
        else:
            # 仅事件名称，需要从ABI中查找并构建签名
            event_name = event_signature_or_name
            event_abi = [event for event in self.contract.abi if event.get('name') == event_name and event.get('type') == 'event']
            if not event_abi:
                raise ValueError(f"No event named '{event_name}' found in contract ABI")
            if len(event_abi) > 1:
                raise ValueError(f"Multiple events named '{event_name}' found, please specify the full signature")
            event_signature = "{}({})".format(event_name, ','.join(input['type'] for input in event_abi[0]['inputs']))

        # 生成事件签名哈希
        event_signature_hash = self.web3.keccak(text=event_signature).hex()

        # 创建事件过滤器
        event_filter = self.web3.eth.filter(
            {
                "address": self.contract.address,
                "topics": [event_signature_hash],
            }
        )

        # 启动监听
        if is_async:
            worker = Thread(
                target=self.__log_loop, args=(event_filter, event_handler, 1), daemon=True
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
                event_handler(event, self.__prase_event(event))
            time.sleep(poll_interval)

    def __prase_event(self, event):
        """
        Internal method to parse the raw event data into a more readable format.

        :param event: Raw event data.

        :return: Parsed event data.
        """
        event_args = {}
        event_data = event["data"]
        event_topics = event["topics"]

        # Extract the event's signature hash
        event_signature_hash = event_topics[0].hex()

        # Find the corresponding event definition in the ABI
        for event_abi in self.contract.abi:
            if event_abi.get("type") == "event":
                event_signature = (
                    event_abi["name"]
                    + "("
                    + ",".join(i["type"] for i in event_abi["inputs"])
                    + ")"
                )
                if self.web3.keccak(text=event_signature).hex() == event_signature_hash:
                    # Parse event parameters
                    indexed_types = [input["type"] for input in event_abi["inputs"] if input["indexed"]]
                    non_indexed_types = [input["type"] for input in event_abi["inputs"] if not input["indexed"]]
                    names = [input["name"] for input in event_abi["inputs"]]
                    indexed_values = event_topics[1:]

                    # Decode non-indexed parameters
                    if type(event_data)==str:
                        event_data = event_data.encode()
                    non_indexed_values_bytes = bytes(event_data)
                    non_indexed_decoded = list(decode(non_indexed_types, non_indexed_values_bytes))

                    # Prepare indexed parameters
                    indexed_decoded = []
                    for i, typ in enumerate(indexed_types):
                        if typ == "address":
                            indexed_decoded.append(self.web3.toChecksumAddress(indexed_values[i].hex()))
                        elif typ == "uint256":
                            indexed_decoded.append(int(indexed_values[i].hex(), 16))

                    # Merge parameters
                    event_args = dict(zip(names, indexed_decoded + non_indexed_decoded))
                    break
        return event_args



if __name__ == "__main__":
    # 测试参数定义
    provider_url = "http://127.0.0.1:8545"
    contract_address = "0xd7357e2A30760f94971bC8Eb10f5dd0D1cFdB6Ae"
    account = "0xe7B44655990857181d5fCfaaAe3471B2B911CaB4"
    private_key = "0x5ddfd9257c762b7b23f65844dac651b8469c01b1b14291ffde2a9017d15453c5"

    # 合约对象初始化
    with open("solidity/SimpleContract.json") as file:
        contract_abi = json.loads(file.read())  # 智能合约ABI
    contract_interface = ContractInterface(provider_url, contract_address, contract_abi)

    # 监听事件
    def handle_integer_received(raw_event, args):
        print(args)

    contract_interface.listen_for_events(
        "IntegerReceived", handle_integer_received, is_async=True
    )

    # 发送交易
    contract_interface.send_transaction("receiveInteger", account, private_key, 123)

    lastReceivedInteger = contract_interface.call_function("lastReceivedInteger")
    print(lastReceivedInteger)

    # 使用异步模式监听事件时 主程序可以运行其它代码
    for _ in range(10):
        time.sleep(1)