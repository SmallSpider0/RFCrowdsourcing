# 添加当前路径至解释器，确保单元测试时可正常import其它文件
import os
import sys

current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 基于顶层包的import
from prototype.task.cifar10_tagging import CIFAR10Task
from prototype.system_interface import SystemInterface


# 该类的每个对象对应一组实验参数的实验
class EvalGasCost:
    def __init__(self, eval_paras):
        # 启动分布式系统
        task = CIFAR10Task("CIFAR10 tagging", eval_paras["submitter_num"])
        self.system = SystemInterface(
            task,
            self.__server,
            submitter_num=eval_paras["submitter_num"],
            randomizer_num=eval_paras["randomizer_num"],
            subtask_num=eval_paras["subtask_num"],
            re_enc_num=eval_paras["re_enc_num"],
        )

    def start(self):
        self.system.run()
        # 要求submitter开始执行任务
        for id in range(self.system.SUBMITTER_NUM):
            self.system.call_submitter(id, "start", False)

    def __server(self, instruction, conn, addr):
        if instruction == "event/TASK_END":
            print("event/TASK_END")
            self.__collect_gas_cost()

    def __collect_gas_cost(self):
        gas_requester = self.system.call_requester("get/gas_cost")
        gas_submitter = []
        gas_randomizer = []
        for id in range(self.system.SUBMITTER_NUM):
            gas_submitter.append(self.system.call_submitter(id, "get/gas_cost"))
        for id in range(self.system.RANDOMIZER_NUM):
            gas_randomizer.append(self.system.call_randomizer(id, "get/gas_cost"))

        print("requester:", gas_requester)
        print("submitter:", gas_submitter)
        print("randomizer:", gas_randomizer)


if __name__ == "__main__":
    # 准备实验参数
    settings = [
        {"submitter_num": 1, "randomizer_num": 1, "subtask_num": 10, "re_enc_num": 1},
        {"submitter_num": 10, "randomizer_num": 10, "subtask_num": 50, "re_enc_num": 3},
        {
            "submitter_num": 100,
            "randomizer_num": 20,
            "subtask_num": 100,
            "re_enc_num": 3,
        },
    ]

    # 初始化实验
    Eval = EvalGasCost(settings[0])

    # 开始实验
    Eval.start()
