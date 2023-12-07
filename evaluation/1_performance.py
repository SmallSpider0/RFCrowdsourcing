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


def eval(SUBMITTER_NUM, RANDOMIZER_NUM, SUBTASK_NUM, RE_ENC_NUM, port):
    global ret
    ret = None

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
        port,
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


paras = [
    [1, 10, 25, 3],
    [1, 10, 25, 6],
    [1, 10, 25, 9],
    [1, 10, 25, 12],

    [1, 20, 25, 3],
    [1, 20, 25, 6],
    [1, 20, 25, 9],
    [1, 20, 25, 12],

    [1, 30, 25, 3],
    [1, 30, 25, 6],
    [1, 30, 25, 9],
    [1, 30, 25, 12],

    [1, 40, 25, 3],
    [1, 40, 25, 6],
    [1, 40, 25, 9],
    [1, 40, 25, 12],

    [1, 50, 25, 3],
    [1, 50, 25, 6],
    [1, 50, 25, 9],
    [1, 50, 25, 12],

    [1, 10, 50, 3],
    [1, 10, 50, 6],
    [1, 10, 50, 9],
    [1, 10, 50, 12],

    [1, 20, 50, 3],
    [1, 20, 50, 6],
    [1, 20, 50, 9],
    [1, 20, 50, 12],

    [1, 30, 50, 3],
    [1, 30, 50, 6],
    [1, 30, 50, 9],
    [1, 30, 50, 12],

    [1, 40, 50, 3],
    [1, 40, 50, 6],
    [1, 40, 50, 9],
    [1, 40, 50, 12],

    [1, 50, 50, 3],
    [1, 50, 50, 6],
    [1, 50, 50, 9],
    [1, 50, 50, 12],
]

paras = [
    [1,10,10,1]
]

port = 33333
for p in paras:
    for _ in range(1):
        ret = eval(p[0], p[1], p[2], p[3], port)
        with open("evaluation/results/results.txt", "a") as f:
            f.write((",".join([str(num) for num in p]) + ":" + str(ret) + "\n"))