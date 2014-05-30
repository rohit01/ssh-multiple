#!/usr/bin/env python
#
# Takes a list of server names as command line argument in the form:
# <user@server1:password> <user@server2:password> ...
# And:
# 1. Provides a shell like interface for inputting commands
# 2. Executes the inputted command on all the remote servers in parallel
# 3. Displays the output of the command server-wise, with the server name as a 
#    prefix for every line
#
# Author - @rohit01
#

import gevent
import gevent.monkey
gevent.monkey.patch_all()

import paramiko
import sys
import getpass

# Global variables
ssh_server_list = {}
TIMEOUT = 30            # 30 seconds
PROMPT_STRING = "$ "


def print_help():
    print "Interactive shell to ssh into multiple remote servers and execute" \
          " commands simultanously"
    print ""
    print "Sample usage:"
    print "\t%s <user@server1:password> [<user@server2:password> " \
          "<user@server3:password> ...]" % sys.argv[0]
    sys.exit()


def set_server_details():
    if '-h' in sys.argv or '--help' in sys.argv:
        print_help()
    for argument in sys.argv[1:]:
        argument = argument.strip()
        if not argument:
            continue
        temp_argument = argument
        if '@' in temp_argument:
            username = temp_argument.split('@')[0]
            temp_argument = temp_argument.split('@')[1]
        else:
            username = getpass.getuser()
        if ':' in temp_argument:
            hostname = temp_argument.split(':')[0]
            password = temp_argument.split(':')[1]
        else:
            hostname = temp_argument
            password = None
        ssh_client = paramiko.SSHClient()
        ssh_client.load_system_host_keys()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh_client.connect(hostname, username=username, password=password)
        except Exception as e:
            print "Exception: %s. Ignoring: '%s'" % (e.message, argument)
            continue
        ssh_server_list[hostname] = ssh_client


def exeute_command(hostname, ssh_client, command):
    stdin, stdout, stderr = ssh_client.exec_command(command)
    output = ''.join(stdout.readlines())
    output = "%s: %s%s" % (hostname, output, ''.join(stderr.readlines()))
    output = output.replace('\n', '\n%s: ' % hostname)
    print output
    print ""


def close_connections():
    print "Closing connections. Please wait!"
    for ssh_client in ssh_server_list.values():
        ssh_client.close()
    print "Done"


def interactive_shell():
    print "Entering interactive shell to execute commands in all servers."
    print ""
    while True:
        try:
            command = raw_input(PROMPT_STRING).strip()
            thread_list = []
            for hostname, ssh_client in ssh_server_list.items():
                thread = gevent.spawn(exeute_command, hostname, ssh_client, 
                                      command)
                thread_list.append(thread)
            gevent.joinall(thread_list, timeout=TIMEOUT)
        except KeyboardInterrupt:
            close_connections()
            break
        except EOFError:
            close_connections()
            break


def run():
    set_server_details()
    if not ssh_server_list:
        print "Server details missing. Aborting!"
        print "Try `%s -h/--help' for more information" % sys.argv[0]
        sys.exit(1)
    interactive_shell()


if __name__ == '__main__':
    run()
