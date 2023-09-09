#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nrrdalrt
Version:  0.0.2
Author:   Sean O'Connell <sean@sdoconnell.net>
License:  MIT
Homepage: https://github.com/sdoconnell/nrrdalrt
About:
Task and event notifications for nrrdtask and nrrddate.

usage: nrrdalrt [-h] [-c <file>] for more help: nrrdalrt <command> -h ...

Task and event notifications for nrrdtask and nrrddate.

commands:
  (for more help: nrrdalrt <command> -h)
    config              edit configuration file
    start               start the daemon
    stop                stop the daemon
    version             show version info

optional arguments:
  -h, --help            show this help message and exit
  -c <file>, --config <file>
                        config file


Copyright © 2021 Sean O'Connell

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""
import argparse
import configparser
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime

import notify2
import tzlocal
from daemonize import Daemonize
from dateutil import parser as dtparser

APP_NAME = "nrrdalrt"
APP_VERS = "0.0.2"
APP_COPYRIGHT = "Copyright © 2021 Sean O'Connell."
APP_LICENSE = "Released under MIT license."
DEFAULT_CONFIG_FILE = f"$HOME/.config/{APP_NAME}/config"
DEFAULT_CONFIG = (
    "[main]\n"
    "# icon to use in desktop notifications\n"
    "#notify_icon =\n"
    "# command to play a sound file for desktop notifications\n"
    "#sound_cmd =\n"
    "# how often to refresh reminders (in minutes)\n"
    "#refresh_interval = 5\n"
    "# mailer command for sending reminders\n"
    "# command must include '%s' to represent the\n"
    "# email subject, '%r' to represent the recipient\n"
    "# address, and '%b' to represent the message\n"
    "# body itself.\n"
    "#mailer_cmd = mutt -s %s -- %r << EOF %b\n"
    "[commands]\n"
    "# keynames are arbitrary, you may add as many as you require\n"
    "tasks_cmd  = nrrdtask reminders 15m\n"
    "events_cmd = nrrddate reminders 15m\n"
)
DEFAULT_MAILER_CMD = "mutt -s %s -- %r << EOF %b"
DEFAULT_REFRESH_INTERVAL = 5

