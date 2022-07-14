# silumation_redis_honeypot
仿真redis蜜罐探索

resp.py 伪造的redis协议
server.py 伪造的redis服务

`python3 server.py`

终端中输入 `redis-cli -p 3998` 即可连接

代码中注释埋点字样 可做一些告警操作

支持多客户端连接