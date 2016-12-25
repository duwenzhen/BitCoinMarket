#!/usr/bin/env python
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect

import sys
import os
import time
import thread
import quickfix as fix
import quickfix44 as fix44
from datetime import datetime
import FixClientApplication

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
fixClientApplication = FixClientApplication.FixClientApplication(socketio)


def background_thread(file):
    settings = fix.SessionSettings(file)
    storeFactory = fix.FileStoreFactory(settings)
    logFactory = fix.FileLogFactory(settings)
    initiator = fix.SocketInitiator(fixClientApplication, storeFactory, settings, logFactory)

    initiator.start()
    fixClientApplication.run()
    """Example of how to send server generated events to clients."""


    initiator.stop()

@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)


@socketio.on('my_buy', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('myEvent',
         {'data': 'You buy ' + message['data'], 'count': session['receive_count']})

@socketio.on('my_sell', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('myEvent',
         {'data': 'You sell ' + message['data'], 'count': session['receive_count']})


@socketio.on('my broadcast event', namespace='/test')
def test_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('myLog',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)


@socketio.on('subscribe', namespace='/test')
def join(message):
    join_room(message['ric'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('myEvent',
         {'data':message['ric'] + 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})
    if (fixClientApplication is None):
        print "exit"
        exit()
    else:
        print "not exit"
    fixClientApplication.marketDataRequest(message['ric'])


@socketio.on('unsubscribe', namespace='/test')
def leave(message):
    leave_room(message['ric'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('myEvent',
         {'data': message['ric'] + 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('close room', namespace='/test')
def close(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('myLog', {'data': 'Room ' + message['room'] + ' is closing.',
                         'count': session['receive_count']},
         room=message['room'])
    close_room(message['room'])


@socketio.on('my room event', namespace='/test')
def send_room_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('level',
         {'data': message['data'], 'count': session['receive_count']},
         room=message['room'])


@socketio.on('disconnect request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('myLog',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()


@socketio.on('my ping', namespace='/test')
def ping_pong():
    emit('my pong')


@socketio.on('connect', namespace='/test')
def test_connect():
    print sys.path
    if (len(sys.argv) < 2):
        print "usage: ", sys.argv[0] + " FILE."

    file = sys.argv[1]
    global thread
    if thread is None:
        thread = socketio.start_background_task(background_thread, file)
    emit('myLog', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)


if __name__ == '__main__':
    socketio.run(app, debug=True)
