# -*- coding: utf-8 -*-
import socket,time,base64,hashlib,struct,threading,json,signal,sys,argparse,httplite
from urllib.parse import quote,unquote
global client_list
client_list = []
class Websocket:
    finished = False
    opcode = 0
    textMode = True
    binairyMode = True
    def __init__(self):
        pass
    def recv_data(self, channel, length):
        data = channel.recv(length)
        return data
    def get_headers(self, data):
        host = origin = key = final_line = ""
        lines = data.splitlines()
        for line in lines:
            parts = str(line, encoding='utf8').split(": ")
            if parts[0] == "Sec-WebSocket-Key":
                key = parts[1]
            elif parts[0] == "Host":
                host = parts[1]
            elif parts[0] == "origin":
                origin = parts[1]
        final_line = lines[len(lines) - 1]
        return (host, origin, key, final_line)
    def do_handshake(self, channel):
        shake = self.recv_data(channel, 1024)
        headers = self.get_headers(shake)
        wsid = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11".encode('utf-8')
        key = headers[2].encode('utf-8')
        response = base64.b64encode(hashlib.sha1(key + wsid).digest())
        response = str(response, encoding='utf8')
        handshake = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            "Sec-WebSocket-Accept: %s\r\n\r\n") % response
        channel.send(bytes(handshake, 'UTF-8'))
    def encode_data(self, fin, msg):
        if fin:
            finbit = 0x80
        else:
            finbit = 0
        opcode = 0x1
        frame = struct.pack("B", finbit | opcode)
        l = len(msg)
        if l < 126:
            frame += struct.pack("B", l)
        elif l <= 0xFFFF:
            frame += struct.pack("!BH", 126, l)
        else:
            frame += struct.pack("!BQ", 127, l)
        frame += msg.encode('utf-8', "replace")
        return frame
    def decode_data(self, msg):
        message = bytearray(msg)
        codeLength = len(message[1:])
        masks = 0
        data = 0
        firstbyte = message[0]
        opcode = firstbyte
        fin = firstbyte >= 128
        if fin:
            opcode -= 128
        if codeLength == 126:
            masks = message[4:8]
            data = message[8:]
        elif codeLength == 127:
            masks = message[10:14]
            data = message[14:]
        else:
            masks = message[2:6]
            data = message[6:]
        for x in range(len(data)):
            data[x] = data[x] ^ masks[x % 4]
        encoded = data
        if opcode == 1:
            encoded = str(data, encoding='utf-8')
        self.finished = fin
        self.opcode = opcode
        self.textMode = opcode == 1
        return (encoded, fin, opcode)
class Wsclient:
    clientid = 0
    socket = 0
    lastTimeSeen = time.time()
    status = False
    def __init__(self, socket, clientid,status):
        self.clientid = clientid
        self.socket = socket
        self.status = status
