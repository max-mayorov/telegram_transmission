#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import subprocess

from telegram.ext import Updater, CommandHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

TOKEN = "TOKEN"
TRANSMISSION_USER = "TRANSMISSION_USER"
TRANSMISSION_PASSWORD = "TRANSMISSION_PASSWORD"
DEFAULT_DOWNLOAD_PATH = '/DEFAULT/DOWNLOAD/PATH'
DEFAULT_DOWNLOAD_FOLDER = "DEFAULT_DOWNLOAD_FOLDER"
AUTHORIZED_USERS = []


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


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
    if location != "Temp":
        cmd = cmd + " --download-dir " + download_dir
    execute_command(cmd)


def add_torrent(bot, update, args):
    if update.message.from_user.id not in AUTHORIZED_USERS:
        bot.sendMessage(update.message.chat_id, text='Get the fuck out of here ' + str(update.message.from_user.id))
        return

    magnet_url = args[0]
    try:
        if len(args) == 1:
            cmd_add_torrent(magnet=magnet_url)
            bot.sendMessage(chat_id=update.message.chat_id, text="Torrent added in Temp")
        else:
            content_type = args[1]
            cmd_add_torrent(magnet=magnet_url, location=content_type)
            bot.sendMessage(chat_id=update.message.chat_id, text="Torrent added in " + content_type)
    except Exception as e:
        bot.sendMessage(chat_id=update.message.chat_id, text="Ups, the torrent was not added: " + str(e))


def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    add_torrent_handler = CommandHandler('add', add_torrent, pass_args=True)
    dp.add_handler(add_torrent_handler)
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
