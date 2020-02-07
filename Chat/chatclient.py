# -*- coding: utf-8 -*-
import time,base64,hashlib,json,signal,sys,argparse,websocket,asyncio,_thread
from urllib.parse import quote,unquote
log = print
global UserID,status,token
token = ''
status = True
UserID = 0
def on_message(ws, message):
    raw_data = json.loads(message)
    global UserID
    if(raw_data['info'] == 'startChat'):
        UserID = int(raw_data['userid'])
    info = '[{0}] {1} Online:{2} '
    msg = '[Recv] {0} User ID: {1} >:{2}'
    chatdata = unquote(unquote(raw_data['chatdata']))
    if(len(raw_data['chatdata'])>0):
        log(msg.format(raw_data['time'],raw_data['userid'],chatdata))
    else:
        log(info.format(raw_data['status'],raw_data['info'],raw_data['online']))
    log('[Your ID:{0}] >:'.format(UserID))
def on_error(ws, error):
    log(error)
def on_open(ws):
    global token
    ws.send(token)
    def run():
        Chat(ws)
    _thread.start_new_thread(run, ())
    log('[INFO] Client Running!')
def on_close(ws):
    global status
    status = False
    ws.close()
    log('[INFO] Client Exit Success!')
def Chat(client):
    message = {
        "chatdata":'',
        "time":'',
        "token":token,
    }
    global status,UserID
    while status:
        chatdata = input('')
        message['chatdata'] = quote(chatdata)
        message['time'] = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()) 
        client.send(json.dumps(message))
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default=9001, type=int,help="This is Chat Server Port.")
    parser.add_argument('--server', default="127.0.0.1", type=str,help="This is Chat Server IP.")
    parser.add_argument('--token', default="", type=str,help="This is Chat Server Login token.")
    args = parser.parse_args()
    #websocket.enableTrace(True)
    if isinstance(args.port, int):
        client = 0 
        token = args.token
        if isinstance(args.server, str):
            client = websocket.WebSocketApp('ws://'+args.server+':'+str(args.port),on_message=on_message,on_error=on_error,on_close=on_close,on_open=on_open)
            client.run_forever()
        def signalHandler(s, frame):
            if s == signal.SIGINT:
                client.close()
        signal.signal(signal.SIGINT, signalHandler)