# -*- coding: utf-8 -*-
from websockets.server import SocketServer
import signal
import sys
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default=9001, type=int,help="The port the server should listen on.")
    args = parser.parse_args()

    if isinstance(args.port, int):
        server = SocketServer("localhost", args.port)
        def signalHandler(s, frame):
            if s == signal.SIGINT:
                server.stopListening()
                print('Server Stoped!')
                sys.exit(0)
        signal.signal(signal.SIGINT, signalHandler)
        server.startListening()
