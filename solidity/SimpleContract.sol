// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract SimpleContract {
    // 定义一个event，用于记录接收到的整数
    event IntegerReceived(uint8[] value);

    // 存储最后一个接收到的整数
    uint public lastReceivedInteger;

    // 函数用于接收整数并触发事件
    function receiveInteger(uint _value) public {
        lastReceivedInteger = _value;
        uint8[] memory values = new uint8[](2);
        values[0]=123;
        values[1]=233;
        emit IntegerReceived(values);
    }
}
