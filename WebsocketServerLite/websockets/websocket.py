# -*- coding: utf-8 -*-
import base64
import hashlib
import struct


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
        self.textMode = opcode is 1
        return (encoded, fin, opcode)