class Reminders():
    """Performs reminder event operations.

    Attributes:
        config_file (str): application config file.
        dflt_config (str): the default config if none is present.

    """
    def __init__(
            self,
            config_file,
            dflt_config):
        """Initializes a Reminders() object."""
        self.config_file = config_file
        self.config_dir = os.path.dirname(self.config_file)
        self.dflt_config = dflt_config
        self.notify_icon = None
        self.refresh_interval = DEFAULT_REFRESH_INTERVAL
        self.mailer_cmd = None
        self.sound_cmd = None
        self.commands = []
        self.ltz = tzlocal.get_localzone()
        self._default_config()
        self._parse_config()
        self._read_reminders()

        # editor (required for some functions)
        self.editor = os.environ.get("EDITOR")

    def _datetime_or_none(self, timestr):
        """Verify a datetime object or a datetime string in ISO format
        and return a datetime object or None.

        Args:
            timestr (str): a datetime formatted string.

        Returns:
            timeobj (datetime): a valid datetime object or None.

        """
        if isinstance(timestr, datetime):
            timeobj = timestr.astimezone(tz=self.ltz)
        else:
            try:
                timeobj = dtparser.parse(timestr).astimezone(tz=self.ltz)
            except (TypeError, ValueError, dtparser.ParserError):
                timeobj = None
        return timeobj

    def _default_config(self):
        """Create a default configuration directory and file if they
        do not already exist.
        """
        if not os.path.exists(self.config_file):
            try:
                os.makedirs(self.config_dir, exist_ok=True)
                with open(self.config_file, "w",
                          encoding="utf-8") as config_file:
                    config_file.write(self.dflt_config)
            except IOError:
                self._error_exit(
                    "Config file doesn't exist "
                    "and can't be created.")

    def _check_reminders(self):
        """Checks reminders and generates emails and notifications."""
        now = datetime.now(tz=self.ltz)
        today = now.date()
        this_hour = now.hour
        this_minute = now.minute
        for reminder in self.reminders:
            rem_dt = self._datetime_or_none(reminder.get('datetime'))
            notification = reminder.get('notification')
            address = reminder.get('address')
            summary = reminder.get('summary')
            body = reminder.get('body')
            if (rem_dt.date() == today and
                    rem_dt.hour == this_hour and
                    rem_dt.minute == this_minute):
                if notification == "email" and address and self.mailer_cmd:
                    subject = f"\"Reminder: {summary}\""
                    body = (
                        "\nReminder:\n\n"
                        f"{body}\n"
                        "EOF\n"
                    )
                    raw_cmd = self.mailer_cmd.split()
                    # this could probably be done with list comp
                    # but might be more confusing than a simple loop
                    this_mailer_cmd = []
                    for item in raw_cmd:
                        if item == '%s':
                            this_mailer_cmd.append(subject)
                        elif item == '%r':
                            this_mailer_cmd.append(address)
                        elif item == '%b':
                            this_mailer_cmd.append(body)
                        else:
                            this_mailer_cmd.append(item)
                    this_mailer_cmd = " ".join(this_mailer_cmd)
                    try:
                        subprocess.run(
                            this_mailer_cmd,
                            capture_output=True,
                            check=True,
                            shell=True)
                    except subprocess.CalledProcessError:
                        pass
                elif notification == "display":
                    if self.notify_icon:
                        this_icon = self.notify_icon
                    else:
                        this_icon = ""
                    desktop_notify = notify2.Notification(
                        summary="Reminder",
                        message=body,
                        icon=this_icon)
                    desktop_notify.set_urgency(notify2.URGENCY_NORMAL)
                    desktop_notify.set_timeout(notify2.EXPIRES_NEVER)
                    desktop_notify.show()
                    if self.sound_cmd:
                        try:
                            subprocess.run(
                                self.sound_cmd,
                                capture_output=True,
                                check=True,
                                shell=True)
                        except subprocess.CalledProcessError:
                            pass

    @staticmethod
    def _error_exit(errormsg):
        """Print an error message and exit with a status of 1

        Args:
            errormsg (str): the error message to display.

        """
        print(f'ERROR: {errormsg}.')
        sys.exit(1)

    def _parse_config(self):
        """Read and parse the configuration file."""
        config = configparser.ConfigParser()
        if os.path.isfile(self.config_file):
            try:
                config.read(self.config_file)
            except configparser.Error:
                self._error_exit("Error reading config file")

            if "main" in config:
                if config["main"].get("notify_icon"):
                    self.notify_icon = os.path.expandvars(
                        os.path.expanduser(
                            config["main"].get("notify_icon")))

                if config["main"].get("refresh_interval"):
                    try:
                        self.refresh_interval = int(
                            config["main"].get("refresh_interval",
                                               DEFAULT_REFRESH_INTERVAL))
                    except ValueError:
                        self.refresh_interval = DEFAULT_REFRESH_INTERVAL

                self.mailer_cmd = (
                    config["main"].get("mailer_cmd",
                                       DEFAULT_MAILER_CMD,
                                       raw=True))
                self.sound_cmd = (
                    config["main"].get("sound_cmd",
                                       raw=True))

            if "commands" in config:
                command_items = config.items("commands")
                for cmd in command_items:
                    self.commands.append(cmd[1])
        else:
            self._error_exit("Config file not found")

    def _read_reminders(self):
        """Reads reminders from command output."""
        self.reminders = []
        for command in self.commands:
            try:
                cmd = subprocess.run(
                    command,
                    capture_output=True,
                    check=True,
                    shell=True)
            except subprocess.CalledProcessError:
                pass
            else:
                result = cmd.stdout.decode('utf-8')
                if result:
                    try:
                        json_read = json.loads(result)
                    except ValueError:
                        pass
                    else:
                        rem_read = json_read.get('reminders')
                        if rem_read:
                            for reminder in rem_read:
                                self.reminders.append(reminder)

    @staticmethod
    def _format_timestamp(timeobj, pretty=False):
        """Convert a datetime obj to a string.

        Args:
            timeobj (datetime): a datetime object.
            pretty (bool):      return a pretty formatted string.

        Returns:
            timestamp (str): "%Y-%m-%d %H:%M:%S" or "%Y-%m-%d[ %H:%M]".

        """
        if pretty:
            if timeobj.strftime("%H:%M") == "00:00":
                timestamp = timeobj.strftime("%Y-%m-%d")
            else:
                timestamp = timeobj.strftime("%Y-%m-%d %H:%M")
        else:
            timestamp = timeobj.strftime("%Y-%m-%d %H:%M:%S")
        return timestamp

    def edit_config(self):
        """Edit the config file (using $EDITOR) and then reload config."""
        if self.editor:
            try:
                subprocess.run(
                    [self.editor, self.config_file], check=True)
            except subprocess.SubprocessError:
                self._error_exit("failure editing config file")
        else:
            self._error_exit("$EDITOR is required and not set")

    def init(self):
        """Initialize the reminder timers and start monitoring."""
        notify2.init("nrrdalrt")
        seconds = 60 - datetime.now(tz=self.ltz).second
        time.sleep(seconds)
        self.start()

    def start(self):
        """Start the reminder collection and monitoring loop."""
        while True:
            if datetime.now(tz=self.ltz).minute % self.refresh_interval == 0:
                self._read_reminders()
            self._check_reminders()
            time.sleep(60)


