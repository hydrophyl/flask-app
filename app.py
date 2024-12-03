from gevent import monkey
# Patch the standard library to use gevent
monkey.patch_all()
from flask import Flask, render_template
from flask_socketio import SocketIO
from gevent.event import Event
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
socketio = SocketIO(app, async_mode='gevent')

pause_event = Event()
task_running = False

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('my_event')
def handle_my_event(json):
    print('Received event: ' + str(json))
    socketio.emit('my_response', {'data': 'Event received!'})

def long_task():
    global task_running
    task_running = True
    for i in range(100):
        pause_event.wait()  # Wait if the task is paused
        socketio.sleep(0.1)
        socketio.emit('my_response', {'data': f'Task running: {i*10} seconds'})
    print('Task completed!')
    socketio.emit('my_response', {'data': 'Task completed!'})
    task_running = False

@socketio.on('start_long_task')
def start_long_task():
    global pause_event, task_running
    if task_running:
        socketio.emit('my_response', {'data': 'Task already running!'})
        print('Task already running')
        return
    pause_event.set()  # Ensure the task is not paused
    socketio.start_background_task(target=long_task)
    print('Task started')

@socketio.on('pause_task')
def pause_task():
    global pause_event
    pause_event.clear()  # Pause the task
    print('Task paused')

@socketio.on('resume_task')
def resume_task():
    global pause_event
    pause_event.set()  # Resume the task
    print('Task resumed')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)