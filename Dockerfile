# 使用官方Python运行时作为父镜像
FROM python:3.8

# 设置工作目录
WORKDIR /usr/src/app

# 将当前目录内容复制到位于容器内的/usr/src/app目录
COPY config ./config
COPY prototype ./prototype
COPY tmp/keypairs ./tmp/keypairs
COPY tmp/cifar-10-batches-py ./tmp/cifar-10-batches-py
COPY requirements.txt .
COPY start_manager.py .

# 安装项目依赖
RUN pip install --no-cache-dir -r requirements.txt

# 使端口可供此容器外的环境使用
EXPOSE 1-65535

# 在容器启动时运行Python应用
CMD ["python", "./start_manager.py"]