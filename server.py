import logging
import sys
import socketserver
import socket
import threading
import datetime

from resp import RespHandler

logging.basicConfig(format="%(asctime)s %(thread)d %(threadName)s %(message)s", stream=sys.stdout, level=logging.INFO)


class ServerHandler(socketserver.BaseRequestHandler):

    def setup(self) -> None:
        self.event = threading.Event()
        super(ServerHandler, self).setup()
        logging.info("新加入了一个链接{}".format(self.client_address))
        self.client_port = self.client_address[1]
        self.client_host = self.client_address[0]
        self.host_log_name = str(self.client_host) + "_" + str(
            datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")) + ".log"

    def handle(self) -> None:
        super(ServerHandler, self).handle()
        sk: socket.socket = self.request

        resp = RespHandler()
        count = 0
        while not self.event.isSet():
            try:
                data = sk.recv(1024)
                print(data)
                command = data.decode("utf8")
                self.log_write(cmd=command)
                result = resp.handle_command(command)
                self.log_write(result=result)
                sk.send(result)
            except Exception as e:
                logging.info(e)
                break

            logging.info(data)

    def finish(self):
        super(ServerHandler, self).finish()
        self.event.set()
        self.request.close()

    # 日志写入
    def log_write(self, cmd=None, result=None):
        if cmd is not None:
            log = f"[execute][{self.client_host}:{self.client_port}]" \
                  f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {cmd}".replace("\r\n", "\\r\\n")
        else:
            result = result.decode("utf8")
            log = f"[return][{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {result}".replace("\r\n",
                                                                                                        "\\r\\n")

        with open(self.host_log_name, "a") as f:
            f.write(log + "\n")


if __name__ == '__main__':
    server = socketserver.ThreadingTCPServer(("127.0.0.1", 3998), ServerHandler)
    # 异步调度
    threading.Thread(target=server.serve_forever, name="server").start()
    # 同步调试时使用
    # server.serve_forever()
    while True:
        cmd = input(">>> ")
        if cmd.strip() == "quit":
            server.shutdown()
            server.server_close()
            print("bye")
            break
        logging.info(threading.enumerate())
