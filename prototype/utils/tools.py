def split_array(arr, n):
    """将数组拆分为最多n个相同大小的分片，最后一个分片大小可以不同。

    :param arr: 要拆分的数组。
    :param n: 分片的数量。
    :return: 包含分片的列表。
    """
    # 计算每个分片的大致大小
    size = len(arr) // n
    # 如果数组大小不能被n整除，最后一个分片需要增加一个元素
    size += 1 if len(arr) % n > 0 else 0

    # 生成分片
    return [arr[i:i + size] for i in range(0, len(arr), size)]