from abc import ABC, abstractmethod

class AnswerInterface(ABC):
    @abstractmethod
    def validate(self):
        '''验证答案的有效性'''
        pass

    @abstractmethod
    def encode(self):
        '''将回答转为bytearray'''
        pass

    @classmethod
    @abstractmethod
    def from_encoding(cls, s):
        '''从bytearray还原回答'''
        pass

    @classmethod
    @abstractmethod
    def merge(cls, answers):
        '''聚合Answer对象'''
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
    @property
    @abstractmethod
    def subtasks_num(self):
        """返回子任务的数量"""
        pass

    @classmethod
    @abstractmethod
    def SUBTASK_CLS(cls):
        """返回子任务的类"""
        pass
    
    @classmethod
    @abstractmethod
    def ANSWER_CLS(cls):
        """返回子任务回答的类"""
        pass

    @abstractmethod
    def get_subtasks(self):
        """获取一个子任务"""
        pass
    
    @abstractmethod
    def evaluation(self, answers):
        """输入一轮中的所有回答，评估它们的正确性，并返回各回答正确与否和最终聚合的结果"""
        pass