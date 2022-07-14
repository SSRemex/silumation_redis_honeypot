import os
import sys
import re


class RespHandler:
    def __init__(self):
        # 用来临时存储数据的字典
        self.k_v_dict = {
            "admin": "12345"
        }
        self.command_log = []
        self.executable_command = {
            "ping": (self.ping, True),
            "get": (self.get, True),
            "set": (self.set, True),
            "keys": (self.keys, True),
            "auth": (self.auth, True),
            "del": (self.delete, True),
            "exists": (self.exists, True),
            "dbsize": (self.exists, True)

        }
        self.unexecutable_command = [
            "hget", "hset", "hdel", "hlen", "hexists", "hkeys", "hvals", "hgetall", "hincrby", "hincrbyfloat",
            "hstrlen", "shutdown", "expire", "expireat", "pexpire", "pexpireat", "ttl", "type", "rename", "renamenx",
            "randomkey", "move", "dump", "restore", "migrate", "scan", "select", "flushdb", "flushall", "mset", "mget",
            "incr", "decr", "append", "strlen", "getset", "setrange", "getrange", "rpush", "lpush", "linsert", "lrange",
            "lindex", "llen", "rpop", "lpop", "lrem", "lset", "blpop",

        ]
        self.danger_command = [
            "config"
        ]
        self.max_num = 100

    # 接受命令解析处理
    def _parser(self, command):
        command_list = command.split("\r\n")
        cache = {
            "cmd": None,
            "params": [],
        }

        command_list.pop()
        for index in range(1, len(command_list), 2):
            command = (command_list[index], command_list[index + 1])
            if index == 1:
                cache["cmd"] = command
            else:
                cache["params"].append(command)

        self.command_log.append(cache)
        return cache

    # 返回数据格式化处理
    def _format(self, result, error=False):
        if error:
            result_str = "-" + result + "\r\n"
        else:
            if type(result) == str:
                print(result)
                result_str = "+" + result + "\r\n"
            if type(result) == dict:
                print(result)
                length = len(result)
                result_str = "*" + str(length) + "\r\n"
                for k, v in result.items():
                    k_l = len(k)
                    result_str += "$" + str(k_l) + "\r\n" + str(k) + "\r\n"
                    v_l = len(v)
                    result_str += "$" + str(v_l) + "\r\n" + str(v) + "\r\n"

            if type(result) == int:
                print(result)
                result_str = "$" + str(result) + "\r\n"

        return result_str

    # 命令处理引擎
    def handle_command(self, command):
        cache = self._parser(command)
        cmd = cache.get("cmd")[1]
        try:
            if cmd in self.executable_command.keys():
                if self.executable_command.get(cmd)[1]:
                    result, error = self.executable_command.get(cmd)[0](cache)
                else:
                    result, error = self.finall_error()
            elif cmd in self.danger_command:
                # 埋点
                result, error = self.finall_error()

            elif cmd in self.unexecutable_command:
                result, error = self.finall_error()
            else:
                result, error = self.normal_error(cache)
        except Exception:
            result, error = self.finall_error()

        result = self._format(result, error=error).encode("utf8")
        print(f"result ==> {result}")
        return result

    # 可执行命令
    def ping(self, cache):
        return "PONG", False

    def get(self, cache):
        cmd = cache.get("cmd")
        params = cache.get("params")
        if len(params) == 1:
            result = self.k_v_dict.get(params[0][1])
            error = False
            if result is None:
                result = -1
        else:
            result = self._num_error(cmd)
            error = True
        print(f"get ==> {result}")
        return result, error

    def exists(self, cache):
        cmd = cache.get("cmd")
        params = cache.get("params")
        if len(params) == 1:
            result = self.k_v_dict.get(params[0][1])
            error = False
            if result is None:
                result = 0
            else:
                result = 1
        else:
            result = self._num_error(cmd)
            error = True
        print(f"exists ==> {result}")
        return result, error

    def dbsize(self, cache):
        cmd = cache.get("cmd")
        params = cache.get("params")
        if len(params) == 0:
            result = len(self.k_v_dict)
        else:
            result = self._num_error(cmd)
            error = True

        print(f"dbsize ==> {result}")
        return result, error

    def set(self, cache):
        cmd = cache.get("cmd")
        params = cache.get("params")
        if len(params) < 2:
            result, error = self._num_error(cmd)
        elif len(params) == 2:
            self.k_v_dict[params[0][1]] = params[1][1]
            loss = len(self.k_v_dict) - self.max_num
            if loss > 0:
                c = list(self.k_v_dict.items())
                self.k_v_dict = dict(c[loss:])
            result = "OK"
            error = False
        else:
            result = "ERR syntax error"
            error = True
        print(f"set ==> {result}")
        return result, error

    def keys(self, cache):
        cmd = cache.get("cmd")
        params = cache.get("params")
        if len(params) != 1:
            result, error = self._num_error(cmd)
        else:
            res_str = params[0][1]
            if res_str == "*":
                res_str = ".*"
            key_list = self.k_v_dict.keys()
            result = {}
            error = False
            for key in key_list:
                if re.match(res_str, key):
                    result[key] = self.k_v_dict.get(key)

            print(f"keys ==> {result}")

        return result, error

    def delete(self, cache):
        cmd = cache.get("cmd")
        params = cache.get("params")
        if len(params) < 1:
            result, error = self._num_error(cmd)
        else:
            count = 0
            error = False
            for param in params:
                try:
                    del self.k_v_dict[param]
                    count += 1
                except:
                    continue

            result = count

        print(f"delete ==> {result}")
        return result, error

    def auth(self, cache):
        error = True
        cmd = cache.get("cmd")
        params = cache.get("params")
        if len(params) < 1:
            result, error = self._num_error(cmd)
        elif len(params) == 1:
            result = "ERR AUTH <password> called without any password configured for the default user. Are you sure your configuration is correct?"
            error = True
        else:
            result = "WRONGPASS invalid username-password pair or user is disabled."

        return result, error

    # 错误信息
    def _num_error(self, cmd):
        error = True
        return f"ERR wrong number of arguments for '{cmd}' command", error

    def normal_error(self, cache):
        error = True
        args_str = ""
        for i in cache.get("params"):
            args_str += i[1] + ", "
        return f"ERR unknown command `{cache.get('cmd')[1]}`, with args beginning with: {args_str}", error

    # 针对不可执行命令的报错
    def finall_error(self):
        error = True
        result = "ERR Protocol error: invalid bulk length"
        return result, error


if __name__ == '__main__':
    a = RespHandler()