def parse_args():
    """Parse command line arguments.

    Returns:
        args (dict):    the command line arguments provided.

    """
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description='Task and event notifications for nrrdtask and nrrddate.')
    parser._positionals.title = 'commands'
    parser.set_defaults(command=None)
    subparsers = parser.add_subparsers(
        metavar=f'(for more help: {APP_NAME} <command> -h)')
    config = subparsers.add_parser(
        'config',
        help='edit configuration file')
    config.set_defaults(command='config')
    start = subparsers.add_parser(
        'start',
        help='start the daemon')
    start.set_defaults(command='start')
    stop = subparsers.add_parser(
        'stop',
        help='stop the daemon')
    stop.set_defaults(command='stop')
    version = subparsers.add_parser(
        'version',
        help='show version info')
    version.set_defaults(command='version')
    parser.add_argument(
        '-c',
        '--config',
        dest='config',
        metavar='<file>',
        help='config file')
    args = parser.parse_args()
    return parser, args


def main():
    """Entry point. Parses arguments, creates daemon obj."""
    def _stop_daemon(silent=False):
        """Stop the running daemon (if any).

        Args:
            silent (bool): squelch error messages.

        """
        if os.path.isfile(pidfile):
            try:
                with open(pidfile, 'r', encoding='utf-8') as pid:
                    running = int(pid.read())
            except (OSError, IOError, ValueError):
                if not silent:
                    print(f"ERROR: failed reading {pidfile}.")
                    sys.exit(1)
            else:
                try:
                    os.kill(running, signal.SIGTERM)
                except OSError:
                    if not silent:
                        print(f"ERROR: failed stopping PID {running}")
                        sys.exit(1)
                else:
                    while os.path.isfile(running):
                        time.sleep(.25)
                    sys.exit(0)
        else:
            if not silent:
                print("ERROR: PID file not found. Is the daemon running?")
                sys.exit(1)

    if os.environ.get("XDG_CONFIG_HOME"):
        config_file = os.path.join(
            os.path.expandvars(os.path.expanduser(
                os.environ["XDG_CONFIG_HOME"])), APP_NAME, "config")
    else:
        config_file = os.path.expandvars(
            os.path.expanduser(DEFAULT_CONFIG_FILE))

    parser, args = parse_args()

    if args.config:
        config_file = os.path.expandvars(
            os.path.expanduser(args.config))

    tempdir = tempfile.gettempdir()
    uid = os.getuid()
    hostname = os.uname()[1]
    filename = f"{uid}_{hostname}_nrrdalrt.pid"
    pidfile = os.path.join(tempdir, filename)

    if not args.command:
        parser.print_help(sys.stderr)
        sys.exit(1)
    elif args.command == "config":
        reminders = Reminders(
            config_file,
            DEFAULT_CONFIG)
        reminders.edit_config()
    elif args.command == "version":
        print(f"{APP_NAME} {APP_VERS}")
        print(APP_COPYRIGHT)
        print(APP_LICENSE)
    elif args.command == "start":
        reminders = Reminders(
            config_file,
            DEFAULT_CONFIG)
        daemon = Daemonize(
            app="nrrdalrt",
            pid=pidfile,
            action=reminders.init)
        daemon.start()
    elif args.command == "stop":
        _stop_daemon()
    else:
        sys.exit(1)


# entry point
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(1)
