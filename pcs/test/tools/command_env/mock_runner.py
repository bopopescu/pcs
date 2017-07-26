from __future__ import (
    absolute_import,
    division,
    print_function,
)

from os import path

from pcs import settings
from pcs.test.tools.assertions import assert_xml_equal


CALL_TYPE_RUNNER = "CALL_TYPE_RUNNER"

def create_check_stdin_xml(expected_stdin):
    def stdin_xml_check(stdin, command, order_num):
        assert_xml_equal(
            expected_stdin,
            stdin,
            (
                "Trying to run command no. {0}"
                "\n\n    '{1}'\n\nwith expected xml stdin.\n"
            ).format(order_num,  command)
        )
    return stdin_xml_check

def check_no_stdin(stdin, command, order_num):
    if stdin:
        raise AssertionError(
            (
                "With command\n\n    '{0}'\n\nno stdin expected but was"
                "\n\n'{1}'"
            )
            .format(command, stdin)
        )

COMMAND_COMPLETIONS = {
    "crm_resource": path.join(settings.pacemaker_binaries, "crm_resource"),
    "cibadmin": path.join(settings.pacemaker_binaries, "cibadmin"),
    "crm_mon": path.join(settings.pacemaker_binaries, "crm_mon"),
    "sbd": settings.sbd_binary,
}

def complete_command(command):
    for shortcut, full_path in COMMAND_COMPLETIONS.items():
        if command.startswith("{0} ".format(shortcut)):
            return full_path + command[len(shortcut):]
    return command

def bad_call(order_num, expected_command, entered_command):
    return (
        "As {0}. command expected\n    '{1}'\nbut was\n    '{2}'"
        .format(order_num, expected_command, entered_command)
    )


class Call(object):
    type = CALL_TYPE_RUNNER

    def __init__(
        self, command, stdout="", stderr="", returncode=0, check_stdin=None
    ):
        """
        callable check_stdin raises AssertionError when given stdin doesn't
            match
        """
        self.type = CALL_TYPE_RUNNER
        self.command = complete_command(command)
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.check_stdin = check_stdin if check_stdin else check_no_stdin

    def __repr__(self):
        return str("<Runner '{0}' returncode='{1}'>").format(
            self.command,
            self.returncode
        )


class Runner(object):
    def __init__(self, call_queue=None):
        self.__call_queue = call_queue

    def run(
        self, args, stdin_string=None, env_extend=None, binary_output=False
    ):
        command = " ".join(args)
        i, call = self.__call_queue.take(CALL_TYPE_RUNNER, command)

        if command != call.command:
            raise self.__call_queue.error_with_context(
                bad_call(i, call.command, command)
            )

        call.check_stdin(stdin_string, command, i)
        return  call.stdout, call.stderr, call.returncode
