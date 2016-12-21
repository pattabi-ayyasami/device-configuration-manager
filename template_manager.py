import json
import xml.dom.minidom
import airspeed



def read_file(file_name):
    with open(file_name) as data_file:    
        data = data_file.read()
        return data
    

def write_to_file(data, file_name):
    with open(file_name, "wb") as text_file:
        text_file.write(data)
      

def replace_dash_with_underscore(d):
    new = {}
    for k,v in d.iteritems():
        if isinstance(v, dict):
            v = replace_dash_with_underscore(v)
        elif isinstance(v, list):
            new_list = []
            for v_item in v:
                v_item = replace_dash_with_underscore(v_item)
                new_list.append(v_item)
            v = new_list
        new[k.replace('-', '_')] = v
    return new
    

def generate_request_data(node_type, service_type, action, input_data):
    TEMPLATE_FILE = "./templates/%s/%s-%s-template.txt" %(node_type, action, service_type)
    template_content = read_file(TEMPLATE_FILE)
    template = airspeed.Template(template_content)
    
    data = replace_dash_with_underscore(input_data)
    print data

    output = template.merge(data)

    request_file = None
    if node_type == "junos":
        xml_data = xml.dom.minidom.parseString(output)
        pretty_xml =  xml_data.toprettyxml()
        formatted_output =  pretty_xml.splitlines(True)

        request_file = "./output/%s-%s-%s-netconf-request.xml" %(node_type, action, service_type)
        with open(request_file, "wb") as text_file:
            for line in formatted_output:
                line = line.strip("\n\r\t ")
                if line != '':
                    text_file.write(line + "\n")
    elif node_type == "iosxr":
        formatted_output =  output.splitlines(True)
        request_file = "./output/%s-%s-%s-cli-request.txt" %(node_type, action, service_type)
        with open(request_file, "wb") as text_file:
            for line in formatted_output:
                line = line.strip("\n\r\t ")
                if line != '':
                    text_file.write(line + "\n")
    elif node_type == "iosxe":
        formatted_output =  output.splitlines(True)
        request_file = "./output/%s-%s-%s-cli-request.txt" %(node_type, action, service_type)
        with open(request_file, "wb") as text_file:
            for line in formatted_output:
                line = line.strip("\n\r\t ")
                if line != '':
                    text_file.write(line + "\n")

    return request_file
    
