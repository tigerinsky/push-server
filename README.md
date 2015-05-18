部署说明
========

1. 安装virtualenv
2. 安装pip
3. 安装thrift
4. 项目跟目录下执行：
virtualenv venv
. venv/bin/activate
pip install -r requirements.txt

cd src

thrift --gen python idl/push_server.thrift

python server.py

