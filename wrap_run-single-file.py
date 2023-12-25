#!/usr/bin/env python

import sys
import os
import subprocess
import time


class RestartSignal(Exception):
    pass


def read_until_empty(file_descriptor):
    # MAKE SURE that the given file descriptor
    # is set to non-blocking mode.
    output = ""
    line = file_descriptor.readline()
    while line != "":
        output += line
        # time.sleep(0.1)
        line = file_descriptor.readline()
    return output.rstrip()


class ProcessRunner:
    def __init__(
        self,
        cmd,
        print_output_on_screen: bool = True,
        stdout_callback=lambda x: None,
        stderr_callback=None,
    ):
        self.cmd = cmd
        self.print_output_on_screen = print_output_on_screen

        if stderr_callback is None:
            stderr_callback = stdout_callback

        self.stdout_callback = stdout_callback
        self.stderr_callback = stderr_callback

    def run(self, poll_rate: float = 1):
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1,
            text=True,
        )
        # The following make it so that readline on the target file
        # (i.e. stderr) is non-blocking.
        # NOTE: it only works on unix system.
        os.set_blocking(self.process.stdout.fileno(), False)
        os.set_blocking(self.process.stderr.fileno(), False)
        exit_status = self.process.poll()
        while exit_status is None:
            time.sleep(poll_rate)

            stdout = read_until_empty(self.process.stdout)
            stderr = read_until_empty(self.process.stderr)
            if self.print_output_on_screen:
                if stdout:
                    print(stdout)
                if stderr:
                    print(stderr, file=sys.stderr)

            if stdout:
                self.stdout_callback(stdout)
            if stderr:
                self.stderr_callback(stderr)

            exit_status = self.process.poll()
        return exit_status

    def kill(self):
        self.process.kill()


def stdout_callback(output_line):
    """
    The traceback signal some sort of error in the whole chrome process, which cannot
    be refined without restarting.

    Cannot read properties of undefined (reading 'close') URL: https://abc.xyz
    Stack: TypeError: Cannot read properties of undefined (reading 'close')
        at exports.getPageData (/home/soraxas/single-file-cli/back-ends/puppeteer.js:59:15)
        at async capturePage (/home/soraxas/single-file-cli/single-file-cli-api.js:256:20)
        at async runNextTask (/home/soraxas/single-file-cli/single-file-cli-api.js:176:20)
        at async Promise.all (index 0)
        at async runNextTask (/home/soraxas/single-file-cli/single-file-cli-api.js:192:3)
        at async Promise.all (index 0)
        at async runNextTask (/home/soraxas/single-file-cli/single-file-cli-api.js:192:3)
        at async Promise.all (index 0)
        at async runNextTask (/home/soraxas/single-file-cli/single-file-cli-api.js:192:3)
        at async Promise.all (index 0)
    """
    if "Cannot read properties of undefined (reading 'close')" in output_line:
        raise RestartSignal()


if len(sys.argv) <= 1:
    print("no command given.")
    exit(1)

cmd = sys.argv[1:]

i = 0
try:
    while True:
        # keep running until it returns status 0
        try:
            print(f"============= RUN {i} =============")
            i += 1
            runner = ProcessRunner(cmd, stdout_callback=stdout_callback)
            if runner.run() == 0:
                break
        except RestartSignal:
            print(f"-----------------------------------")
            print(f"  Chrome error detected. killing.")
            print(f"-----------------------------------")
            runner.process.kill()
except KeyboardInterrupt:
    runner.process.kill()
