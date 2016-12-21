import os
import uuid
import mimetypes
import uuid
import json
import utils
from time import gmtime, strftime
import getpass
import reservation_manager

import falcon
import backend
import db
import schema_validator


def validate_service_state_for_operation(target_service_state, current_service_state, allowed_target_service_states):
    is_ok = True
    http_status = None
    http_response_body = None

    if target_service_state not in allowed_target_service_states:
        is_ok = False
        message = "Invalid target service state %s specified in the request"
        tokens = [ target_service_state ]
        code = "DSM-LITE-400"
        http_status = falcon.HTTP_400
        http_response_body = error_response(code = code, message = message, tokens = tokens)
    return (is_ok, http_status, http_response_body)


def check_schema_conformance(service_data):
    service_type = service_data.get("serviceType")
    request_data = service_data.get("requestData")
    is_valid = True
    http_status = None
    http_response_body = None
    is_valid, error_message = schema_validator.validate_input(service_type, service_data.get("requestData"))
    if not is_valid:
        message = "Request data does not conform to the service definition schema. %s"
        tokens = [ error_message ]
        code = "DSM-LITE-400"
        http_status = falcon.HTTP_400
        http_response_body = error_response(code = code, message = message, tokens = tokens)
    return (is_valid, http_status, http_response_body)

def generate_system_attributes(service_name):
    system_attributes = {}
    res_mgr = reservation_manager.ReservationManager()
    system_attributes["vrf_name"] = service_name
    system_attributes["route_target"] = res_mgr.get_route_target()
    system_attributes["route_distinguisher"] = res_mgr.get_route_distinguisher()
    system_attributes["ospf_id"] = str(res_mgr.get_ospf_id())
    system_attributes["domain_id"] = str(res_mgr.get_domain_id())
    system_attributes["policy_name"] = res_mgr.get_policy_name()
    system_attributes["local_as_number"] = str(res_mgr.get_local_as_number())

    return system_attributes
    


    
class Services():

    def on_post(self, req, resp):
        service_data = None
        if req.content_length:
            request_body = json.load(req.stream)

        service_data = request_body.get("service")
        service_name = service_data.get("name")
        service_type = service_data.get("serviceType")
        service_state = "Draft"
        does_service_exist = db.does_service_exist(service_name)
        if does_service_exist:
            message = "Service %s already exists"
            tokens = [ service_name ]
            code = "DSM-LITE-409"
            resp.status = falcon.HTTP_409
            resp.body = error_response(code = code, message = message, tokens = tokens)
            return

        target_service_state = service_data.get("targetState", "Draft")
        allowed_target_service_states = ["Draft", "Reserved", "Active"]
        is_ok, http_status, http_response_body = validate_service_state_for_operation(target_service_state, None, allowed_target_service_states)
        if not is_ok:
            resp.status = http_status
            resp.body = http_response_body
            return

        if target_service_state in ["Reserved", "Active"]:
            is_valid, http_status, http_response_body = check_schema_conformance(service_data)
            if not is_valid:
                resp.status = http_status
                resp.body = http_response_body
                return

            service_attributes = generate_system_attributes(service_name)
            service_data["service-attributes"] = service_attributes
            if target_service_state == "Active":
                result = backend.perform_operation(service_data, "activate")
                if result:
                    service_state = "Active"
                else:
                    service_state = "Reserved"
            else:
                service_state = "Reserved"

        del service_data["targetState"]
        service_id = str(uuid.uuid4())
        service_data["id"] = service_id
        href = "/services/%s" %service_id
        created_by = getpass.getuser()
        creation_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        service_data["href"] = href
        service_data["createdBy"] = created_by
        service_data["createdOn"] = creation_time
        service_data["serviceState"] = service_state
        db.create(service_data)

        resp.status = falcon.HTTP_201
        resp.location = href
        resp.body = success_response(service_data)


    def on_get(self, req, resp): 
       	list_of_services = []
        services = db.get_all()
        query_filter = req.params
        for k, v in services.iteritems():
            if not self.filter_data(query_filter, v):
                continue

            service_summary = {}
            service_summary["name"] = v.get("name")
            service_summary["serviceType"] = v.get("serviceType")
            service_summary["serviceState"] = v.get("serviceState")
            service_summary["id"] = v.get("id")
            service_summary["href"] = v.get("href")
            service_summary["createdBy"] = v.get("createdBy")
            service_summary["createdOn"] = v.get("createdOn")
            list_of_services.append(service_summary)

        resp.status = falcon.HTTP_200
        resp.body = success_response(list_of_services)

    def filter_data(self, query_filter, data):
        for k,v in query_filter.items():
            if data.get(k) and data.get(k) == v:
                continue
            else:
                return False
        return True

