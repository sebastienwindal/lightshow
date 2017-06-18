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
        return super(MyJSONEncoder, self).default(obj)

server = Flask("Light Show")
server.json_encoder = MyJSONEncoder

#callbacks methods
def rest_status_off_requested():
    print "rest_status_off_requested"
def rest_status_manual_requested():
    print "rest_status_manual_requested"



@server.route("/light_shows", methods=['GET'])
def index():
    shows = led_control.get_light_shows()
    sorted_shows = sorted(shows, key=lambda show: show.id)
    json_list = jsonify(sorted_shows)
    return json_list

@server.route("/mode/<mode_id>", methods=['PUT'])
def put(mode_id):
    if mode_id == "off":
        rest_status_off_requested()
        return json.dumps("{ 'status': 'off'}")

    if mode_id == "manual":
        rest_status_manual_requested()
        return json.dumps("{ 'status': 'manual'}")

    abort(400) #bad request

@server.route("/light_shows/<light_show_id>", methods=['GET'])
def get(light_show_id):
    light_show = led_control.get_light_show(int(light_show_id))
    if light_show == None:
        abort(404)
        return

    return jsonify(light_show)

