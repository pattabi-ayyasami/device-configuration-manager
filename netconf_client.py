import socket
import string
import time
import xml.dom.minidom

import paramiko

from utils import read_file


def read_file(file_name):
    with open(file_name) as data_file:    
        data = data_file.read()
        return data


def write_to_file(data, file_name):
    with open(file_name, "wb") as text_file:
        text_file.write(data)
        
        
def edit_config(node_info, command_data):
    is_success = True

    ch, trans, conn_socket = open_session(node_info)

    send_hello(ch)
    result = send_command(ch, command_data)
    if result:
        commit_result = commit_changes(ch)
        if not commit_result:
            is_success = False
            send_discard(ch)
    else:
        is_success = False
        send_discard(ch)

    close_session(ch)
    ch.close()
    trans.close()
    conn_socket.close()
    return is_success


def delete_config(node_info, command_data):
    return edit_config(node_info, command_data)


def get_running_config(node_info, command_data):
    ch, trans, conn_socket = open_session(node_info)

    send_hello(ch)
    send_command(ch, command_data)
    close_session(ch)
    
    ch.close()
    trans.close()
    conn_socket.close()
    return True


def open_session(node_info):
    host=node_info["host"]
    user = node_info["user"]
    password = node_info["password"]
    netconf_port = 830

    # Start to open connection
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    conn_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    conn_socket.connect((host, netconf_port))
    trans = paramiko.Transport(conn_socket)
    trans.connect(username=user, password=password)

    ch = trans.open_session()
    ch.set_name('netconf')

    #Invoke NETCONF
    ch.invoke_subsystem('netconf')

    return ch, trans, conn_socket


def send_command(ch, command_data):
    # Send the data
    print "Request %s" %command_data
    ch.send(command_data)

    result=''
    while True:
        data = ch.recv(1024)
        result += data
        if data.find('</rpc-reply>') >= 0 or data.find('</hello>') >= 0:
            break
        else:
            #print "Waiting for the complete response ..."
            time.sleep(1)
    
    try:
        result=string.replace(result, ']]>]]>', '' )
        print result

        write_to_file(result, "./output/rpc-result.xml")
  
        if result.find('</rpc-error>') >= 0:
            print "RPC invocation failed"
            return False
        elif result.find('<result>false</result>') >= 0 or result.find('<result>failed</result>') >= 0:
            print "RPC action failed."
            return False
        else:
            print "RPC invocation succeed."
            pass

    except IOError as e:
        print "IOError:" + str(e)
        return False

    return True

def send_discard(channel):
    NETCONF_XML = "./netconf-data/discard.xml"
    request = read_file(NETCONF_XML)
    send_command(channel, request)


def send_hello(channel):
    HELLO_NETCONF_XML = "./netconf-data/hello.xml"
    hello_request = read_file(HELLO_NETCONF_XML)
    send_command(channel, hello_request)


def close_session(channel):
    CLOSE_NETCONF_XML = "./netconf-data/close.xml"
    close_session_request = read_file(CLOSE_NETCONF_XML)
    send_command(channel, close_session_request)


def commit_changes(channel):
    COMMIT_NETCONF_XML = "./netconf-data/commit.xml"
    commit_request = read_file(COMMIT_NETCONF_XML)
    return send_command(channel, commit_request)
