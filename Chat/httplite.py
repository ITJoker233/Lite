import socket,threading,os,time,json,hashlib
log = print
global STATIC_DIR
STATIC_DIR = ''
HEADER_CONTENT_TYPE = 'Content-Type:text/html; charset=UTF-8'
class Request():
    def __init__(self, orign_request, addr):
        self.path = None
        self.method = None
        self.signature = None
        self.headers = dict()
        self.body = None
        self.orignal_request = orign_request
        self.host, self.port = addr
        self.__parse_request__(orign_request)
    def __parse_request__(self, request):
        twopart = [x for x in request.split('\r\n\r\n') if x]
        self.__parse_headers_and_signature__(twopart[0])
        if len(twopart) == 2:
            self.body = twopart[1]
    def __parse_headers_and_signature__(self, headers_part):
        lines = headers_part.split("\r\n")
        self.signature = lines[0]
        for header in range(1, len(lines)):
            if lines[header].startswith('Host'):
                self.headers['Host'] = lines[header].split(":")[1:]
                continue
            item = lines[header].split(":", 2)
            self.headers[item[0]] = item[1].strip()
        self.method, self.path, *other = self.signature.split(' ')
class Response():
    def __init__(self, status=200, headers={}, body=None, message='ok', RESPONSE_FIRST_VERSION='HTTP/1.0'):
        self.status = status
        self.headers = headers
        self.body = body
        self.message = message
        self.RESPONSE_FIRST_VERSION = RESPONSE_FIRST_VERSION
    @classmethod
    def ok(cls, body=None):
        res = Response(body=body)
        res.body = body
        if body:
            res.headers['Content-Length'] = str(len(body))
        return res
    @classmethod
    def bad_request(cls):
        return Response(status=400, message='Bad Request')
    def headers_responses(self):
        signature = ' '.join([self.RESPONSE_FIRST_VERSION, str(self.status), self.message])
        headers_str = str()
        header_of_response = str()
        for title, content in self.headers.items():
            headers_str += ': '.join([title, content])+'\r\n'
        headers_str = headers_str[:-2]
        header_of_response += '\r\n'.join([signature, headers_str])+'\r\n\r\n'
        return bytes(header_of_response, encoding='utf-8')
    def data(self):
        body = self.body
        response = bytes('', encoding='utf-8')
        if body:
            response += body
        return response
def is_json(myjson):
   try:
      json_object = json.loads(myjson)
   except ValueError:
      return False
   return True
def read_file(filepath, type_):
    with open(filepath, type_) as file:
        result = file.read()
    return result
def file(page) -> bytes:
    path_ = os.path.join(STATIC_DIR, page)
    if not os.path.exists(path_):
        return read_file(os.path.join(STATIC_DIR, '404.html'), 'rb')
    elif not os.access(path_, os.X_OK):
        return b'403 Forbidden'
    if os.path.isfile(path_):
        body = read_file(path_, 'rb')
    else:
        body = read_file(path_+'/index.html', 'rb')
    return body
def handle_get_request(request) -> Response:
    path = request.path
    if path == '/':
        return Response.ok(body=file('index.html'))
    return Response.ok(body=file(path[1:]))
def handle_post_request(request) -> Response:
    headers = request.headers
    path = request.path
    body = request.body.split('\r\n')
    datas = b'<h1>error<h1>'
    if headers['Content-Type'].replace(' ', '') == 'application/json;charset=UTF-8' or headers['Content-Type'].replace(' ', '') == 'application/json;':
        error_data = json.dumps({'status': 0, 'message': 'error'})
        if path == '/chat?':
            if is_json(body[0]):
                json_data = json.loads(body[0])
                token = hashlib.md5( bytes(json_data['username'] + json_data['password']+'passwords',encoding='utf-8') ).hexdigest()
                success_data = json.dumps({'status': 1, 'message': 'success', 'token': token})
                datas = success_data
            else:
                datas = error_data
            datas = bytes(datas, encoding='utf-8')
        else:
            datas = error_data
    return Response.ok(body=datas)
def method_not_support(method) -> Response:
    try:
        body = file('method_not_support.html')
        return Response(405, body=body, message='Method %s Not Allowed' % method)
    except FileNotFoundError as e:
        return Response.bad_request()
def handle_request(request: Request) -> Response:
    if request.method.lower() == 'get':
        return handle_get_request(request)
    elif request.method.lower() == 'post':
        return handle_post_request(request)
    elif request.method.lower() == 'options':
        return Response().ok()
    return method_not_support(request.method.lower())
def after_handle_response(response):  # CROS
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers["Access-Control-Allow-Headers"] = ("Content-Type,Content-Length, Authorization, Accept,X-Requested-With")
    response.headers["Access-Control-Allow-Methods"] = "PUT,POST,GET,DELETE,OPTIONS"
def accept_socket(sock: socket, addr, REQUEST_MAX_LENGTH=1024 * 1024):
    ori_request = sock.recv(REQUEST_MAX_LENGTH)
    request = Request(ori_request.decode('utf-8'), addr)
    response = handle_request(request)
    after_handle_response(response)
    response_bytes = response.data()
    response_headers_bytes = response.headers_responses()
    sock.send(response_headers_bytes)
    sock.send(response_bytes)
    sock.close()
    log(' >>>>[INFO] '+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) +
        ' Accept Connection %s:%s   %s' % (addr[0], addr[1], request.signature,))
def start(host, port, static_dir='static'):
    global _main
    global STATIC_DIR
    STATIC_DIR = static_dir
    _main = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _main.bind((host, port))
    _main.listen()
    while True:
        sock, addr = _main.accept()
        threading.Thread(target=accept_socket, args=(sock, addr)).start()
if __name__ == "__main__":
    start("0.0.0.0", 9001, 'static')