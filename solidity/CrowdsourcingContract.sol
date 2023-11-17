// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract CrowdsourcingContract {
    // 定义事件
    event SubTaskAnswerSubmitted(uint subTaskId, bytes32 commit, string filehash);
    event SubTaskAnswerEncrypted(uint subTaskId, bytes32 commit, string filehash, address randomizer);
    event SubTaskEncryptionCompleted(uint subTaskId);

    // 用于存储重加密结果的结构体
    struct EncryptionResult {
        bytes32 commit;
        string filehash;
    }

    // 子任务结构体
    struct SubTask {
        bytes32 initialCommit;
        string initialFilehash;
        EncryptionResult[] encryptionResults;
        uint requiredEncryptions;
        bool isCompleted;
    }

    // 存储所有子任务
    SubTask[] public subTasks;

    // 构造函数，由Requester初始化主任务
    constructor(uint subTaskCount, uint requiredEncryptions) {
        for (uint i = 0; i < subTaskCount; i++) {
            SubTask storage newSubTask = subTasks.push();
            newSubTask.requiredEncryptions = requiredEncryptions;
        }
    }

    // 重置合约到初始状态的函数
    // 仅用于测试！！！！！！！！！
    function reset() public {
        for (uint i = 0; i < subTasks.length; i++) {
            SubTask storage subTask = subTasks[i];
            subTask.initialCommit = 0;
            subTask.initialFilehash = "";
            delete subTask.encryptionResults;  // 清除加密结果数组
            subTask.isCompleted = false;
        }
    }

    // Submitter提交子任务答案
    function submitSubTaskAnswer(uint subTaskId, bytes32 commit, string memory filehash) public {
        SubTask storage subTask = subTasks[subTaskId];
        require(!subTask.isCompleted, "SubTask already completed");
        subTask.initialCommit = commit;
        subTask.initialFilehash = filehash;
        emit SubTaskAnswerSubmitted(subTaskId, commit, filehash);
    }

    // Randomizer进行子任务答案的重加密
    function encryptSubTaskAnswer(uint subTaskId, bytes32 newCommit, string memory newFilehash) public {
        SubTask storage subTask = subTasks[subTaskId];
        require(!subTask.isCompleted, "SubTask already completed");
        subTask.encryptionResults.push(EncryptionResult(newCommit, newFilehash));

        emit SubTaskAnswerEncrypted(subTaskId, newCommit, newFilehash, msg.sender);

        if (subTask.encryptionResults.length >= subTask.requiredEncryptions) {
            subTask.isCompleted = true;
            emit SubTaskEncryptionCompleted(subTaskId);
        }
    }

    // 获取子任务信息
    function getSubTaskInfo(uint subTaskId) public view returns (SubTask memory) {
        require(subTaskId < subTasks.length, "SubTask does not exist");
        return subTasks[subTaskId];
    }

    // 获取子任务最终结果
    function getSubTaskFinalResult(uint subTaskId) public view returns (EncryptionResult memory) {
        SubTask storage subTask = subTasks[subTaskId];
        require(subTask.isCompleted, "SubTask is not completed yet");
        return subTask.encryptionResults[subTask.encryptionResults.length - 1];
    }
}
