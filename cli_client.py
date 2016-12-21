import paramiko
import re
import time


def send_command(command):
    global connection
    pause = 0.01

    print command
    connection.send(command + "\n")

    config_error = False
    time.sleep(pause)
    output = ''
    while True:
        if not connection.recv_ready():
            time.sleep(pause)
            continue

        output += connection.recv(9999)
        if re.search(r"% Invalid input detected at", output):
            print "Error occurred during configuration of the command:  %s" %(command)
            config_error = True
            break
        elif re.search(r"% Failed to commit one or more configuration items during a pseudo-atomic operation", output):
            print "Error occurred during configuration of the command:  %s" %(command)
            config_error = True
            break
        elif output.endswith("#"):
            break
    print output
    return config_error

    

ssh = None
connection = None

def open(node_info):
    host=node_info["host"]
    user = node_info["user"]
    password = node_info["password"]

    global ssh
    global connection
    ssh = paramiko.SSHClient()

    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username = user, password = password, allow_agent=False, look_for_keys=False)
    connection = ssh.invoke_shell()



def configure(commands):
    global connection
    is_success = False
    config_error = False
    for command in commands:
        if config_error:
            break;
        config_error = send_command(command)


    if config_error:
        send_command("abort")
    else:
        error = send_command("commit")
        if error:
            send_command("show configuration failed")
            send_command("abort")
        else:
            is_success = True
            send_command("end")
    return is_success


def close():
    global ssh
    ssh.close()


def edit_config(node_info, command_data):
    open(node_info)
    is_success = configure(command_data)
    close()
    return is_success
