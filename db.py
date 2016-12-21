import utils
import os.path
import json



DB_HOME = "./db"
OBJECT_TYPE = "services"

FILE_NAME = DB_HOME + "/" + OBJECT_TYPE + "/" + "services" + ".json"

def init():
    if not os.path.isfile(FILE_NAME):
        data = {}
        utils.write_to_file(json.dumps(data), FILE_NAME)

def create(service_data):
    service_name = service_data.get("name")
    if does_service_exist(service_name):
        print "Service %s already exists" %(service_name)
        return False

    services = json.loads(utils.read_file(FILE_NAME))
    services[service_name] = service_data
    utils.write_to_file(json.dumps(services), FILE_NAME)
    return True


def does_service_exist(service_name):
    init()
    services = json.loads(utils.read_file(FILE_NAME))
    if service_name in services.keys():
        return True
    return False

 
def delete(service_name):
    if does_service_exist(service_name):
        services = json.loads(utils.read_file(FILE_NAME))
        del services[service_name]
        utils.write_to_file(json.dumps(services), FILE_NAME)

def get(service_name):
    services = json.loads(utils.read_file(FILE_NAME))
    return services.get(service_name)


def update(service_data):
    service_name = service_data.get("name")
    if not does_service_exist(service_name):
        print "Service %s does not exist" %(service_name)
        return False

    services = json.loads(utils.read_file(FILE_NAME))
    services[service_name] = service_data
    utils.write_to_file(json.dumps(services), FILE_NAME)
    return True


def get_all():
    return json.loads(utils.read_file(FILE_NAME))
