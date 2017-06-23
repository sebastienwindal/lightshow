from flask import Flask, abort, request, jsonify, make_response
from flask.json import JSONEncoder
import json
import string
import random
import led_control
import socketio
import eventlet


class MyJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, led_control.LightShow):
            return {
                'id': obj.id,
                'name': obj.name,
                'description': obj.description
            }
        if isinstance(obj, led_control.Led):
            status = "off"
            if obj.on:
                status = "on"
            return {
                'id': obj.id,
                'status': status,
                'color': obj.color
            }
        if isinstance(obj, led_control.System):
            return {
                'current_light_show_id': obj.current_light_show_id,
                'frequency': obj.frequency,
                'status': obj.status_str()
            }
        return super(MyJSONEncoder, self).default(obj)

sio = socketio.Server()    
app = Flask("LightShow")
app.json_encoder = MyJSONEncoder

def start_web_server():
    global app
    #    rest_server.server.run(host="0.0.0.0")

    # deploy as an eventlet WSGI server
    app = socketio.Middleware(sio, app)
    eventlet.wsgi.server(eventlet.listen(('', 5000)), app)

def abort_if_not_ready():
    system = led_control.get_system()
    if not system.is_ready():
        abort(make_response("System is initializing. try again in a couple seconds.", 503))
    
#######################################################################
# light shows CRUD endpoint

@app.route("/light_shows", methods=['GET','POST'])
def light_shows():
    if request.method == 'GET':
        return get_light_shows()
    if request.method == 'POST':
        abort_if_not_ready()
        name = request.args.get('name')
        description = request.args.get('description')
        led_masks_str = request.args.get('led_masks_list')
        return create_light_show(name, description, led_masks_str)
        
def get_light_shows():
    abort_if_not_ready()
              
    shows = led_control.get_light_shows()
    sorted_shows = sorted(shows, key=lambda show: show.id)
    json_list = jsonify(sorted_shows)
    return json_list

@app.route("/light_shows/<light_show_id>", methods=['GET','DELETE'])
def light_show(light_show_id):
    if request.method == 'GET':
        return get_light_show(light_show_id)

    if request.method == 'DELETE':
        abort_if_not_ready()
        delete_light_show(light_show_id)
        return
    
def get_light_show(light_show_id):
    light_show = led_control.get_light_show(int(light_show_id))
    if light_show == None:
        abort(make_response("error - light show not found", 404))
        return
    return jsonify(light_show)

def delete_light_show(light_show_id):
    light_show = led_control.get_light_show(int(light_show_id))
    if light_show == None:
        abort(make_response("error - light show not found", 404))
        return
    if light_show.read_only:
        abort(make_response("light show is read only", 400))
        return
    led_control.delete_light_show(light_show)

def create_light_show(name, description, led_masks_str):   
    if led_masks_str == None:
        led_masks_str = ""
    if name == None:
        name = ""
        
    led_masks_list = []
    for e in led_masks_str.split(','):
        if e.isdigit():
            led_masks_list.append(int(e))
        
    if len(led_masks_list) == 0:
        abort(make_response("error - missing led_masks_list", 400))
    if len(name) == 0:
        abort(make_response("error - missing name", 400))
            
    light_show = led_control.create_light_show(name, description, led_masks_list)
    return jsonify(light_show)


#################################################
# system control endpoints

@app.route("/system", methods=['PUT', 'GET'])
def system():
    if request.method == 'GET':
        return system_get()
    if request.method == 'PUT':
        return system_put()
    
def system_get():
    return jsonify(led_control.get_system())
    
def system_put():
    abort_if_not_ready()
    system = led_control.get_system()

    json = request.get_json()
    
    status = json['status']
    system.set_status_str(status)
    
    try:
        frequency = float(json['frequency'])
        system.frequency = frequency
    except (TypeError,ValueError) as e:
        pass

    try:
        current_light_show_id = int(json['current_light_show_id'])
        system.current_light_show_id = current_light_show_id
    except (TypeError, ValueError) as e:
        pass

    led_control.set_system(system)
    
    return jsonify(system)

############################################
# led endpoints

@app.route("/leds", methods=['GET'])
def led_index():
    leds = led_control.get_leds()
    return jsonify(leds)

@app.route("/leds/<led_id>", methods=['GET'])
def led_get(led_id):
    abort_if_not_ready()
    
    id = int(led_id)
    led = led_control.get_led(id)
    if led == None:
        abort(make_response("error - LED not found", 404))
    return jsonify(led)

@app.route("/leds/<led_id>", methods = ['PUT'])
def update_led(led_id):
    abort_if_not_ready()

    json = request.get_json()
    state = json['status']

    if state == "on":
        return led_on(led_id)
    if state == "off":
        return led_off(led_id)
    abort(make_response("error - state must be 'on' or 'off'", 400))

def led_off(led_id):
    id = int(led_id)
    led = led_control.turn_led_off(id)
    if led == None:
        abort(make_response("error - LED not found", 404))
    return jsonify(led)

def led_on(led_id):
    id = int(led_id)
    led = led_control.turn_led_on(id)
    if led == None:
        abort(make_response("error - LED not found", 404))
    return jsonify(led)

###################################################
# led mask

@app.route("/led_mask", methods=['GET'])
def get_led_mask():
    mask = led_control.get_led_mask()
    return jsonify({ 'led_mask': mask })

@app.route("/led_mask/<mask>", methods=['PUT'])
def set_led_mask(mask):
    abort_if_not_ready()
    
    m = int(mask)
    maskres = led_control.set_led_mask(m)
    return jsonify({ 'led_mask': maskres })



###############################################3############
# web sockets

@sio.on('connect')
def connect(sid, environ):
    print('connect ', sid)

@sio.on('my message')
def message(sid, data):
    print('message ', data)

@sio.on('disconnect')
def disconnect(sid):
    print('disconnect ', sid)

def test_emit():
    sio.emit('led_changed')
