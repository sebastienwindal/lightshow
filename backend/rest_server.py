from flask import Flask, abort, request, jsonify, make_response
from flask.json import JSONEncoder
import json
import string
import random
import led_control


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
                'status': status
            }
        return super(MyJSONEncoder, self).default(obj)

server = Flask("Light Show")
server.json_encoder = MyJSONEncoder

#callbacks methods and events
def status_off_requested():
    print("rest_status_off_requested")
def status_manual_requested():
    print("rest_status_manual_requested")
def frequency_requested(freq):
    print("frequency_requested")
def light_show_start_requested(show_id):
    print("light_show_start_requested")
    
#######################################################################
# light shows CRUD endpoint

@server.route("/light_shows", methods=['GET','POST'])
def light_shows():
    if request.method == 'GET':
        return get_light_shows()
    if request.method == 'POST':
        name = request.args.get('name')
        description = request.args.get('description')
        led_masks_str = request.args.get('led_masks_list')
        return create_light_show(name, description, led_masks_str)
        
def get_light_shows():
    shows = led_control.get_light_shows()
    sorted_shows = sorted(shows, key=lambda show: show.id)
    json_list = jsonify(sorted_shows)
    return json_list

@server.route("/light_shows/<light_show_id>", methods=['GET','DELETE'])
def light_show(light_show_id):
    if request.method == 'GET':
        return get_light_show(light_show_id)

    if request.method == 'DELETE':
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

@server.route("/system", methods=['PUT'])
def put():
    state = request.args.get('state')

    dict = {}
    
    if state == "off":
        status_off_requested()
        dict["status"] = "off"

    if state == "manual":
        status_manual_requested()
        dict["state"] = "manual"
        
    try:
        frequency = float(request.args.get('frequency'))
        frequency_requested(frequency)
        dict["frequency"] = frequency
    except (TypeError,ValueError) as e:
        pass

    try:
        light_show_id = int(request.args.get('light_show_id'))
        light_show_start_requested(light_show_id)
        dict["light_show_id"] = light_show_id
    except (TypeError, ValueError) as e:
        pass
    
    return jsonify(dict)

############################################
# led endpoints

@server.route("/leds", methods=['GET'])
def led_index():
    leds = led_control.get_leds()
    return jsonify(leds)

@server.route("/leds/<led_id>", methods=['GET'])
def led_get(led_id):
    id = int(led_id)
    led = led_control.get_led(id)
    if led == None:
        abort(make_response("error - LED not found", 404))
    return jsonify(led)

@server.route("/leds/<led_id>", methods = ['PUT'])
def update_led(led_id):
    state = request.args.get('state')
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

@server.route("/led_mask", methods=['GET'])
def get_led_mask():
    mask = led_control.get_led_mask()
    return jsonify({ 'led_mask': mask })

@server.route("/led_mask/<mask>", methods=['PUT'])
def set_led_mask(mask):
    m = int(mask)
    maskres = led_control.set_led_mask(m)
    return jsonify({ 'led_mask': maskres })
