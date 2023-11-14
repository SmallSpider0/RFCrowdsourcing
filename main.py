"""
秘钥管理

Randomizer 仅需保存Requester的公钥用于重加密; 

Requester 需要保存自己的公私钥;

Submitter 仅需保存Requester的公钥;

"""

# TODO：完成Requester模块，并与Randomizers模块联合测试 交互式证明

from prototype import ipfshttpclient
import pickle

# 连接到本地IPFS节点
client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')  # 确保这个地址和端口与你的IPFS配置匹配

# 示例：上传一个文件
file_hash = client.add('tmp/ciphertext.pkl')['Hash']  # 替换为你要上传的文件路径

# 示例：下载文件
download_path = 'tmp/IPFS_downloads'  # 设置下载文件的保存路径
client.get(file_hash, download_path)

with open(f"{download_path}/{file_hash}", 'rb') as f:
    tmp = pickle.load(f)
    print(tmp)

# QmR7sAkVj6SVPL7dzCUU5bJZbPRNB18WWwK1yuDsTGFKha
print(file_hash)