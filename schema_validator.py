import utils
import jsonschema
import json


def validate_input(service_type, request_data):
    schema = None
    schema_file = None
    if service_type.lower() == "l3vpn":
         schema_file = "./schema/L3VPN-SCHEMA.json"
    elif service_type.lower() == "tunnel":
         schema_file = "./schema/MPLS-TE-TUNNEL-SCHEMA.json"
    schema = json.loads(utils.read_file(schema_file))
 
    try:
        validator = jsonschema.Draft4Validator(schema, format_checker=jsonschema.FormatChecker())
        validator.validate(request_data)
        print "JSON data is conforming to the schema in %s file" %schema_file
        return True, None
    except jsonschema.ValidationError as e:
        print "JSON data does not conform to the schema in %s file" %schema_file
        print (e.message)
        return False, e.message
