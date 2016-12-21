import paramiko
import re
import time


class iosxe_client_manager:
    ssh = None
    connection = None

    def send_command(self, command):

        pause = 0.1
        print command
        command = command + "\n"
        self.connection.send(command)

        config_error = False
        time.sleep(pause)
        output = ''
        while True:
            if not self.connection.recv_ready():
                time.sleep(pause)
                continue

            output += self.connection.recv(1024)
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


    def open(self, node_info):
        host=node_info["host"]
        user = node_info["user"]
        password = node_info["password"]

        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(host, username = user, password = password, allow_agent=False, look_for_keys=False)
        self.connection = self.ssh.invoke_shell()


    def configure(self, commands):
        config_error = False
        for command in commands:
            if config_error:
                break;
            config_error = self.send_command(command)
        return config_error
    
    def close(self):
        self.ssh.close()


def edit_config(node_info, command_data):
    client = iosxe_client_manager()
    client.open(node_info)
    is_error = client.configure(command_data)
    client.close()
    return not is_error
