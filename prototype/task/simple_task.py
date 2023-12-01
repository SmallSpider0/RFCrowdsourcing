# 添加当前路径至解释器，确保单元测试时可正常import其它文件
import os
import sys

current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 基于顶层包的import
from utils.tools import split_array
from task.task_interface import AnswerInterface, TaskInterface, SubTaskInterface

# 系统库
import json
import time
from multiprocessing import Lock


class SimpleAnswer(AnswerInterface):
    """任务回答"""
    def __init__(self, content: int):
        self.content = content

    def validate(self):
        # 对答案内容进行简单的有效性检查
        return isinstance(self.content, int)

    def encode(self):
        return bytearray(self.content.to_bytes(8, byteorder='big', signed=True))

    @classmethod
    def from_encoding(cls, encoded):
        content = int.from_bytes(encoded, byteorder='big', signed=True)
        return cls(content)

    @classmethod
    def merge(self, answers):
        ret = 0
        for answer in answers:
            ret += answer.content
        return ret


class SimpleSubtask(SubTaskInterface):
    """子任务"""

    def __init__(self, id, description, content):
        self.id = id
        self.description = description
        self.content = content

    def execute(self):
        """执行单个子任务"""
        time.sleep(0.5)  # 模拟操作时间
        ret = len(self.content)  # 这里简单的求和为例
        return SimpleAnswer(ret)

    def __str__(self):
        return json.dumps(
            {"id": self.id, "description": self.description, "content": self.content}
        )

    @classmethod
    def from_str(cls, s):
        obj = json.loads(s)
        return cls(obj["id"], obj["description"], obj["content"])


# 一个简单的累加任务
# 子任务为一个整数数组的切片，回答为切片的求和
class SimpleTask(TaskInterface):
    def __init__(self, description, data, subtasks_num):
        self.description = description
        self.data = data  # 假设是一个数据集list
        self._subtasks_num = subtasks_num
        self.subtasks = self.__create_subtasks(subtasks_num)
        self.current_subtask_index = 0
        self.lock = Lock()

    @property
    def subtasks_num(self):
        return self._subtasks_num

    @classmethod
    def SUBTASK_CLS(self):
        return SimpleSubtask

    @classmethod
    def ANSWER_CLS(self):
        return SimpleAnswer

    def __create_subtasks(self, num):
        splited_tasks = split_array(self.data, num)
        return [
            SimpleSubtask(i, self.description + f" - Subtask {i}", splited_tasks[i])
            for i in range(num)
        ]

    def get_subtasks(self):
        with self.lock:
            if self.current_subtask_index < len(self.subtasks):
                subtask = self.subtasks[self.current_subtask_index]
                self.current_subtask_index += 1
                return subtask
            return None

    def evaluation(self, answers):
        """评估子任务的回答"""
        valid_answers = []
        valid_answers_indexes = []
        index = 0
        for answer in answers:
            if answer.validate():
                valid_answers.append(answer)
                valid_answers_indexes.append(index)
            index += 1
        final_answer = self.ANSWER_CLS().merge(valid_answers)
        return valid_answers_indexes, final_answer


if __name__ == "__main__":

    def test_simple_task():
        # 创建一个任务实例
        task = SimpleTask("Example task", list(range(100)), 5)

        answers = []

        while True:
            subtask = task.get_subtasks()
            if subtask == None:
                break
            answer = subtask.execute()
            answers.append(answer)

        # 评估答案
        indexes, answer = task.evaluation(answers)
        print(indexes)
        print(str(answer))

    test_simple_task()
    # ans = SimpleAnswer(2333)
    # print(ans.content)
    # encoded = ans.encode()
    # decoded = SimpleAnswer.from_encoding(encoded)
    # print(decoded.content)
