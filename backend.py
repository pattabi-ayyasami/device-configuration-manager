import ConfigParser

import cli_client
import iosxe_cli_client
from inventory_manager import InventoryManager
from reservation_manager import ReservationManager
import netconf_client
import template_manager
import sys
import json
import utils

import falcon
import service


inventory_manager = InventoryManager()
reservation_manager = ReservationManager()

def perform_operation(service_data, action):
    service_type = service_data.get("serviceType")
    service_name = service_data.get("name")
  
    successfully_configured_nodes = []
    failed_to_configure_nodes = []
    rollback_action = None 
    system_attributes = {}

    is_success = True
    if service_type == "l3vpn":
        system_attributes = service_data.get("service-attributes")
        sites = service_data.get("requestData").get("l3vpn-svc").get("sites").get("site")

        #system_attributes["policy_name"] = reservation_manager.get_policy_name()
        #system_attributes["ospf_id"] = str(reservation_manager.get_ospf_id())
        #system_attributes["domain_id"] = str(reservation_manager.get_domain_id())
        #system_attributes["route_target"] = reservation_manager.get_route_target()
        #system_attributes["route_distinguisher"] = reservation_manager.get_route_distinguisher()


        for site in sites:
            router_name = site.get("site-network-accesses").get("site-network-access").get("provider-edge").get("router-name")
            device_info = inventory_manager.get_device_information(router_name)
            node_type = device_info.get("type")

            print "Router name (%s), Type (%s)" %(router_name, node_type)
            #system_attributes["vrf_name"] = reservation_manager.get_vrf_name(router_name, service_name)
            #system_attributes["local_as_number"] = str(reservation_manager.get_local_as_number(router_name))

            
            input_data = {}
            input_data["service-attributes"] = system_attributes
            input_data["site"] = site

            request_file = template_manager.generate_request_data(node_type, service_type, action, input_data)
            if node_type.lower() == "junos":
                command_data = utils.read_file(request_file)
                print "=========================================================="
                print command_data
                print "=========================================================="
                is_success = netconf_client.edit_config(device_info, command_data)
            elif node_type.lower() == "iosxr":
                command_data = utils.read_file_as_lines(request_file)
                print "=========================================================="
                print command_data
                print "=========================================================="
                is_success = cli_client.edit_config(device_info, command_data)
            elif node_type.lower() == "iosxe":
                command_data = utils.read_file_as_lines(request_file)
                print "=========================================================="
                print command_data
                print "=========================================================="
                is_success = iosxe_cli_client.edit_config(device_info, command_data)
                if not is_success:
                    if action == "activate":
                        rollback_action =  "deactivate"
                    else:
                        rollbacl_action = "activate"
                    request_file = template_manager.generate_request_data(node_type, service_type, rollback_action, input_data)
                    iosxe_cli_client.edit_config(device_info, command_data)
            if is_success:
                successfully_configured_nodes.append(router_name)
            else:
                failed_to_configure_nodes.append(router_name)
                break;

    elif service_type == "tunnel":
        router_name = service_data.get("requestData").get("source")
        device_info = inventory_manager.get_device_information(router_name)
        node_type = device_info.get("type")
        print "Router name (%s), Type (%s)" %(router_name, node_type)
        input_data = service_data.get("requestData")
        request_file = template_manager.generate_request_data(node_type, service_type, action, input_data)

        if node_type.lower() == "junos":
            command_data = utils.read_file(request_file)
            is_success = netconf_client.edit_config(device_info, command_data)
        elif node_type.lower() == "iosxr":
            command_data = utils.read_file_as_lines(request_file)
            print "=========================================================="
            print command_data
            print "=========================================================="
            is_success = cli_client.edit_config(device_info, command_data)
        elif node_type.lower() == "iosxe":
            print "=========================================================="
            print "Tunnel service not supported for iosxe device"
            print "=========================================================="
            return False

        if is_success:
            successfully_configured_nodes.append(router_name)
        else:
            failed_to_configure_nodes.append(router_name)

    print "=========================================================="
    print "Successfully configured nodes: %s" %successfully_configured_nodes
    print "Failed to configure nodes: %s" %failed_to_configure_nodes
    print "=========================================================="
    if not is_success:
        if action == "activate":
            rollback_action =  "deactivate"
        else:
            rollback_action = "activate"

        rollback(successfully_configured_nodes, service_data, rollback_action, system_attributes)
        return False

    return True 


def rollback(nodes, service_data, rollback_action, system_attributes):
    print "Rollback for the nodes: %s" %nodes
    service_type = service_data.get("serviceType")
    service_name = service_data.get("name")

    if service_type == "l3vpn":
        sites = service_data.get("requestData").get("l3vpn-svc").get("sites").get("site")

        for site in sites:
            router_name = site.get("site-network-accesses").get("site-network-access").get("provider-edge").get("router-name")
            if router_name not in nodes:
                continue

            device_info = inventory_manager.get_device_information(router_name)
            node_type = device_info.get("type")
            print "Router name (%s), Type (%s)" %(router_name, node_type)
            #system_attributes["vrf_name"] = reservation_manager.get_vrf_name(router_name, service_name)
            #system_attributes["local_as_number"] = str(reservation_manager.get_local_as_number(router_name))

                
            input_data = {}
            input_data["service-attributes"] = system_attributes
            input_data["site"] = site

            request_file = template_manager.generate_request_data(node_type, service_type, rollback_action, input_data)
            if node_type.lower() == "junos":
                command_data = utils.read_file(request_file)
                print "=========================================================="
                print command_data
                print "=========================================================="
                netconf_client.edit_config(device_info, command_data)
            elif node_type.lower() == "iosxr":
                command_data = utils.read_file_as_lines(request_file)
                print "=========================================================="
                print command_data
                print "=========================================================="
                cli_client.edit_config(device_info, command_data)
            elif node_type.lower() == "iosxe":
                command_data = utils.read_file_as_lines(request_file)
                print "=========================================================="
                print command_data
                print "=========================================================="
                iosxe_cli_client.edit_config(device_info, command_data)
    elif service_type == "tunnel":
        router_name = service_data.get("requestData").get("source")
        device_info = inventory_manager.get_device_information(router_name)
        node_type = device_info.get("type")
        print "Router name (%s), Type (%s)" %(router_name, node_type)
        request_file = template_manager.generate_request_data(node_type, service_type, rollback_action, service_data)

        if node_type.lower() == "junos":
            command_data = utils.read_file(request_file)
            netconf_client.edit_config(device_info, command_data)
        elif node_type.lower() == "iosxr":
            command_data = utils.read_file_as_lines(request_file)
            print "=========================================================="
            print command_data
            print "=========================================================="
            cli_client.edit_config(device_info, command_data)
        elif node_type.lower() == "iosxe":
            print "=========================================================="
            print "Tunnel service not supported for iosxe device"
            print "=========================================================="


