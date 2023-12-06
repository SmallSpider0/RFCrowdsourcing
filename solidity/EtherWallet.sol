// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract EtherWallet {
    // 用于跟踪每个地址余额的mapping
    mapping(address => uint) public balances;

    constructor() payable{
        balances[msg.sender] += msg.value;
    }

    // 当合约接收Ether时，增加发送者的余额
    receive() external payable {
        balances[msg.sender] += msg.value;
    }

    // 允许用户提取他们的Ether，前提是余额充足
    function withdraw(uint _amount) external {
        require(balances[msg.sender] >= _amount, "Insufficient balance");
        balances[msg.sender] -= _amount;
        payable(msg.sender).transfer(_amount);
    }

    // 返回合约的总余额
    function getBalance() external view returns (uint) {
        return address(this).balance;
    }
}
