from web3 import Web3
from eth_abi import decode
from threading import Thread
import json
import time


class ContractInterface:
    def __init__(self, provider_url: str, contract_address: str, contract_abi: list):
        self.web3 = Web3(Web3.HTTPProvider(provider_url))
        self.contract = self.web3.eth.contract(
            address=contract_address, abi=contract_abi
        )

    def send_transaction(
        self, function_name: str, account: str, private_key: str, *args, **kwargs
    ):
        """
        Send a transaction to the contract.
        """
        func = getattr(self.contract.functions, function_name)(*args, **kwargs)
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

    def log_loop(self, event_filter, event_handler, poll_interval):
        while True:
            for event in event_filter.get_new_entries():
                event_handler(event, self.prase_event(event))
            time.sleep(poll_interval)

    def listen_for_events(self, event_name: str, event_handler, is_async=False):
        """
        Listen for events and handle them using the provided event_handler function.
        """
        event_signature_hash = self.web3.keccak(text=event_name).hex()
        event_filter = self.web3.eth.filter(
            {
                "address": self.contract.address,
                "topics": [
                    event_signature_hash,
                ],
            }
        )
        if is_async:
            worker = Thread(
                target=self.log_loop, args=(event_filter, event_handler, 1), daemon=True
            )
            worker.start()
        else:
            self.log_loop(event_filter, event_handler, 1)

    def prase_event(self, event):
        event_args = {}
        event_data = event["data"]
        event_topics = event["topics"]

        # 获取事件的签名哈希
        event_signature_hash = event_topics[0].hex()

        # 查找对应的事件定义
        for event_abi in self.contract.abi:
            if event_abi.get("type") == "event":
                event_signature = (
                    event_abi["name"]
                    + "("
                    + ",".join(i["type"] for i in event_abi["inputs"])
                    + ")"
                )
                if self.web3.keccak(text=event_signature).hex() == event_signature_hash:
                    # 解析事件参数
                    indexed_types = [
                        input["type"]
                        for input in event_abi["inputs"]
                        if input["indexed"]
                    ]
                    non_indexed_types = [
                        input["type"]
                        for input in event_abi["inputs"]
                        if not input["indexed"]
                    ]
                    names = [input["name"] for input in event_abi["inputs"]]
                    indexed_values = event_topics[1:]

                    # 解码非索引参数
                    if type(event_data)==str:
                        event_data = event_data.encode()
                    non_indexed_values_bytes = bytes(event_data)
                    non_indexed_decoded = list(
                        decode(non_indexed_types, non_indexed_values_bytes)
                    )

                    # 准备索引参数
                    indexed_decoded = []
                    for i, typ in enumerate(indexed_types):
                        if typ == "address":
                            # 如果是地址类型，转换为常规0x开头的地址格式
                            indexed_decoded.append(
                                self.web3.toChecksumAddress(indexed_values[i].hex())
                            )
                        elif typ == "uint256":
                            # 如果是uint256，直接转换为整数
                            indexed_decoded.append(int(indexed_values[i].hex(), 16))
                        # 根据需要处理其他类型...

                    # 合并参数
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
    with open("solidity/contract-abi.json") as file:
        contract_abi = json.loads(file.read())  # 智能合约ABI
    contract_interface = ContractInterface(provider_url, contract_address, contract_abi)

    # 监听事件
    def handle_integer_received(raw_event, args):
        print(args)

    contract_interface.listen_for_events(
        "IntegerReceived(uint256)", handle_integer_received, is_async=True
    )

    # 使用异步模式监听事件时 主程序可以运行其它代码
    for _ in range(10):
        time.sleep(1)

    # 发送交易
    contract_interface.send_transaction("receiveInteger", account, private_key, 123)
