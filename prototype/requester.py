class Requester:
    # 类变量
    name = ''

    # 构造函数
    def __init__(self, name):
        self.name = name

    # 启动事件监听器
    def start(self):
        # 1.启动监听器，监听特定事件
        # 2.启动奖励发放器，执行随机延迟的奖励发放
        pass

    # 【内部函数】监听器的处理函数，接收重加密好的回答并处理
    def __handle_submission(self, event):
        # 1.监听event，等待最后顺位的Randomizers提交重加密结果
        # 2.根据智能合约中存储的pointer，从分布式文件存储服务下载重加密结果
        # 3.调用__verify_re_encryption验证重加密结果
        # 4.调用__answer_collection解密重加密结果并保存
        pass
    
    # 【内部函数】验证重加密结果有效性
    def __verify_re_encryption(self, submissions):
        # 1.验证序列中的各个submission的链上承诺无误
        # 2.验证各submission的NIZKP有效

        # 返回验证结果
        pass

    # 【内部函数】解密提交并保存，供后续奖励发放模块处理
    def __answer_collection(self, submissions):
        # 1.使用自己的私钥解密submissions中的回答
        # 2.将解密结果放入队列，供后续处理
        pass
    
    # 【内部函数】由奖励发放器调用，评估结果并处理奖励发放相关事宜
    def __evaluation(self, submissions):
        # 1.评估提交的正确性并保存正确的提交
        # 2.给诚实的参与者计算奖励
        # 3.使用随机延迟奖励发放算法给参与者发放奖励
        pass


if __name__=="__main__":
    A = Requester(1)