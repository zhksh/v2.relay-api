from flask import Flask
from flask import request
import time
from logging.config import dictConfig
import logging as logger
import json
import logging as logger
# from flask_socketio import SocketIO
from queue import LifoQueue, Queue
from flask import render_template
from flask_socketio import SocketIO, emit
from flask_sock import Sock



dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {
                    "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
                }
            },
            "handlers": {
                "wsgi": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://flask.logging.wsgi_errors_stream",
                    "formatter": "default",
                }
            },
            "root": {"level": "DEBUG", "handlers": ["wsgi"]},
        }
    )
queue = Queue(maxsize=0)
queues = {}
app = Flask(__name__)
sock = Sock(app)






@app.before_request
def before_req():
    # logger.debug(request.headers)

    if "X-Real-Ip" in request.headers:
        logger.info(request.headers["X-Real-Ip"])
    try:
        logger.debug(json.loads(request.data))
    except:
        pass
wss = {}

@sock.route('/echo')
def echo(ws):
    id = request.args.get('id', type = int)
    q = Queue()
    queues[id] = {"ws": ws, "q" : q}
    while True:
        while q.qsize() > 0:
            if not ws.connected: 
                ws.close
                del queues[id]
            ws.send(q.get())
    
                

@app.route('/api/post-sensor-data', methods = ['GET', 'POST'])
def user():
    if request.method == 'GET':
        return {'time': time.time()}
    if request.method == 'POST':
        
        data = request.json # a multidict containing POST data
        
        logger.info(request.json)
        for id, ws in queues.items():
            ws['q'].put(request.json)
            
        return {"success" : "true"}

        

@app.route('/', methods = ['GET'])
def index():
    return render_template('index.html')
   

    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port = 5000)
    # socketio = SocketIO(app)
    # socketio.run(app,
    #     host=app._conf.api.host,
    #     port=app._conf.api.port,