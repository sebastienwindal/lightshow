from flask import Flask, abort, request, jsonify
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

    
@server.route("/light_shows", methods=['GET'])
def index():
    shows = led_control.get_light_shows()
    sorted_shows = sorted(shows, key=lambda show: show.id)
    json_list = jsonify(sorted_shows)
    return json_list


@server.route("/mode/<mode_id>", methods=['PUT'])
def put(mode_id):
    if mode_id == "off":
        status_off_requested()
        return json.dumps("{ 'status': 'off'}")

    if mode_id == "manual":
        status_manual_requested()
        return json.dumps("{ 'status': 'manual'}")

    abort(400) #bad request

    
@server.route("/light_shows/<light_show_id>", methods=['GET'])
def get(light_show_id):
    light_show = led_control.get_light_show(int(light_show_id))
    if light_show == None:
        abort(404)
        return
    return jsonify(light_show)


@server.route("/leds", methods=['GET'])
def led_index():
    leds = led_control.get_leds()
    return jsonify(leds)

@server.route("/leds/<led_id>", methods=['GET', 'DELETE', 'POST'])
def led(led_id):
    if request.method == 'GET':
        return led_get(led_id)
    if request.method == 'DELETE':
        return led_off(led_id)
    if request.method == 'POST':
        return led_on(led_id)
    
def led_get(led):
    id = int(led_id)
    led = led_control.get_led(id)
    if led == None:
        abort(404)
    return jsonify(led)

def led_off(led_id):
    id = int(led_id)
    led = led_control.turn_led_off(id)
    if led == None:
        abort(404)
    return jsonify(led)

def led_on(led_id):
    id = int(led_id)
    led = led_control.turn_led_on(id)
    if led == None:
        abort(404)
    return jsonify(led)

@server.route("/led_mask", methods=['GET'])
def get_led_mask():
    mask = led_control.get_led_mask()
    return jsonify({ 'led_mask': mask })

@server.route("/led_mask/<mask>", methods=['PUT'])
def set_led_mask(mask):
    m = int(mask)
    maskres = led_control.set_led_mask(m)
    return jsonify({ 'led_mask': maskres })

