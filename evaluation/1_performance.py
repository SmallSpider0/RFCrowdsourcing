# 添加当前路径至解释器，确保单元测试时可正常import其它文件
import os
import sys

current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 基于顶层包的import
from prototype.system_interface_remote import SystemInterfaceRemote

# 系统库
import time
import pickle

CNT = 0
ret = None


def eval(SUBMITTER_NUM, RANDOMIZER_NUM, SUBTASK_NUM, RE_ENC_NUM, key_len):
    global ret
    ret = None

    public_key_file = f"tmp/keypairs/pk{key_len}.pkl"
    private_key_file = f"tmp/keypairs/sk{key_len}.pkl"

    def server(instruction, conn, addr):
        if instruction == "event/TASK_END":
            print("event/TASK_END")
            global ret
            ret = time.time() - system.times["inited"]
            print("dur", ret)

    # 启动分布式系统
    system = SystemInterfaceRemote(
        "CIFAR10Task",
        server,
        SUBMITTER_NUM,
        RANDOMIZER_NUM,
        SUBTASK_NUM,
        RE_ENC_NUM,
        public_key_file,
        private_key_file,
    )
    system.start_envs()
    system.start_manager(True)
    system.run()
    for id in range(SUBMITTER_NUM):
        system.call_submitter(id, "start", False)
    print("started")

    while True:
        if ret is not None:
            return ret
        time.sleep(1)


# paras = [
#     [10, 10, 25, 2],
#     [10, 10, 25, 4],
#     [10, 10, 25, 6],
#     [10, 10, 25, 8],
#     [10, 10, 50, 2],
#     [10, 10, 50, 4],
#     [10, 10, 50, 6],
#     [10, 10, 50, 8],
#     [10, 50, 25, 2],
#     [10, 50, 25, 4],
#     [10, 10, 25, 6],
#     [10, 10, 25, 8],
#     [10, 10, 50, 2],
#     [10, 10, 50, 4],
#     [10, 10, 50, 6],
#     [10, 10, 50, 8],
# ]

paras = [
    [10, 10, 25, 2],
    [10, 10, 25, 4],
    [10, 10, 25, 6],
    [10, 10, 25, 8],
    [10, 10, 25, 2],
    [10, 10, 25, 4],
    [10, 10, 25, 6],
    [10, 10, 25, 8],
    [10, 10, 25, 2],
    [10, 10, 25, 4],
    [10, 10, 25, 6],
    [10, 10, 25, 8],

]

for p in paras:
    for key_len in [2048]:
        ret = eval(p[0], p[1], p[2], p[3], key_len)
        with open("evaluation/results/results.txt", "a") as f:
            f.write(
                str(key_len)
                + ","
                + (",".join([str(num) for num in p]) + ":" + str(ret) + "\n")
            )
