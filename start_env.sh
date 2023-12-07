#!/bin/bash

# 检查命令行参数
case "$1" in
    init)
        # 初始化环境脚本内容
        find "envs/logs" -mindepth 1 ! -name ".gitkeep" -exec rm -f {} \;
        cd envs/ipfs && ./0-init.sh
        cd ../mychain && ./0-init.sh
        echo "Environment initialization successful"
        ;;
    up)
        # 启动环境脚本内容
        echo "Starting environments ..."
        cd envs/mychain && ./1-node1.sh && ./1-node2.sh  && ./1-node3.sh
        cd ../ipfs && ./1-start.sh
        echo "Environment startup successful"
        tail -f ../logs/bc_node1
        ;;
    down)
        # 停止环境脚本内容
        ps -ef | grep ./geth | grep -v grep | awk '{print $2}' | xargs kill
        ps -ef | grep ./ipfs | grep -v grep | awk '{print $2}' | xargs kill
        echo "Environment shutdown successful"
        ;;
    clean)
        # 执行清理
        cd tmp
        find "IPFS_downloads" -mindepth 1 ! -name ".gitkeep" -exec rm -f {} \;
        find "IPFS_uploads" -mindepth 1 ! -name ".gitkeep" -exec rm -f {} \;
        ;;
    *)
        # 错误处理
        echo "Usage: $0 {init|up|down}"
        exit 1
        ;;
esac
