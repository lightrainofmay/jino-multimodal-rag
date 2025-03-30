# 使用 Python 官方轻量镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 拷贝所有文件到容器中
COPY . .

# 安装依赖
RUN pip install --upgrade pip && \
  pip install -r requirements.txt && \
  pip install python-dotenv

# 暴露端口
EXPOSE 5000

# 运行应用
CMD ["python", "run.py"]