class Service():

    def on_get(self, req, resp, id): 
        does_service_exist = db.does_service_exist(id)
        if not does_service_exist:
            message = "Service %s does not exist"
            tokens = [ id ]
            code = "DSM-LITE-404"
            resp.status = falcon.HTTP_404
            resp.body = error_response(code = code, message = message, tokens = tokens)
            return

        service_data = db.get(id)
        resp.content_type = 'application/json'
        resp.body = success_response(service_data)
        resp.status = falcon.HTTP_200

    def on_put(self, req, resp, id):
        service_data = None
        if req.content_length:
            request_body = json.load(req.stream)

        service_data = request_body.get("service")
        service_name = service_data.get("name")
        service_type = service_data.get("serviceType")
        request_data = service_data.get("requestData")
        target_service_state = service_data.get("targetState", "Draft")

        does_service_exist = db.does_service_exist(service_name)
        if not does_service_exist:
            message = "Service %s does not exist"
            tokens = [ id ]
            code = "DSM-LITE-404"
            resp.status = falcon.HTTP_404
            resp.body = error_response(code = code, message = message, tokens = tokens)
            return

        allowed_target_service_states = ["Draft", "Reserved", "Active"]
        is_ok, http_status, http_response_body = validate_service_state_for_operation(target_service_state, None, allowed_target_service_states)
        if not is_ok:
            resp.status = http_status
            resp.body = http_response_body
            return

        existing_service_data = db.get(id)
        service_attributes = {}

        service_state = existing_service_data.get("serviceState")
        if service_state not in ["Draft"]:
            message = "Invalid service state %s. Only the service(s) in Draft state can be edited."
            tokens = [ service_state ]
            code = "DSM-LITE-405"
            resp.status = falcon.HTTP_405
            resp.body = error_response(code = code, message = message, tokens = tokens)
            return

        if target_service_state == "Draft": 
            service_state = "Draft"
        elif target_service_state == "Reserved": 
            is_valid, error_message = schema_validator.validate_input(service_type, request_data)
            if not is_valid:
                message = "Request data does not conform to the service definition schema. %s"
                tokens = [ error_message ]
                code = "DSM-LITE-400"
                resp.status = falcon.HTTP_400
                resp.body = error_response(code = code, message = message, tokens = tokens)
                return
            service_attributes = generate_system_attributes(id)
            service_state = "Reserved"
        elif target_service_state == "Active":
            is_valid, error_message = schema_validator.validate_input(service_type, request_data)
            if not is_valid:
                message = "Request data does not conform to the service definition schema. %s"
                tokens = [ error_message ]
                code = "DSM-LITE-400"
                resp.status = falcon.HTTP_400
                resp.body = error_response(code = code, message = message, tokens = tokens)
                return
            service_attributes = generate_system_attributes(id)
            service_data["service-attributes"] = service_attributes
            result = backend.perform_operation(service_data, "activate")
            if result:
                service_state = "Active"
            else:
                service_state = "Reserved"
        existing_service_data["requestData"] = request_data
        existing_service_data["serviceState"] = service_state
        existing_service_data["service-attributes"] = service_attributes
        db.update(existing_service_data)

        resp.status = falcon.HTTP_201
        resp.body = success_response(existing_service_data)

    
    def on_delete(self, req, resp, id): 
        does_service_exist = db.does_service_exist(id)
        if not does_service_exist:
            message = "Service %s does not exist"
            tokens = [ id ]
            code = "DSM-LITE-404"
            resp.status = falcon.HTTP_404
            resp.body = error_response(code = code, message = message, tokens = tokens)
            return

        service_data = db.get(id)
        service_state = service_data.get("serviceState")
        if service_state not in ["Draft", "Reserved"]:
            message = "Invalid service state %s. Only services in Draft or Reserved state can be deleted."
            tokens = [ service_state ]
            code = "DSM-LITE-405"
            resp.status = falcon.HTTP_405
            resp.body = error_response(code = code, message = message, tokens = tokens)
            return

        db.delete(id)
        resp.content_type = 'application/json'
        resp.body = success_response(None)
        resp.status = falcon.HTTP_200


