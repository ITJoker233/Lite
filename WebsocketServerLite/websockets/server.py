# -*- coding: utf-8 -*-
import socket
from websockets.wsclient import Wsclient
from websockets.wsthread import WebsocketThread


class SocketServer():
    port = 0
    clientid = 0
    clients = []
    threads = []
    socketConn = 0
    connected = False
    status = False
    def __init__(self, address, port):
        self.port = port
        self.socketConn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socketConn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socketConn.bind(("", port))
        self.socketConn.listen(1)

    def stopListening(self):
        self.connected = False
        for thread in self.threads:
            thread.stop()
        for client in self.clients:
            client.socket.close()
        self.socketConn.close()
        print("Websocket Server Stopped Listening")

    def startListening(self):
        self.connected = True
        print(("Websocket Server Started on Port {0}".format(self.port)))
        while self.connected:
            channel, details = self.socketConn.accept()
            self.status = True
            client = Wsclient(channel, self.clientid,self.status)
            self.clientid = self.clientid + 1
            self.clients.append(client)
            thread = WebsocketThread(channel, details, client,self)
            thread.start()
            self.threads.append(thread)
