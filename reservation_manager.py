import random
from inventory_manager import InventoryManager

inventory_manager = InventoryManager()

class ReservationManager():

    def get_vrf_name(self, node_name, service_name):
        device_information = inventory_manager.get_device_information(node_name)
        host = device_information.get("host")
        vrf_name = service_name + "-" + host.replace(".", "_")
        return vrf_name
  
    def get_local_as_number(self, node_name = None):
        #device_information = inventory_manager.get_device_information(node_name)
        #bgp_id = device_information.get("bgp_id", 65001)
        return 65001

    def get_ospf_id(self):
        return random.sample(range(1000, 2000), 1)[0]

    def get_domain_id(self):
        return random.sample(range(1000, 2000), 1)[0]

    def get_policy_name(self):
        return "bgp-into-ospf"

    def get_route_target(self):
        return "65000:15"

    def get_route_distinguisher(self):
        return "65000:15"
