

from prototype.utils.network import listen_on_port, connect_to, sendLine, recvLine
import threading



from prototype.task.cifar10_tagging import CIFAR10Task
# task = SimpleTask("This is a simple task", list(range(1, 1001)), SUBTASK_NUM)
task = CIFAR10Task("CIFAR10 tagging", SUBTASK_NUM)



def call_requester(data, need_ret = True):
    def handler(conn):
        sendLine(conn, data)
        if need_ret:
            ret = recvLine(conn)
            return ret
    return connect_to(handler, REUQESTER_SERVING_PORT)

def call_submitter(id , data, need_ret = True):
    def handler(conn):
        sendLine(conn, data)
        if need_ret:
            ret = recvLine(conn)
            return ret
    return connect_to(handler, SUBMITTER_SERVING_PORT_BASE + id)

def call_randomizer(id , data, need_ret = True):
    def handler(conn):
        sendLine(conn, data)
        if need_ret:
            ret = recvLine(conn)
            return ret
    return connect_to(handler, RANDOMIZER_SERVING_PORT_BASE + id)

server_start()

for id in range(SUBMITTER_NUM):
    call_submitter(id, "start", False)