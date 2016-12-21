import json

def read_file(file_name):
    with open(file_name) as data_file:
        data = data_file.read()
        return data

class InventoryManager():

    device_information_file = "./data/network-information.json"
    devices = {}
   
    def __init__(self):
        self.devices = json.loads(read_file(self.device_information_file))

    def get_device_information(self, name):
        return self.devices.get(name)
    
