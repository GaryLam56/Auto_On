import shlex
import subprocess
import datetime
import random
import glob
import json
import sys
import os
import time
from easyprocess import Proc
from threading import Timer

class AutoOn:

    def __init__(self):

        self.default_config = {
            'away_timeout_mins' : 30
        }

        self.config = self.load_json('config.json')

        if not self.config: # If there is not configuration file
            self.config = self.default_config

        if not 'away_timeout_mins' in self.config:
            self.config['away_timeout_mins'] = self.default_config('away_timeout_mins')

        self.users = self.load_json('users.json')
        self.start_time = datetime.datetime.now()

        sys.stdout.flush()
        self.update_console_status()
        self.run_loop()


    def load_json(self, file_name):
        json_data = open(file_name)
        data = json.load(json_data)
        return data


    def run_loop(self):
        while True:
            for user in self.users:
                if not 'confirmed_not_there' in user:
                    user['confirmed_not_there'] = False
                try:
                    cmd = shlex.split("ping {0}".format(user['ip']))
                    stdout = Proc(cmd).call(timeout=1.8).stdout
                    if "bytes from" in stdout:
                        if self.should_turn_on(user):
                            self.turn_on(user)
                        self.log("User: {0} is Reachable. {1}".format(user['name'], user['ip']))
                        user['last_seen'] = datetime.datetime.now()
                        user['confirmed_not_there'] = False

                    else:
                        user['confirmed_not_there'] = True
                        last_seen = user['last_seen'] if 'last_seen' in user else "never"
                        self.log("User: {0} is NotReachable. last seen: {1}".format(user['name'], last_seen))
                    self.update_console_status()

                except subprocess.CalledProcessError:
                    print("subprocess.CalledProcessError")
                else:
                    pass


    def turn_on(self, user):
        print("Turning on computer")
        sys.stdout.write("Turning on the computer")
        os.popen("wakeonlan 88:88:88:88:87:88")


    @staticmethod
    def green(msg):
        return "\033[92m{0}\033[0m".format(msg)


    @staticmethod
    def red(msg):
        return "\033[91m{0}\033[0m".format(msg)


    def update_console_status(self):
        os.system('clear')
        sys.stdout.flush()
        string = ""
        for user in self.users:
            last_seen = user['last_seen'] if 'last_seen' in user else "Never seen"
            confirmed_not_there = user['confirmed_not_there'] if 'confirmed_not_there' in user else True
            not_here_string = last_seen if 'confirmed_not_there' in user else "Loading..."
            here_or_not = self.red(not_here_string) if confirmed_not_there  else self.green("Here")
            string = "{0}\n\r {1}: {2}".format(string, user['name'], here_or_not)
        sys.stdout.write("\r{0}".format(string))
        sys.stdout.flush()


    @staticmethod
    def log(message):
        # print message
        pass


    def should_turn_on(self, user):
        # If we haven't confirmed they aren't there, then don't turn on
        if not user['confirmed_not_there']:
            self.log("{0} was not confirmed to not be there".format(user['name']))
            return False

        # If we have confirmed they were previously not there and last_seen isn't set then turn on
        if not 'last_seen' in user:
            # Did we just restart the script?
            five_mins_ago = datetime.datetime.now() - datetime.timedelta(minutes=self.config['away_timeout_mins'])
            if five_mins_ago > self.start_time:
                return True
            else:
                self.log("{0} was never seen but we just restarted the script".format(user['name']))
                return False

        # if last seen is set and it's older than timeout return true
        time_ago = self.config['away_timeout_mins']
        distant_time = datetime.datetime.now() - datetime.timedelta(minutes=time_ago)
        if user['last_seen'] < distant_time:
            self.log("{0} was last seen more than {1} mins ago".format(user['name'], time_ago))
            return True
        else:
            # otherwise dont play
            self.log("Dont play for {0} delta was lest than 1 min {1} - {2}".format(user['name'], user['last_seen'],
                                                                                    distant_time))
            return False


class Process_runner:
    def __init__(self, cmd, timeout):
        self.run(cmd, timeout)

    @staticmethod
    def kill_proc(proc, timeout):
        timeout["value"] = True
        proc.kill()


    def run(self, cmd, timeout_sec):
        proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        timeout = {"value": False}
        timer = Timer(timeout_sec, self.kill_proc, [proc, timeout])
        timer.start()
        stdout, stderr = proc.communicate()
        timer.cancel()
        return proc.returncode, stdout.decode("utf-8"), stderr.decode("utf-8"), timeout["value"]

autoOn = AutoOn()
