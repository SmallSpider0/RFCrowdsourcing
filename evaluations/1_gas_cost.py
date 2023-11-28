# 大规模测试
SUBMITTER_NUM = 100  # 提交者数量
RANDOMIZER_NUM = 20  # 重加密者数量
SUBTASK_NUM = 1000  # 子任务数量
RE_ENC_NUM = 3  # 子任务需要的重加密次数

# 标准测试
# SUBMITTER_NUM = 5  # 提交者数量
# RANDOMIZER_NUM = 10  # 重加密者数量
# SUBTASK_NUM = 20  # 子任务数量
# RE_ENC_NUM = 2  # 子任务需要的重加密次数

# 最小系统
# SUBMITTER_NUM = 1  # 提交者数量
# RANDOMIZER_NUM = 1  # 重加密者数量
# SUBTASK_NUM = 10  # 子任务数量
# RE_ENC_NUM = 1  # 子任务需要的重加密次数

# 外部控制接口启动
def server_start():
    # 服务器功能定义
    def server(conn, addr):
        instruction = recvLine(conn)
        if instruction == "event/TASK_END":
            conn.close()
            collect_gas_cost()

    # 启动服务器
    threading.Thread(
        target=listen_on_port,
        args=(server, 20000),
    ).start()


def collect_gas_cost():
    gas_requester = call_requester("get/gas_cost")
    gas_submitter = []
    gas_randomizer = []
    for id in range(SUBMITTER_NUM):
        gas_submitter.append(call_submitter(id, "get/gas_cost"))
    for id in range(RANDOMIZER_NUM):
        gas_randomizer.append(call_randomizer(id, "get/gas_cost"))

    print("requester:", gas_requester)
    print("submitter:", gas_submitter)
    print("randomizer:", gas_randomizer)

if __name__ == "__main__":
    pass