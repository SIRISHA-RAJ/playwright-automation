import paramiko
import time

HOST = "192.168.1.107"
USERNAME = "sysadmin"
PASSWORD = "admin@123"

def apply_enb_config(config_file):

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(HOST, username=USERNAME, password=PASSWORD)

    print("\nConnected to callbox")

    shell = ssh.invoke_shell()

    time.sleep(1)

    # Enter sudo mode
    shell.send("sudo su\n")
    time.sleep(1)

    # Execute commands
    shell.send(f"ln -sf {config_file} /root/enb/config/enb.cfg\n")
    time.sleep(3)

    shell.send("service lte restart\n")
    time.sleep(3)

    # Read output
    output = shell.recv(10000).decode()
    #print(output)

    ssh.close()

    print("Configuration applied successfully\n")
