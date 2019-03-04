from flask import Flask
from flask_restplus import Api, Resource, fields
from rq import Connection, Queue, Worker
from rq.job import Job
import rq_dashboard
import RPi.GPIO as GPIO
import time
import sys
import redis
import json
import datetime


REDIS_HOST = 'redis'
REDIS_PORT = '6379'
REDIS_CONN = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)

Q = Queue(connection=REDIS_CONN)

GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme

# define relay pins
relay_1_pin = 26
relay_2_pin = 19
relay_3_pin = 13
relay_4_pin = 6

# configure relay pins
GPIO.setup(relay_1_pin, GPIO.OUT)
GPIO.setup(relay_2_pin, GPIO.OUT)
GPIO.setup(relay_3_pin, GPIO.OUT)
GPIO.setup(relay_4_pin, GPIO.OUT)

interval = 0.05 # How long switch should be activated

app = Flask(__name__)
api = Api(app, version='1.0', title='garageController API',
    description='Monitor and control garage doors.',
)

ns = api.namespace('doors', description='Door operations')

door = api.model('Door', {
    'id': fields.String(readOnly=True, description='The door unique identifier'),
    'state': fields.String(required=True, description='The state of the door'),
    'target': fields.String(required=False, description='')
})


class doorDAO(object):
    def get_door_list(self):
        doors = []
        bytes = REDIS_CONN.get('doors')
        if bytes is not None:
            doors = json.loads(bytes)
        else:
            REDIS_CONN.set('doors',json.dumps(doors))
        return doors
    
    def get_all(self):
        doors = self.get_door_list()
        door_data = []
        
        for door in doors:
            door_bytes = REDIS_CONN.get(door)
            if door_bytes is not None:
                door_data.append(json.loads(door_bytes))
            
        return door_data
        api.abort(404, "Could not find any doors.".format(id))
        
    def get(self, id):
        bytes = REDIS_CONN.get(id)
        if bytes is not None:
            door = json.loads(bytes)

            return door
        api.abort(404, "Door {} doesn't exist.".format(id))

    def create(self, id, data):
        door_list = self.get_door_list()
        if id in door_list:
            print('Door {} already exists.  Doing nothing.'.format(id))
        else:
            door_list.append(id)
            REDIS_CONN.set('doors',json.dumps(door_list))
            
            if 'id' not in data:
                data['id'] = id
            
            assert REDIS_CONN.set(id,json.dumps(data)) == True
        
        return id

    def update(self, id, data):
        bytes = REDIS_CONN.get(id)
        if bytes is not None:
            door = json.loads(bytes)
            
        for key in data:
            door[key] = data[key]

        if (door['state'] == 'open' and door['target'] == 'closed') or (door['state'] == 'closed' and door['target'] == 'open'):
            door['triggered'] = True
            assert REDIS_CONN.set(id,json.dumps(door)) == True
            job = Q.enqueue_call(func=change_door_state, args=(id,), result_ttl=30000, timeout=30000)
        else:
            assert REDIS_CONN.set(id,json.dumps(door)) == True

        return door

    def delete(self, id):
        door_list = self.get_door_list()
        door_list.remove(id)
        assert REDIS_CONN.set('doors',json.dumps(door_list)) == True
        assert REDIS_CONN.delete(id) == True
        
        
DAO = doorDAO()
DAO.create('door_1',{'state': 'unknown', 'sensor_pin_open':2, 'sensor_pin_close':3})
DAO.create('door_2',{'state': 'unknown', 'sensor_pin_open':4, 'sensor_pin_close':14})
DAO.create('door_3',{'state': 'unknown', 'sensor_pin_open':15, 'sensor_pin_close':16})


def change_door_state(id):
    door = DAO.get(id)
    assert door['triggered'] == True
    
    if door['id'] == 'door_1':
        pin = relay_1_pin
    elif door['id'] == 'door_2':
        pin = relay_2_pin
    elif door['id'] == 'door_3':
        pin = relay_3_pin
        
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(0.25)
    GPIO.output(pin, GPIO.LOW)
    
    # time.sleep(10)
    
    # add a loop here to read actual state sensors.
    # door['state'] = door['target']
    
    
def monitor_sensors():
    next_door_refresh = datetime.datetime.now()
    next_sensor_refresh = datetime.datetime.now()
    door_info = []
    while True:
        # update door info every 10 seconds
        if datetime.datetime.now() >= next_door_refresh:
            door_info = DAO.get_all()
            next_door_refresh = datetime.datetime.now() + datetime.timedelta(seconds=10)
            
        if datetime.datetime.now() >= next_sensor_refresh:
            for door in door_info:
                isOpen = GPIO.input(item['sensor_pin_open'])
                isClosed = GPIO.input(item['sensor_pin_close'])
                
                if not isOpen and not isClosed:
                    measured_state = 'unknown'
                elif isOpen:
                    measured_state = 'open'
                elif isClosed:
                    measured_state = 'closed'
                    
                if door['state'] == measured_date:
                    # do nothing
                    pass
                else:
                    bytes = REDIS_CONN.get(id)
                    if bytes is not None:
                        door_object = json.loads(bytes)
                        
                        door_object['state'] = measured_state
                        print('{} has changed state to {}!!!!'.format(door['id'],measured_state))
                        assert REDIS_CONN.set(door['id'],json.dumps(door_object)) == True
                        
            next_sensor_refresh = datetime.datetime.now() + datetime.timedelta(seconds=1)
    
    

@ns.route('/')
class DoorList(Resource):
    '''Shows a list of all doors, and lets you POST to add new doors'''
    @ns.doc('list_doors')
    @ns.marshal_list_with(door)
    def get(self):
        '''List all doors'''
        return DAO.get_all()


@ns.route('/<id>')
@ns.response(404, 'Door not found')
@ns.param('id', 'The door identifier')
class Door(Resource):
    '''Show a single todo item and lets you delete them'''
    @ns.doc('get_door')
    @ns.marshal_with(door)
    def get(self, id):
        '''Fetch a given resource'''
        return DAO.get(id)

    @ns.expect(door)
    @ns.marshal_with(door)
    def put(self, id):
        '''Update a task given its identifier'''
        return DAO.update(id, api.payload)
    

# @api.route("/")
# def hello():
#     print('received command!!')
    
#     GPIO.output(relay_1_pin, GPIO.HIGH) #turn relay 1 on
#     time.sleep(interval)
#     GPIO.output(relay_1_pin, GPIO.LOW) #turn relay 1 off
#     time.sleep(interval)

#     GPIO.output(relay_2_pin, GPIO.HIGH) #turn relay 1 on
#     time.sleep(interval)
#     GPIO.output(relay_2_pin, GPIO.LOW) #turn relay 1 off
#     time.sleep(interval)

#     #Not Used For Pi Zero
#     GPIO.output(relay_3_pin, GPIO.HIGH) #turn relay 1 on
#     time.sleep(interval)
#     GPIO.output(relay_3_pin, GPIO.LOW) #turn relay 1 off
#     time.sleep(interval)

#     GPIO.output(relay_4_pin, GPIO.HIGH) #turn relay 1 on
#     time.sleep(interval)
#     GPIO.output(relay_4_pin, GPIO.LOW) #turn relay 1 off
#     time.sleep(interval)
    
#     return "Hello World!"

if __name__ == "__main__":
    if sys.argv[-1] == "worker":
        with Connection(connection=REDIS_CONN):
            Worker(Q).work()