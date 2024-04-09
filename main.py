
import os
from flask import Flask
from flask import request
import time
from logging.config import dictConfig
import logging as logger
import json
import logging as logger
from pathlib import Path

from queue import Queue
from flask_socketio import SocketIO, emit
from threading import Lock

from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
import logging as logger

import time

import random
from datetime import datetime



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


# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = "threading"

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode, cors_allowed_origins="*")


thread = None
thread_lock = Lock()
queue = Queue(maxsize=0)
data = []

lng = 48.12800085254037
lat = 11.57960005323633
start = time.time()

def create_dummy_data_d():
    alt_d = random.gauss(-0.5, 0.1)
    return {
    "temp": random.gauss(10, 0.5),
     "pressure": "{:4.2f}".format(random.gauss(900, 50.0)),
     "depth": "{:4.2f}".format(alt_d),
     "altitude": "{:4.2f}".format(523 + alt_d),
     "gps": "{:.15f}, {:.15f}".format(lat + 2*random.uniform(1e-4, 1e-7), lng + 2*random.uniform(1e-4, 1e-7)),
     "v1": "{:.2f}".format(random.gauss(4, 0.5)),
     "v2": "{:.2f}".format(random.gauss(4, 0.7)),
     "online_time": time.time() -start,
     "ts" : int(time.time())
     }

broadcast = True

def make_save_name():
    return datetime.now().strftime("%H_%M_%S_%d_%m_%Y") + '.json'


def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    logger.info("bg started")
    while broadcast:
        # count += 1
        # d = create_dummy_data_d()
        # data.append(d)
        # socketio.emit('sensor-data',d)
        # socketio.sleep(1)
        while queue.qsize() > 0:  
            d =  queue.get()
            data.append(d)
            socketio.emit('sensor-data',d)
            socketio.sleep(0.1)
            

@app.before_request
def before_req():
    # logger.debug(request.headers)
    if "X-Real-Ip" in request.headers:
        logger.info(request.headers["X-Real-Ip"])
    try:
        logger.debug(json.loads(request.data))
    except:
        pass


@socketio.on('persist')
def save_current():
    global data
    filename = make_save_name()
    path = os.path.join("data/", filename)
    with open(path, 'w') as f:
        json.dump(data, f)
        data = []
        socketio.emit('persisted', {'new_session': filename.removesuffix('.json') })



@app.route('/time')
def get_current_time():
    return {'time': time.time()}

@app.route('/api/sensor-sessions')
def get_sessions():
    session_names = [] 

    for filename in os.listdir("data/"):
       if filename.endswith(".json"):
            session_names.append(filename.removesuffix('.json'))
    logger.info(session_names)
    return {'sessions' : session_names}

@socketio.event
def connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)
    emit('connect-ok', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect')
def disconnect():
    print('Client disconnected', request.sid)


# @app.route('/api/request-sensor-session', methods = ['POST'])
@socketio.on('request-sensor-session')
def req_session(data):
        global broadcast 
        # broadcast = False
        pl = json.loads(data)
        logger.info(pl)
        with open(os.path.join('data/', pl['session_name'] + '.json')) as f:
            data = json.load(f)
            logger.info(data)
            for d in data:
                socketio.emit('send-session', d)


@app.route('/api/post-sensor-data', methods = ['GET', 'POST'])
def user():
    if request.method == 'GET':
        return {'time': time.time()}
    if request.method == 'POST':                
        queue.put(request.json)
        logger.info("queue size: {}".format(queue.qsize()))

   

    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port = 5000)