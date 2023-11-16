from prototype.task.simple_task import SimpleTask


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