#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os, sys
from daemonize import Daemonize

import logging
import subprocess
import time

import telepot
from telepot.loop import MessageLoop

# Config file in the following format (one value per line):
# TOKEN
# TRANSMISSION_USER
# TRANSMISSION_PASSWORD
# AUTHORIZED_USERS (comma separated list)
# DEFAULT_DOWNLOAD_PATH
# DEFAULT_DOWNLOAD_FOLDER
SETTINGS_FILENAME = 'main.config'

telegram_bot = None 

with open(SETTINGS_FILENAME) as f:
  lineList = f.read().splitlines()
TOKEN, TRANSMISSION_USER, TRANSMISSION_PASSWORD, users, DEFAULT_DOWNLOAD_PATH, DEFAULT_DOWNLOAD_FOLDER = lineList
AUTHORIZED_USERS = map(int, users.split(','))

TRANSMISSION_REMOTE_BASE = "transmission-remote -n '%s:%s' " % (TRANSMISSION_USER, TRANSMISSION_PASSWORD)

def execute_command(cmd, returns=True):
    result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = result.communicate()
    if returns:
        return "%s: %s%s%s" % (str(result.returncode), output, "" if not output else "\r\n", err) 

def cmd_add_torrent(magnet=None, location=DEFAULT_DOWNLOAD_FOLDER):
    cmd = "%s --add '%s'" % (TRANSMISSION_REMOTE_BASE, magnet)
    if location != DEFAULT_DOWNLOAD_FOLDER:
        download_dir = DEFAULT_DOWNLOAD_PATH + location
        cmd = "%s --download-dir %s" % (cmd, download_dir)
    return execute_command(cmd)

def cmd_manage_torrent(command, torrents):
    cmd = "%s -t %s %s" % (TRANSMISSION_REMOTE_BASE, torrents, command)
    return execute_command(cmd)

def cmd_torrent(command):
    cmd = "%s %s" % (TRANSMISSION_REMOTE_BASE, command)
    return execute_command(cmd)    

def cmd_ipsec(arg):
    if(arg not in ["start","stop","restart","status"]):
        return "Incorrect verb"       
    cmd = "ipsec " + arg
    result = execute_command(cmd)
    if(arg in ["start", "restart"]):
        handle_dns()
    return result

def handle_add(args):
    if(len(args) == 1):
        return cmd_add_torrent(magnet=args[0])
    if(len(args) == 2):
        return cmd_add_torrent(args[0], args[1])
    return 'Incorrect number of arguments, use: /add <magnet> [folder]'

def handle_start(args):
    if(len(args) > 1):
        return 'Incorrect number of arguments, use: /start [torrents]'
    torrents = "all" if len(args) == 0 else args[0]
    return cmd_manage_torrent("--start", torrents)

def handle_speed_limit(args):
    if(len(args) != 1):
        return 'Incorrect number of arguments, use: /speed_limit <on|off>'
    cmd = args[0]
    if(cmd not in ["on", "off"]):
        return 'Wrong argument, use: /speed_limit <on|off>'
    command = {
        "on": "-as",
        "off": "-AS"
    }[cmd]
    return cmd_torrent(command)

def handle_stop(args):
    if(len(args) > 1):
        return 'Incorrect number of arguments, use: /stop [torrents]'
    torrents = "all" if len(args) == 0 else args[0]
    return cmd_manage_torrent("--stop", torrents)

def handle_remove(args):
    if(len(args) > 1):
        return 'Incorrect number of arguments, use: /delete [torrents]'
    torrents = "all" if len(args) == 0 else args[0]
    return cmd_manage_torrent("--remove", torrents)

def handle_list(args):
    return cmd_torrent("--list")

def handle_vpn(args):
    if(len(args) == 1):
        return cmd_ipsec(args[0])
    return 'Incorrect number of arguments, use: /vpn <status|start|restart|stop>'

def handle_dns(args):
    cmd = """
if grep -q 8\\.8\\.[48].[48] /etc/resolv.conf; then
    echo Already there
else
    echo Adding
cat <<EOF | tee /etc/resolv.conf --append
nameserver 8.8.8.8
nameserver 8.8.4.4
EOF

fi
    """
    return execute_command(cmd)

def handle_unknown(args):
    return 'Unknown command'

def action(msg):
    user_id = msg['from']['id']
    chat_id = msg['chat']['id']
    if(user_id not in AUTHORIZED_USERS):
        telegram_bot.sendMessage(chat_id, 'Not authorized ' + str(user_id))
        return
    
    try:
        command = msg['text'].split(' ')
        reply = {
                '/add': handle_add,
                '/remove': handle_remove,
                '/start': handle_start,
                '/speed_limit': handle_speed_limit,
                '/stop': handle_stop,
                '/list': handle_list,
                '/vpn': handle_vpn,
                '/dns': handle_dns,
            }.get(command[0], handle_unknown)(command[1:]) if (len(command) > 0) else "Where's a command?"
    except Exception as e:
        reply = 'Ups, error: ' + str(e)
    reply = "<empty>" if not reply else reply 
    telegram_bot.sendMessage(chat_id, reply)

def main():
    global telegram_bot
    handle_dns([])
    telegram_bot = telepot.Bot(TOKEN)
    MessageLoop(telegram_bot, action).run_as_thread()
    while(1):
        time.sleep(10)
    
if __name__ == '__main__':
    myname=os.path.basename(sys.argv[0])
    pidfile='/tmp/%s' % myname       # any name
    daemon = Daemonize(app=myname,pid=pidfile, action=main)
    daemon.stdout = '/home/osmc/main.stdout.txt' # MUST BE ABSOLUTE PATH
    daemon.stderr = '/home/osmc/main.stderr .txt'
    daemon.start()
