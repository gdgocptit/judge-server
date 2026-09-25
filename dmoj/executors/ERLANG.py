import glob
import os

from dmoj.cptbox.isolate import DeniedSyscall, protection_fault
from dmoj.cptbox.syscalls import sys_execve
from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = 'erl'
    command = 'escript'
    nproc = -1
    # BEAM reserves virtual space for literals/JIT; RSS still follows the problem limit.
    address_grace = 2 * 1024 * 1024
    data_grace = 256 * 1024
    syscalls = [
        'eventfd2',
        'memfd_create',
        'ftruncate',
        'socketpair',
        'wait4',
        'setsid',
        'pselect6',
        'timerfd_settime',
        'readv',
        'getsockopt',
    ]
    test_program = 'main(_) -> io:put_chars(io:get_line("")).'
    script_header = b'#!/usr/bin/env escript\n'

    def create_files(self, problem_id, source_code):
        if not source_code.startswith(b'#!'):
            source_code = self.script_header + source_code
        super().create_files(problem_id, source_code + b'\n')

    def get_erlang_root(self):
        return os.path.dirname(os.path.dirname(os.path.realpath(self.runtime_dict['erl'])))

    def get_executable(self):
        return glob.glob(os.path.join(self.get_erlang_root(), 'erts-*/bin/beam.smp'))[0]

    def get_vm_args(self):
        return ['-boot', 'no_dot_erlang', '-run', 'escript', 'start']

    def get_security(self, launch_kwargs=None, extra_fs=None):
        security = super().get_security(launch_kwargs=launch_kwargs, extra_fs=extra_fs)
        child_setup = os.path.join(os.path.dirname(self.get_executable()), 'erl_child_setup')

        def handle_execve(debugger):
            if debugger.readstr(debugger.uarg0) != child_setup:
                raise DeniedSyscall(protection_fault, 'Only the BEAM child setup helper may be executed')

        security[sys_execve] = handle_execve
        return security

    def get_cmdline(self, **kwargs):
        return [
            self.get_executable(),
            '-S',
            '1:1',
            '-SDcpu',
            '1:1',
            '-SDio',
            '1',
            '-A',
            '1',
            '--',
            '-root',
            self.get_erlang_root(),
            '-bindir',
            os.path.dirname(self.get_executable()),
            '-progname',
            'erl',
            '--',
            '-home',
            self._dir,
            '-noshell',
            *self.get_vm_args(),
            '-extra',
            self._code,
        ]

    def get_env(self):
        return {
            **super().get_env(),
            'HOME': self._dir,
            'BINDIR': os.path.dirname(self.get_executable()),
            'ROOTDIR': self.get_erlang_root(),
            'PATH': '/usr/local/bin:/usr/bin:/bin',
            'ERL_CRASH_DUMP': '/dev/null',
        }

    @classmethod
    def get_find_first_mapping(cls):
        return {cls.command: [cls.command], 'erl': ['erl']}

    @classmethod
    def get_versionable_commands(cls):
        return [('erl', cls.runtime_dict['erl'])]

    @classmethod
    def get_version_flags(cls, command):
        return [
            (
                '+S',
                '1:1',
                '-noshell',
                '-eval',
                '{ok,V}=file:read_file(filename:join([code:root_dir(),"releases",'
                'erlang:system_info(otp_release),"OTP_VERSION"])),io:put_chars(V),halt().',
            ),
        ]
