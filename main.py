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
from threading import Lock
from flask import Flask, render_template, session, request, \
    copy_current_request_context
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
import logging as logger

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
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()
queue = Queue(maxsize=0)
import time

def create_dummy_data():
    return {"temp": "{:4.2f}".format(random.uniform(0.0, 30.0)),
     "pressure": "{:4.2f}".format(random.uniform(100.0, 3000.0)),
     "depth": "{:4.2f}".format(random.uniform(0.0, 3.0)),
     "environment_dist": "{:4.2f}".format(random.uniform(0.0, 3.0)),
     "gps": "{:10.8f}, {:10.8f}".format(random.uniform(0.0, 90), random.uniform(0.0, 90)),
     "ts" : time.time()
     }

def create_dummy_data_d():
    return {"temp": random.uniform(0.0, 30.0),
     "pressure": "{:4.2f}".format(random.uniform(100.0, 3000.0)),
     "depth": "{:4.2f}".format(random.uniform(0.0, 3.0)),
     "env_dist": "{:4.2f}".format(random.uniform(0.0, 3.0)),
     "gps": "{:10.8f}, {:10.8f}".format(random.uniform(0.0, 90), random.uniform(0.0, 90)),
     "ts" : time.time()
     }

def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    logger.info("bg started")
    while True:
        count += 1
        # socketio.emit('sensor-data',
        #               create_dummy_data_d())
        while queue.qsize() > 0:  
            logger.info(queue.qsize())
            socketio.emit('sensor-data',
                    {**queue.get(), 'count': count})
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

@socketio.event
def my_broadcast_event(data):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('re', **data,
         broadcast=True)

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
def disconnect_request():
    @copy_current_request_context
    def can_disconnect():
        disconnect()

    session['receive_count'] = session.get('receive_count', 0) + 1
    # for this emit we use a callback function
    # when the callback function is invoked we know that the message has been
    # received and it is safe to disconnect
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']},
         callback=can_disconnect)


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
        
        data = request.json # a multidict containing POST data
        
        logger.info(request.json)
        queue.put(data)
        logger.info(queue.qsize())
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