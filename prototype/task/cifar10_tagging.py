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
import numpy as np
import pickle
import random
import tarfile
import urllib.request
from multiprocessing import Lock


class CIFAR10Answer(AnswerInterface):
    """任务回答"""

    def __init__(self, content: list):
        self.content = content

    def validate(self):
        # 对答案内容进行简单的有效性检查
        for ans in self.content:
            if not isinstance(ans, int) or ans < 0 or ans > 9:
                return False
        return True

    def encode(self):
        encoded_bytes = bytes("".join(str(num) for num in self.content), "ascii")
        return bytearray(encoded_bytes)

    @classmethod
    def from_encoding(cls, encoded):
        decoded_int_array = [int(char) for char in encoded.decode("ascii")]
        return cls(decoded_int_array)

    @classmethod
    def merge(self, answers):
        # 简单计算总回答数量
        cnt = 0
        for ans in answers:
            cnt += len(ans.content)
        return f"{cnt} tags"


class CIFAR10Subtask(SubTaskInterface):
    """子任务"""

    def __init__(self, id, description, content):
        self.id = id
        self.description = description
        self.content = content

    def execute(self):
        """执行单个子任务"""
        # time.sleep(0.5)  # 模拟操作时间
        ret = [random.randint(0, 9) for _ in range(len(self.content))]  # 这里返回随机值为例
        return CIFAR10Answer(ret)

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
class CIFAR10Task(TaskInterface):
    def __init__(self, description, subtasks_num):
        # 获取CIFAR10数据集
        self.download_and_extract_cifar10("tmp")
        batches = []
        for i in range(1, 6):
            batch = self.__unpickle(f"tmp/cifar-10-batches-py/data_batch_{i}")
            batches.append(batch[b"data"])
            # 额外加入一个数据集BATCH
            if i == 5:
                batches.append(batch[b"data"])

        # 初始化类变量
        self.description = description
        self.data = np.concatenate(batches).tolist()
        self._subtasks_num = subtasks_num
        self.subtasks = self.__create_subtasks(subtasks_num)
        self.current_subtask_index = 0
        self.lock = Lock()

    def __unpickle(self, file):
        with open(file, "rb") as fo:
            dict = pickle.load(fo, encoding="bytes")
        return dict

    def download_and_extract_cifar10(self, target_dir):
        # CIFAR-10数据集的URL
        url = "http://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz"
        # 数据集的文件名
        filename = url.split("/")[-1]
        # 完整的下载路径
        file_path = os.path.join(target_dir, filename)
        # 解压后的目录名
        extracted_dir_path = os.path.join(target_dir, "cifar-10-batches-py")

        # 检查数据集是否已经存在
        if not os.path.exists(extracted_dir_path):
            # 检查目标目录是否存在，如果不存在则创建
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

            # 下载数据集
            print("Downloading CIFAR-10 dataset...")
            urllib.request.urlretrieve(url, file_path)

            # 解压数据集
            print("Extracting data...")
            with tarfile.open(file_path, "r:gz") as tar:
                tar.extractall(path=target_dir)

            # 删除下载的压缩包
            os.remove(file_path)

            print("Download and extraction complete!")

    @property
    def subtasks_num(self):
        return self._subtasks_num

    @classmethod
    def SUBTASK_CLS(self):
        return CIFAR10Subtask

    @classmethod
    def ANSWER_CLS(self):
        return CIFAR10Answer

    def __create_subtasks(self, num):
        splited_tasks = split_array(self.data, num)
        # 模拟发送任务 以节省流量
        return [
            CIFAR10Subtask(
                i,
                self.description + f" - Subtask {i}",
                [0 for _ in range(len(splited_tasks[i]))],
            )
            for i in range(num)
        ] * 3

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

    def test_task():
        # 创建一个任务实例
        task = CIFAR10Task("Example task", 10)

        answers = []

        while True:
            subtask = task.get_subtasks()
            if subtask == None:
                break
            answer = subtask.execute()
            answers.append(answer)

        # 评估答案
        indexes, answer = task.evaluation(answers)
        # print(len(answer))
        print(str(answer))

    test_task()
    # ans = CIFAR10Answer([0, 2, 0, 4, 5])
    # print(ans.content)
    # encoded = ans.encode()
    # decoded = CIFAR10Answer.from_encoding(encoded)
    # print(decoded.content)
