from flask import Flask
from flask import request
import time
from logging.config import dictConfig
import logging as logger
import json
import logging as logger

from queue import Queue
from flask_socketio import SocketIO, emit
from threading import Lock

from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
import logging as logger

import time

import random




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

lng = 48.12800085254037
lat = 11.57960005323633

def create_dummy_data_d():
    alt_d = random.gauss(-0.5, 0.1)
    return {
    "temp": random.gauss(10, 0.5),
     "pressure": "{:4.2f}".format(random.gauss(900, 50.0)),
     "depth": "{:4.2f}".format(alt_d),
     "alt": "{:4.2f}".format(523 + alt_d),
     "gps": "{:.15f}, {:.15f}".format(lat + 2*random.uniform(1e-4, 1e-7), lng + 2*random.uniform(1e-4, 1e-7)),
     "v1": "{:.2f}".format(random.gauss(4, 0.5)),
     "v2": "{:.2f}".format(random.gauss(4, 0.7)),
     "ts" : int(time.time())
     }

def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    logger.info("bg started")
    while True:
        # count += 1
        # socketio.emit('sensor-data',
        #               create_dummy_data_d())
        # socketio.sleep(1)
        while queue.qsize() > 0:  
            logger.info(queue.qsize())
            socketio.emit('sensor-data',
                    queue.get())
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

@app.route('/time')
def get_current_time():
    return {'time': time.time()}

# @socketio.event
# def join(message):
#     join_room(message['room'])
#     session['receive_count'] = session.get('receive_count', 0) + 1
#     emit('my_response',
#          {'data': 'In rooms: ' + ', '.join(rooms()),
#           'count': session['receive_count']})

# @socketio.event
# def join(message):
#     join_room(message['room'])
#     session['receive_count'] = session.get('receive_count', 0) + 1
#     emit('my_response',
#          {'data': 'In rooms: ' + ', '.join(rooms()),
#           'count': session['receive_count']})

# @socketio.event
# def my_room_event(message):
#     session['receive_count'] = session.get('receive_count', 0) + 1
#     emit('my_response',
#          {'data': message['data'], 'count': session['receive_count']},
#          to=message['room'])
    


@socketio.event
def my_ping():
    emit('my_pong')


@socketio.event
def connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)
    emit('connect-ok', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected', request.sid)


@app.route('/api/post-sensor-data', methods = ['GET', 'POST'])
def user():
    if request.method == 'GET':
        return {'time': time.time()}
    if request.method == 'POST':                
        queue.put(request.json)
        logger.info("queue size: {}".format(queue.qsize()))
        return {"success" : "true"}

   

    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port = 5000)