# -*- coding: utf-8 -*-
import time
class Wsclient:
    clientid = 0
    socket = 0
    status = False
    lastTimeSeen = time.time()
    def __init__(self, socket, clientid,status):
        self.clientid = clientid
        self.socket = socket
        self.status = status
