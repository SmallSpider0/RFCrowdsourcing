# 添加当前路径至解释器，确保单元测试时可正常import其它文件
import os
import sys
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 基于顶层包的import
from utils.tools import split_array
from task.task_interface import AnswerInterface, TaskInterface, subTaskInterface

# 一个简单的累加任务
# 子任务为一个整数数组的切片，回答为切片的求和
class SimpleTask(TaskInterface):
    """任务回答的内部类"""
    class SimpleAnswer(AnswerInterface):
        def __init__(self, content):
            self.content = content

        def validate(self):
            # 对答案内容进行简单的有效性检查
            return isinstance(self.content, int)
        
        def __str__(self):
            return str(self.content)
        
        @classmethod
        def from_str(cls, s):
            content = int(s)
            return cls(content)

    class SimpleSubtask(subTaskInterface):
        """子任务的内部类"""
        def __init__(self, description, content):
            self.description = description
            self.content = content

        def execute(self):
            """执行单个子任务"""
            ret = sum(self.content) # 这里简单的求和为例
            return SimpleTask.SimpleAnswer(ret)

    def __init__(self, description, data, subtasks_num):
        self.description = description
        self.data = data # 假设是一个数据集list
        self.subtasks = self.subtask_iter(subtasks_num)

    def subtask_iter(self, num):
        splited_tasks = split_array(self.data, num)
        for i in range(num):
            yield SimpleTask.SimpleSubtask(self.description + f" - Subtask {i}", splited_tasks[i])    

    def get_subtasks(self):
        try:
            return next(self.subtasks)
        except StopIteration:
            return None  # 或者处理异常的其他方式

    @classmethod
    def evaluation(cls, answers):
        """评估子任务的回答"""
        valid_answers = [answer for answer in answers if answer.validate()]
        return valid_answers

if __name__ == "__main__":    
    def test_simple_task():
        # 创建一个任务实例
        task = SimpleTask("Example task", list(range(100)),5)

        answers = []

        while True:
            subtask = task.get_subtasks()
            if subtask == None: 
                break
            answer = subtask.execute()
            answers.append(answer)
            
        # 评估答案
        for answer in SimpleTask.evaluation(answers):
            print(answer)

    test_simple_task()