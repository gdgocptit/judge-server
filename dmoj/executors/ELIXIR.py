import os

from dmoj.executors.ERLANG import Executor as ErlangExecutor


class Executor(ErlangExecutor):
    ext = 'exs'
    command = 'elixir'
    test_program = 'IO.write(IO.read(:line))'
    script_header = b''

    def get_vm_args(self):
        root = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(self.get_command()))), 'lib')
        return ['-elixir_root', root, '-pa', os.path.join(root, 'elixir/ebin'), '-s', 'elixir', 'start_cli']

    @classmethod
    def get_versionable_commands(cls):
        return [('elixir', cls.get_command()), *super().get_versionable_commands()]

    @classmethod
    def get_version_flags(cls, command):
        if command == 'elixir':
            return ['--short-version']
        return super().get_version_flags(command)
