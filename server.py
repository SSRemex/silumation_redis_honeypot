import logging
import sys
import socketserver
import socket
import threading

from resp import RespHandler

logging.basicConfig(format="%(asctime)s %(thread)d %(threadName)s %(message)s", stream=sys.stdout, level=logging.INFO)


class ServerHandler(socketserver.BaseRequestHandler):
    def setup(self) -> None:
        super(ServerHandler, self).setup()
        self.event = threading.Event()
        logging.info("新加入了一个链接{}".format(self.client_address))

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
                result = resp.handle_command(command)
                sk.send(result)
            except Exception as e:
                logging.info(e)
                break

            logging.info(data)

    def finish(self):
        super(ServerHandler, self).finish()
        self.event.set()
        self.request.close()


if __name__ == '__main__':
    server = socketserver.ThreadingTCPServer(("127.0.0.1", 3998), ServerHandler)
    # threading.Thread(target=server.serve_forever, name="server").start()
    server.serve_forever()
    while True:
        cmd = input(">>> ")
        if cmd.strip() == "quit":
            server.shutdown()
            server.server_close()
            print("bye")
            break
        logging.info(threading.enumerate())
