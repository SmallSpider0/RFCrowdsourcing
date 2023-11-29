# 添加当前路径至解释器，确保单元测试时可正常import其它文件
import os
import sys

current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 基于顶层包的import
from prototype.utils.config import Config

config = Config()

# 系统库
from web3 import Web3
from web3.middleware import geth_poa_middleware
from threading import Thread
import threading
import time
import queue

POLL_INTERVAL = config.get_config("smart_contract").get("poll_interval")


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
        # 合约相关参数
        self.web3 = Web3(Web3.HTTPProvider(provider_url))
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)  # 兼容POA
        self.contract = self.web3.eth.contract(
            address=contract_address, abi=contract_abi
        )

        # 账户相关参数
        self.bc_account = bc_account
        self.bc_private_key = bc_private_key
        self.bc_nonce = self.web3.eth.get_transaction_count(self.bc_account)
        self.transaction_queue = queue.LifoQueue()
        self.sent_transaction_queue = queue.LifoQueue()
        self.total_gas_cost = 0

        # 启动独立线程串行发送交易
        threading.Thread(target=self.__trans_submission_daemon).start()

        # 启动独立线程等待交易回执
        threading.Thread(target=self.__receipt_handler_daemon).start()

    def send_transaction_receipt(self, callback, function_name: str, *args, **kwargs):
        """
        Sends a transaction to a specified function of the smart contract.

        :param function_name: Name of the contract function to call.
        :param callback: Callback function when receive receipt.
        :param args: Positional arguments to pass to the function.
        :param kwargs: Keyword arguments to pass to the function.

        """
        self.transaction_queue.put((callback, function_name, args, kwargs))

    def send_transaction(self, function_name: str, *args, **kwargs):
        """
        Sends a transaction to a specified function of the smart contract.

        :param function_name: Name of the contract function to call.
        :param args: Positional arguments to pass to the function.
        :param kwargs: Keyword arguments to pass to the function.

        """
        self.transaction_queue.put((None, function_name, args, kwargs))

    def __receipt_handler_daemon(self):
        # 按交易发送顺序获取交易回执
        while True:
            callback, function_name, txn_hash = self.sent_transaction_queue.get()
            try:
                receipt = self.web3.eth.wait_for_transaction_receipt(txn_hash, 20, 0.5)
                if receipt.status != 1:
                    print(function_name, receipt)
                else:
                    callback(function_name, receipt)
            except:
                print(function_name)

    def __trans_submission_daemon(self):
        # 按请求顺序发送交易
        while True:
            # 获取下一个待发送的交易
            callback, function_name, args, kwargs = self.transaction_queue.get()

            # 发送交易
            func = getattr(self.contract.functions, function_name)(*args, **kwargs)
            txn = func.build_transaction(
                {
                    "from": self.bc_account,
                    "nonce": self.bc_nonce,
                    "gasPrice": 0,
                }
            )
            signed_txn = self.web3.eth.account.sign_transaction(
                txn, self.bc_private_key
            )
            txn_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)

            # 异步获取回执
            if callback != None:
                self.sent_transaction_queue.put((callback, function_name, txn_hash))

            # 本地管理Nonce 避免由于交易发送太快导致Nonce错误
            self.bc_nonce += 1

            # 记录总gas开销
            self.total_gas_cost += txn["gas"]

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

    def listen_for_events(self, event_name: str, event_handler, is_async=False):
        """
        Listens for events emitted by the smart contract and handles them with the provided event_handler function.

        :param event_name: Complete event name.
        :param event_handler: Function to handle the events.
        :param is_async: If True, runs the listener in a separate thread.

        :return: None
        """

        def log_loop(event_filter, event_handler, poll_interval):
            while True:
                for event in event_filter.get_new_entries():
                    event_handler(event, event["args"])
                time.sleep(poll_interval)

        # 创建事件过滤器
        event_filter = getattr(self.contract.events, event_name).create_filter(
            fromBlock="0x0"
        )
        if is_async:
            worker = Thread(
                target=log_loop,
                args=(event_filter, event_handler, POLL_INTERVAL),
                daemon=True,
            )
            worker.start()
        else:
            self.log_loop(event_filter, event_handler, POLL_INTERVAL)


if __name__ == "__main__":
    # 测试参数定义
    provider_url = "http://127.0.0.1:8545"
    account = "0x9A82f98d6083c30632A22a9e93a9dfA8B054C929"
    private_key = "0x11408f483264dcc0b831b0b95ffbfddc19d9a3ae98fc289baa5592d5b1e1d331"

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
        print("IntegerReceived", args["value"])

    contract_interface.listen_for_events(
        "IntegerReceived", handle_integer_received, is_async=True
    )

    time.sleep(1)

    # 发送交易 并获取回执
    def callback(function_name, receipt):
        print(function_name, receipt)

    contract_interface.send_transaction_receipt(callback, "receiveInteger", 123)

    lastReceivedInteger = contract_interface.call_function("lastReceivedInteger")
    print("lastReceivedInteger", lastReceivedInteger)
