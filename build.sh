#!/bin/bash

# 构建管理器
build_manager(){
    docker build -f "./Dockerfile.manager" --platform linux/amd64 -t rf-crowdsourcing-manager:amd64 .
    docker tag rf-crowdsourcing-manager:amd64 xzc2034222/rf-crowdsourcing-manager:amd64
}

# 构建区块链和ipfs环境
build_envs(){
    cp ./envs/ipfs/bin/ipfs-amd64 .build/ipfs
    cp ./envs/mychain/bin/geth-amd64 .build/geth
    docker build -f "./Dockerfile.envs" --platform linux/amd64 -t rf-crowdsourcing-envs:amd64 .
    docker tag rf-crowdsourcing-envs:amd64 xzc2034222/rf-crowdsourcing-envs:amd64
}

while getopts ":b:r:p:h" optname; do
    case "$optname" in
    "b")
        mkdir .build
        if [ "$OPTARG" = "manager" ]; then
            build_manager;
        elif [ "$OPTARG" = "envs" ]; then
            build_envs; 
        elif [ "$OPTARG" = "a" ]; then
            build_manager;
            build_envs;
        fi
        rm -rf .build
        ;;
    "r")
        if [ "$OPTARG" = "manager" ]; then
            # 获取宿主机的CPU架构
            architecture=$(uname -m)
            # 根据架构选择并运行相应的Docker镜像
            case $architecture in
            x86_64)
                echo "Running amd64 Docker image..."
                docker run -d --name manager --net=host xzc2034222/rf-crowdsourcing-manager:amd64
                ;;
            *)
                echo "Unsupported architecture: $architecture"
                exit 1
                ;;
            esac
        elif [ "$OPTARG" = "envs" ]; then
            # 获取宿主机的CPU架构
            architecture=$(uname -m)
            # 根据架构选择并运行相应的Docker镜像
            case $architecture in
            x86_64)
                echo "Running amd64 Docker image..."
                docker run -d --name envs --net=host xzc2034222/rf-crowdsourcing-envs:amd64
                ;;
            *)
                echo "Unsupported architecture: $architecture"
                exit 1
                ;;
            esac
        fi
        ;;
    "p")
        docker login
        # amd64
        if [ "$OPTARG" = "manager" ]; then
            docker push xzc2034222/rf-crowdsourcing-manager:amd64
        elif [ "$OPTARG" = "envs" ]; then
            docker push xzc2034222/rf-crowdsourcing-envs:amd64
        elif [ "$OPTARG" = "a" ]; then
            docker push xzc2034222/rf-crowdsourcing-manager:amd64
            docker push xzc2034222/rf-crowdsourcing-envs:amd64
        fi
        ;;
    "h")
        echo "eg:./build.sh -t m"
        ;;
    ":")
        echo "No argument value for option $OPTARG"
        ;;
    "?")
        echo "Unknown option $OPTARG"
        ;;
    *)
        echo "Unknown error while processing options"
        ;;
    esac
done