class WebsocketThread(threading.Thread):
    connected = True
    client = 0
    channel = 0
    details = 0
    server = 0
    token = ''
    websocket = Websocket()
    message__ = {
            "userid":0,
            "chatdata":'',
            "info":'',
            "status":'',
            "time":'',
            "token":'',
            "online":0,
        }
    def __init__(self, channel, details, client, token,server):
        super(WebsocketThread, self).__init__()
        self.channel = channel
        self.details = details
        self.client = client
        self.server = server
        self.token= token
    def run(self):
        self.connected = True
        msg = "[INFO] "+time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()) + " Client ID:{0} Connected at {1}"
        print((msg.format(self.client.clientid, self.details[0])))
        self.websocket.do_handshake(self.channel)
        encodeddata = self.channel.recv(8192)
        data = self.websocket.decode_data(encodeddata)
        message_ = self.message__
        if(self.token != data[0]):
            message_['status'] = 'error'
            message_['info'] = "Token Error!"
            send_data = self.websocket.encode_data(True,json.dumps(message_))
            self.channel.send(send_data)
            client_list.remove(self.client)
            self.stop()
            msg = "[INFO] {0} Client IP:{1} ID: {2} Login Error [*] Online:{3}"
            print((msg.format(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()),self.details[0], self.client.clientid,len(client_list))))
        else:
            msg = self.message__
            msg['userid'] = self.client.clientid
            msg['status'] = 'normal'
            msg['chatdata'] = ''
            msg['info'] = 'startChat'
            msg['time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            send_message = json.dumps(msg)
            response = self.websocket.encode_data(True, send_message)
            self.channel.send(response)
            message_ = self.message__
            message_['online'] = len(client_list) - 1
            message_['userid'] = self.client.clientid
            message_['status'] = 'success'
            msg['chatdata'] = ''
            message_['info'] = "UserID: {0} 加入聊天".format(self.client.clientid)
            message_['time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            for cli in client_list:
                if self.client.clientid != cli.clientid:
                    send_data = self.websocket.encode_data(True,json.dumps(message_))
                    cli.socket.send(send_data)
            while self.connected:
                self.message(self.channel)
    def stop(self):
        self.connected = False
        self.client.status = False
        self.channel.close()
    def message(self, channel):
        encodeddata = channel.recv(8192)
        data = self.websocket.decode_data(encodeddata)
        message_ = self.message__
        if is_json(data[0]):
            json_obj = json.loads(data[0])
        message_['userid'] = self.client.clientid
        if data[2] == 8:
            msg = "[INFO] {0} Client ID:{1} Closed Connecting! LastTimeSeen:{2}"
            print(msg.format(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()),self.client.clientid, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.client.lastTimeSeen))))
            client_list.remove(self.client)
            self.channel.close()
            message_['status'] = 'warning'
            message_['online'] = len(client_list)
            message_['info'] = "用户ID为: {0} 退出聊天室！".format(self.client.clientid)
            message_['time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            for cli in client_list:
                send_data = self.websocket.encode_data(True,json.dumps(message_))
                cli.socket.send(send_data)
            self.connected = False
        else:
            if(self.token != json_obj['token']):
                message_['status'] = 'error'
                message_['info'] = "Token Error!"
                send_data = self.websocket.encode_data(True,json.dumps(message_))
                channel.send(send_data)
                client_list.remove(self.client)
                self.stop()
                msg = "[INFO] {0} Client IP:{1} ID: {2} Login Error [*] Online:{3}"
                print((msg.format(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()),self.details[0], self.client.clientid,len(client_list))))
            else:
                msg = "[INFO] {0} Client IP:{1} ID: {2} On Chatting [*] Online:{3}"
                print((msg.format(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()),self.details[0], self.client.clientid,len(client_list))))
                chatdata = quote(json_obj['chatdata'])
                if chatdata != '':
                    message_['online'] = len(client_list)
                    for cli in client_list:
                        info = 'None'
                        if self.client.clientid != cli.clientid:
                            message_['info'] = info
                            message_['status'] = 'normal'
                            message_['chatdata'] = chatdata
                            message_['time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                            send_data = self.websocket.encode_data(True,json.dumps(message_))
                            cli.socket.send(send_data)
                    channel.send(self.websocket.encode_data(True,json.dumps({"userid":self.client.clientid,"online":len(client_list),"info":''})))
class SocketServer():
    port = 0
    clientid = 1
    threads = []
    socketConn = 0
    connected = False
    def __init__(self, address, port):
        self.port = port
        self.socketConn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socketConn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socketConn.bind(("", port))
        self.socketConn.listen(1)
    def stopListening(self):
        global client_list
        self.connected = False
        for thread in self.threads:
            thread.stop()
        for client in client_list:
            client.socket.close()
        self.socketConn.close()
        print("Chat Server Stopped Listening")
    def startListening(self):
        global client_list
        self.connected = True
        token = hashlib.md5(base64.b64encode('ChatServer {0} 233'.format(time.time()).encode("utf-8"))).hexdigest()#密钥
        print("Chat Server Started on Port {0}\nToken >{1}".format(self.port,token))
        while self.connected:
            channel, details = self.socketConn.accept()
            client = Wsclient(channel, self.clientid,True)
            client_list.append(client)
            self.clientid = self.clientid + 1
            thread = WebsocketThread(channel, details, client, token , self)
            thread.start()
            self.threads.append(thread)
def is_json(myjson):
    try:
       json.loads(myjson)
    except ValueError:
       return False
    return True
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default=9001, type=int,help="The port the server should listen on.")
    args = parser.parse_args()
    if isinstance(args.port, int):
        server = SocketServer("0.0.0.0", args.port)
        def signalHandler(s, frame):
            if s == signal.SIGINT:
                server.stopListening()
                sys.exit(0)
        signal.signal(signal.SIGINT, signalHandler)
        server.startListening()
