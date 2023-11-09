class Randomizer:
    # 类变量
    name = ''

    # 构造函数
    def __init__(self, name):
        self.name = name

    # 启动节点
    def start(self):
        # 1.启动监听器，监听特定事件
        pass

    # 【内部函数】监听器的处理函数，接收任务并处理
    def __handle_event(self, event):
        # 1.监听event，等待前一顺位的Randomizers提交重加密结果
        # 2.根据智能合约中存储的pointer，从分布式文件存储服务下载回答密文
        # 3.调用__re_encryption进行重加密
        # 4.调用__submit_results提交重加密结果
        pass

    # 【内部函数】执行重加密
    def __re_encryption(self, parameters):
        # 1.生成随机数，对回答进行重加密，随后销毁随机数
        # 2.生成重加密NIZKP

        # 返回重加密结果
        pass

    # 【内部函数】提交重加密结果
    def __submit_results(self, results):
        # 1.将重加密结果和NIZKP上传分布式数据库，并获取文件pointer
        # 2.计算重加密结果和NIZKP的承诺，与文件pointer一起上传区块链
        pass


if __name__=="__main__":
    A = Randomizer(1)