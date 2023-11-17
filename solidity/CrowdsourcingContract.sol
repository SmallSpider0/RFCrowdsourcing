// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract CrowdsourcingContract {
    // 定义事件
    event SubTaskAnswerSubmitted(uint subTaskId, bytes32 commit, string filehash, uint[] selectedRandomizers);
    event SubTaskAnswerEncrypted(uint subTaskId, bytes32 commit, string filehash, address randomizer);
    event SubTaskEncryptionCompleted(uint subTaskId);

    // 用于存储重加密结果的结构体
    struct EncryptionResult {
        bytes32 commit;
        string filehash;
    }

    // 随机化器结构体
    struct Randomizer {
        uint id;
        bool isRegistered;
    }

    // 子任务结构体
    struct SubTask {
        bytes32 initialCommit;
        string initialFilehash;
        EncryptionResult[] encryptionResults;
        bool isInited;
        bool isCompleted;
        uint[] selectedRandomizers; //被选中执行该提交重加密的Randomizer
        uint currentRandomizerIndex;  // 当前执行加密的Randomizer索引
    }

    // 存储所有子任务
    SubTask[] public subTasks;

    // Mapping from Randomizer's address to their information
    mapping(address => Randomizer) public randomizerInfo;

    // 当前已注册的Randomizer数量
    uint public randomizerCount;

    // 需要重加密的次数
    uint public requiredEncryptions;
    uint public subTaskCount;

    // 构造函数，由Requester初始化主任务
    constructor(uint _subTaskCount, uint _requiredEncryptions) {
        requiredEncryptions = _requiredEncryptions;
        subTaskCount = _subTaskCount;
        for (uint i = 0; i < subTaskCount; i++) {
            subTasks.push();
        }
    }

    // 获取指定子任务的被选中的Randomizer ID数组
    function getSelectedRandomizers(uint subTaskId) public view returns (uint[] memory) {
        require(subTaskId < subTasks.length, "SubTask does not exist");
        return subTasks[subTaskId].selectedRandomizers;
    }

    // Randomizer注册函数
    function registerRandomizer() public {
        require(!randomizerInfo[msg.sender].isRegistered, "Randomizer already registered");
        randomizerInfo[msg.sender] = Randomizer(randomizerCount, true);
        randomizerCount++;
    }

    // 重置合约到初始状态的函数
    // 仅用于测试！！！！！！！！！
    function reset() public {
        // 清除所有子任务
        delete subTasks;

        // 重新初始化子任务
        for (uint i = 0; i < subTaskCount; i++) {
            subTasks.push();
        }

        // 重置Randomizer信息
        randomizerCount = 0;

        // 重置其他需要的状态变量
        // 如果有其他状态变量需要重置，可以在这里添加代码
        // ...
    }


    // Submitter提交子任务答案
    function submitSubTaskAnswer(uint subTaskId, bytes32 commit, string memory filehash, uint vrfOutput, bytes memory vrfProof) public {
        SubTask storage subTask = subTasks[subTaskId];
        require(!subTask.isInited, "SubTask already inited");
        // 验证VRF输出和证据 ...
        // 简单的VRF验证（不具备安全性）
        // 仅用于测试！！！！
        require(keccak256(vrfProof) == keccak256(vrfProof), "Invalid VRF proof");

        // 使用VRF输出选择Randomizer
        uint[] memory selectedRandomizers = selectRandomizers(vrfOutput, requiredEncryptions, randomizerCount);
        subTask.selectedRandomizers = selectedRandomizers;

        subTask.isInited = true;
        subTask.initialCommit = commit;
        subTask.initialFilehash = filehash;
        emit SubTaskAnswerSubmitted(subTaskId, commit, filehash, selectedRandomizers);
    }

    // 随机选择Randomizer的函数
    function selectRandomizers(uint seed, uint count, uint randomizerPoolSize) private pure returns (uint[] memory) {
        uint[] memory selected = new uint[](count);
        for (uint i = 0; i < count; i++) {
            seed = uint(keccak256(abi.encode(seed, i)));
            selected[i] = seed % randomizerPoolSize;
        }
        return selected;
    }


    // Randomizer进行子任务答案的重加密
    function encryptSubTaskAnswer(uint subTaskId, bytes32 newCommit, string memory newFilehash) public {
        require(randomizerInfo[msg.sender].isRegistered, "Randomizer is not registered");
        uint randomizerId = randomizerInfo[msg.sender].id;

        // 确保调用者是选中的Randomizer
        bool isSelected = false;
        for (uint i = 0; i < subTasks[subTaskId].selectedRandomizers.length; i++) {
            if (subTasks[subTaskId].selectedRandomizers[i] == randomizerId) {
                isSelected = true;
                break;
            }
        }
        require(isSelected, "Not a selected Randomizer");

        // 更新子任务
        SubTask storage subTask = subTasks[subTaskId];
        require(!subTask.isCompleted, "SubTask already completed");
        subTask.encryptionResults.push(EncryptionResult(newCommit, newFilehash));

        // 抛出成功提交重加密结果的event
        emit SubTaskAnswerEncrypted(subTaskId, newCommit, newFilehash, msg.sender);

        // 若重加密次数足够，则抛出完成event
        if (subTask.encryptionResults.length >= requiredEncryptions) {
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
