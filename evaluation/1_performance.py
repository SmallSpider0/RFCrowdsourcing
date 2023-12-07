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

    while True:
        if ret is not None:
            return ret
        time.sleep(1)


paras = [
    [1, 20, 10, 1],
    [1, 20, 10, 2],
    [1, 20, 10, 3],
    [1, 20, 10, 4],
    [1, 20, 10, 5],
    [1, 20, 10, 6],
    [1, 20, 10, 7],
    [1, 20, 10, 8],
    [1, 20, 10, 9],
    [1, 20, 10, 10],
]

port = 33333
for p in paras:
    for _ in range(1):
        ret = eval(p[0], p[1], p[2], p[3], port)
        with open("evaluation/results/results.txt", "a") as f:
            f.write((",".join([str(num) for num in p]) + ":" + str(ret) + "\n"))

# 设定[1,5,10,(1,2,3)]
# [33.07875370979309, 50.63353705406189, 67.95407605171204]
# [33.04142427444458, 50.572059869766235, 68.0313081741333]
# [32.85447812080383, 50.49394416809082, 68.28303909301758]

# 设定[1,3,10,(1,2,3)]
# [34.67126822471619, 51.68482184410095, 62.10559916496277]
# [33.24574899673462, 50.554965019226074, 68.2726571559906]
# [33.85741472244263, 50.4607789516449, 68.09521412849426]
