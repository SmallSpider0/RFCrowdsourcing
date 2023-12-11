// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract CrowdsourcingContract {
    // 定义事件
    event SubTaskAnswerSubmitted(uint32 subTaskId, string filehash);

    event SubTaskAnswerEncrypted(
        uint32 subTaskId,
        string filehash,
        uint8 randomizerId
    );
    event SubTaskEncryptionCompleted(uint32 subTaskId);

    // 用于存储重加密结果的结构体
    struct EncryptionResult {
        bytes32 commit;
        string filehash;
    }

    // 随机化器结构体
    struct Randomizer {
        uint8 id;
        bool isRegistered;
    }

    // 子任务结构体
    struct SubTask {
        bytes32 initialCommit;
        string initialFilehash;
        EncryptionResult[] encryptionResults;
        bool isInited;
        bool isCompleted;
        uint8[] selectedRandomizers; //被选中执行该提交重加密的Randomizer
        uint8 currentRandomizerIndex; // 当前执行加密的Randomizer索引
    }

    // 子任务结果
    struct SubTaskResult {
        bytes32 initialCommit;
        string initialFilehash;
        EncryptionResult[] encryptionResults;
        uint8[] selectedRandomizers;
    }

    // 存储所有子任务
    SubTask[] public subTasks;

    // Mapping from Randomizer's address to their information
    mapping(address => Randomizer) public randomizerInfo;

    // 当前已注册的Randomizer数量
    uint8 public randomizerCount;

    // 需要重加密的次数
    uint8 public requiredEncryptions;
    uint32 public subTaskCount;

    // 构造函数，由Requester初始化主任务
    constructor(uint32 _subTaskCount, uint8 _requiredEncryptions) {
        requiredEncryptions = _requiredEncryptions;
        subTaskCount = _subTaskCount;
        for (uint i = 0; i < subTaskCount; i++) {
            subTasks.push();
        }
    }

    // 获取指定子任务的被选中的Randomizer ID数组
    function getSelectedRandomizers(
        uint subTaskId
    ) public view returns (uint8[] memory) {
        require(subTaskId < subTasks.length, "SubTask does not exist");
        return subTasks[subTaskId].selectedRandomizers;
    }

    // Randomizer注册函数
    function registerRandomizer(uint8 id) public {
        require(
            !randomizerInfo[msg.sender].isRegistered,
            "Randomizer already registered"
        );
        randomizerInfo[msg.sender] = Randomizer(id, true);
        randomizerCount++;
    }

    // Submitter提交子任务答案
    function submitSubTaskAnswer(
        uint32 subTaskId,
        bytes32 commit,
        string memory filehash,
        uint vrfOutput
    ) public {
        SubTask storage subTask = subTasks[subTaskId];
        require(!subTask.isInited, "SubTask already inited");
        // 使用VRF输出选择Randomizer
        uint8[] memory selectedRandomizers = selectRandomizers(
            vrfOutput,
            requiredEncryptions,
            randomizerCount
        );
        subTask.selectedRandomizers = selectedRandomizers;
        subTask.isInited = true;
        subTask.initialCommit = commit;
        subTask.initialFilehash = filehash;
        emit SubTaskAnswerSubmitted(subTaskId, filehash);
        if (requiredEncryptions == 0) {
            subTask.isCompleted = true;
            emit SubTaskEncryptionCompleted(subTaskId);
        }
    }

    // 随机选择Randomizer的函数
    function selectRandomizers(
        uint seed,
        uint count,
        uint8 randomizerPoolSize
    ) private pure returns (uint8[] memory) {
        require(
            count <= randomizerPoolSize,
            "More randomizers requested than available"
        );

        uint8[] memory pool = new uint8[](randomizerPoolSize);
        for (uint8 i = 0; i < randomizerPoolSize; i++) {
            pool[i] = i;
        }

        for (uint8 i = 0; i < count; i++) {
            seed = uint(keccak256(abi.encode(seed, i)));
            uint modResult = seed % (randomizerPoolSize - i);
            require(modResult <= 255, "Mod result out of range for uint8");
            uint8 j = i + uint8(modResult);
            // Swap pool[i] and pool[j]
            uint8 temp = pool[i];
            pool[i] = pool[j];
            pool[j] = temp;
        }

        uint8[] memory selected = new uint8[](count);
        for (uint i = 0; i < count; i++) {
            selected[i] = pool[i];
        }

        return selected;
    }

    // Randomizer进行子任务答案的重加密
    function encryptSubTaskAnswer(
        uint32 subTaskId,
        bytes32 newCommit,
        string memory newFilehash
    ) public {
        require(
            randomizerInfo[msg.sender].isRegistered,
            "Randomizer is not registered"
        );
        uint randomizerId = randomizerInfo[msg.sender].id;

        // 确保调用者是选中的Randomizer
        bool isSelected = false;
        for (
            uint i = 0;
            i < subTasks[subTaskId].selectedRandomizers.length;
            i++
        ) {
            if (subTasks[subTaskId].selectedRandomizers[i] == randomizerId) {
                isSelected = true;
                break;
            }
        }
        require(isSelected, "Not a selected Randomizer");

        // 更新子任务
        SubTask storage subTask = subTasks[subTaskId];
        require(!subTask.isCompleted, "SubTask already completed");
        subTask.encryptionResults.push(
            EncryptionResult(newCommit, newFilehash)
        );

        //若重加密次数足够，则抛出完成event
        if (subTask.encryptionResults.length >= requiredEncryptions) {
            subTask.isCompleted = true;
            emit SubTaskEncryptionCompleted(subTaskId);
        } else {
            // 抛出成功提交重加密结果的event 请求下一个Randomizer重加密
            emit SubTaskAnswerEncrypted(
                subTaskId,
                newFilehash,
                randomizerInfo[msg.sender].id
            );
        }
    }

    // 获取子任务最终结果
    function getSubTaskFinalResult(
        uint subTaskId
    ) public view returns (SubTaskResult memory) {
        require(subTaskId < subTasks.length, "SubTask does not exist");
        SubTask storage subTask = subTasks[subTaskId];
        //require(subTask.isCompleted, "SubTask is not completed yet");

        return
            SubTaskResult({
                initialCommit: subTask.initialCommit,
                initialFilehash: subTask.initialFilehash,
                encryptionResults: subTask.encryptionResults,
                selectedRandomizers: subTask.selectedRandomizers
            });
    }
}
