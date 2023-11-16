from abc import ABC, abstractmethod

class AnswerInterface(ABC):
    @abstractmethod
    def validate(self):
        '''验证答案的有效性'''
        pass

    @abstractmethod
    def __str__(self):
        '''将回答转为字符串'''
        pass

    @classmethod
    @abstractmethod
    def from_str(cls, s):
        '''从字符串初始化Answer对象'''
        pass

class SubTaskInterface(ABC):
    @abstractmethod
    def execute(self, subtask):
        """执行单个子任务并获取回答"""
        pass

    @abstractmethod
    def __str__(self):
        '''将任务转为字符串'''
        pass

    @classmethod
    @abstractmethod
    def from_str(cls, s):
        '''从字符串初始化任务对象'''
        pass

class TaskInterface(ABC):
    @abstractmethod
    def get_subtasks(self):
        """获取一个子任务"""
        pass
    
    @classmethod
    @abstractmethod
    def evaluation(cls, answers):
        """输入一轮中的所有回答，并评估它们的正确性"""
        pass