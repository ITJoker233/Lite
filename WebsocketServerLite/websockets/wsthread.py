# -*- coding: utf-8 -*-
import threading,time
from websockets.websocket import Websocket

class WebsocketThread(threading.Thread):
    connected = True
    client = 0
    channel = 0
    details = 0
    server = 0
    websocket = Websocket()
    def __init__(self, channel, details, client, server):
        super(WebsocketThread, self).__init__()
        self.channel = channel
        self.details = details
        self.client = client
        self.server = server
    def run(self):
        self.connected = True
        msg = "[INFO] "+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) +" Server: Client ID:{0} Connected at {1}"
        print((msg.format(self.client.clientid, self.details[0])))
        self.websocket.do_handshake(self.channel)
        while self.connected:
            self.interact(self.channel)

    def stop(self):
        self.connected = False
        self.client.status = False
        self.channel.close()

    def interact(self, channel):
        encodeddata = channel.recv(8192)
        data = self.websocket.decode_data(encodeddata)
        if data[2] == 8:
            msg = "[INFO] "+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) +" Client ID:{0} closed Connecting!"
            print((msg.format(self.client.clientid)))
            self.client.status = False
            self.channel.close()
            self.connected = False
        else:
            msg = "[INFO] "+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) +" client IP:{0} ID: {1} Data: {2}"
            print((msg.format(self.details[0],self.client.clientid, data[0])))
            if data[0] != "":
                time.sleep(1)
                response = self.websocket.encode_data(True,time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
                channel.send(response)