class ServiceAction():

    def on_post(self, req, resp, id, action):

        print "Action %s" %action
        if action == "activate":
            return self.activate(req, resp, id)
        elif action == "deactivate":
            return self.deactivate(req, resp, id)
        elif action == "deactivateAndDelete":
            self.deactivate(req, resp, id)
            if resp.status == falcon.HTTP_200:
                return self.delete(req, resp, id)
            return

    def deactivate(self, req, resp, id):
        does_service_exist = db.does_service_exist(id)
        if not does_service_exist:
            message = "Service %s does not exist"
            tokens = [ id ]
            code = "DSM-LITE-404"
            resp.status = falcon.HTTP_404
            resp.body = error_response(code = code, message = message, tokens = tokens)
            return

        service_data = db.get(id)
        service_state = service_data.get("serviceState")
        if service_state != "Active":
            message = "Invalid service state: %s. Service should be in %s state to deactivate the service"
            tokens = [ service_state, "Active" ]
            code = "DSM-LITE-405"
            resp.status = falcon.HTTP_405
            resp.body = error_response(code = code, message = message, tokens = tokens)
            return
        
        result = backend.perform_operation(service_data, "deactivate")
        if result:
            service_data["serviceState"] = "Reserved"
        else:
            service_data["serviceState"] = "Active"

        db.update(service_data)

        resp.status = falcon.HTTP_200
        resp.body = success_response(service_data)

    def activate(self, req, resp, id):
        does_service_exist = db.does_service_exist(id)
        if not does_service_exist:
            message = "Service %s does not exist"
            tokens = [ id ]
            code = "DSM-LITE-404"
            resp.status = falcon.HTTP_404
            resp.body = error_response(code = code, message = message, tokens = tokens)
            return

        service_data = db.get(id)
        service_state = service_data.get("serviceState")
        if service_state != "Reserved":
            message = "Invalid service state: %s. Service should be in %s state to activate the service"
            tokens = [ service_state, "Reserved" ]
            code = "DSM-LITE-405"
            resp.status = falcon.HTTP_405
            resp.body = error_response(code = code, message = message, tokens = tokens)
            return
        
        result = backend.perform_operation(service_data, "activate")
        if result:
            service_data["serviceState"] = "Active"
        else:
            service_data["serviceState"] = "Reserved"

        db.update(service_data)

        resp.status = falcon.HTTP_200
        resp.body = success_response(service_data)

    def delete(self, req, resp, id): 
        does_service_exist = db.does_service_exist(id)
        if not does_service_exist:
            message = "Service %s does not exist"
            tokens = [ id ]
            code = "DSM-LITE-404"
            resp.status = falcon.HTTP_404
            resp.body = error_response(code = code, message = message, tokens = tokens)
            return

        service_data = db.get(id)
        service_state = service_data.get("serviceState")
        if service_state not in ["Draft", "Reserved"]:
            message = "Invalid service state %s. Only services in Draft or Reserved state can be deleted."
            tokens = [ service_state ]
            code = "DSM-LITE-405"
            resp.status = falcon.HTTP_405
            resp.body = error_response(code = code, message = message, tokens = tokens)
            return

        db.delete(id)
        resp.content_type = 'application/json'
        resp.body = success_response(None)
        resp.status = falcon.HTTP_200



def success_response(data = {}):
    response_body = {}

    status = {}
    status["reqStatus"] = "SUCCESS"

    service = {}
    service["service"] = data

    response_body["status"] = status
    response_body["data"] = service
    return json.dumps(response_body)

    
def error_response(code = "DSM-LITE-500", message = "Internal Server Error", tokens = []):
    response_body = {}
    
    messages = []
    msg = {}
    msg["msgCode"] =  code
    msg["msgText"] =  message
    msg["msgValues"] = tokens

    messages.append(msg)

    status = {}
    status["reqStatus"] = "ERROR"
    status["messages"] = messages

    response_body["status"] = status
    return json.dumps(response_body)

