#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os, sys
from daemonize import Daemonize

import logging
import subprocess
import time

import telepot
from telepot.loop import MessageLoop

# Config file in the following format:
# TOKEN
# TRANSMISSION_USER
# TRANSMISSION_PASSWORD
# AUTHORIZED_USERS (comma separated list)
# DEFAULT_DOWNLOAD_PATH
# DEFAULT_DOWNLOAD_FOLDER
SETTINGS_FILENAME = 'main.config'

with open(SETTINGS_FILENAME) as f:
  lineList = f.readlines()
TOKEN, TRANSMISSION_USER, TRANSMISSION_PASSWORD, users, DEFAULT_DOWNLOAD_PATH, DEFAULT_DOWNLOAD_FOLDER = lineList
AUTHORIZED_USERS = map(int, users.split(','))

telegram_bot = telepot.Bot(TOKEN)

def execute_command(cmd, returns=False):
    result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = result.communicate()
    if result.returncode is 0:
        if returns:
            return output
    else:
        print(err)
        print(result.returncode)
        print(output)
        raise IOError


def cmd_add_torrent(magnet=None, location=DEFAULT_DOWNLOAD_FOLDER):
    download_dir = DEFAULT_DOWNLOAD_PATH + location
    cmd = "transmission-remote -n '" + TRANSMISSION_USER + ":" + TRANSMISSION_PASSWORD + "' --add '" + magnet + "'"
    if location != DEFAULT_DOWNLOAD_FOLDER:
        cmd = cmd + ' --download-dir ' + download_dir
    execute_command(cmd)


def action(msg):
    user_id = msg['from']['id']
    chat_id = msg['chat']['id']
    if(user_id not in AUTHORIZED_USERS):
        telegram_bot.sendMessage(chat_id, 'Not authorized ' + str(user_id))
        return
    
    try:
        command = msg['text'].split(' ')
        reply = ''
        if(len(command) > 0):
            if(command[0] == '/add'):
                if(len(command) == 2):
                    reply = cmd_add_torrent(magnet=command[1])
                elif(len(command) == 3):
                    reply = cmd_add_torrent(command[1], command[2])
                else:
                    reply = 'Incorrect number of arguments, use: /add <magnet> [folder]'
            else:
                reply = 'Unknown command'
        else:
            reply = "Where's a command?"
    except Exception as e:
        reply = 'Ups, error: ' + str(e)

    telegram_bot.sendMessage(chat_id, reply)

def main():
    MessageLoop(telegram_bot, action).run_as_thread()
    while(1):
        time.sleep(10)
    
if __name__ == '__main__':
    myname=os.path.basename(sys.argv[0])
    pidfile='/tmp/%s' % myname       # any name
    daemon = Daemonize(app=myname,pid=pidfile, action=main)
    daemon.start()
