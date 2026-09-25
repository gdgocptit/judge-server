"""Run inside the BEAM image with SYS_PTRACE; checks real sandboxed submissions."""

from subprocess import PIPE

from dmoj.executors.ELIXIR import Executor as Elixir
from dmoj.executors.ERLANG import Executor as Erlang

RUNTIMES = {'elixir': '/opt/elixir/bin/elixir', 'escript': '/usr/local/bin/escript', 'erl': '/usr/local/bin/erl'}
PROGRAMS = {
    Elixir: {
        'sum': 'IO.read(:eof) |> String.split() |> Enum.map(&String.to_integer/1) |> Enum.sum() |> IO.puts()',
        'wrong': 'IO.puts(0)',
        'syntax': 'this is not valid !!!',
        'timeout': 'Stream.cycle([1]) |> Enum.each(fn _ -> :ok end)',
        'memory': 'IO.inspect(Enum.to_list(1..10_000_000))',
        'read': 'case File.read("/judge.yml") do {:error, :eacces} -> IO.puts("blocked"); _ -> IO.puts("unsafe") end',
        'write': 'case File.write("/tmp/beam-escape", "x") do {:error, :eacces} -> IO.puts("blocked"); _ -> IO.puts("unsafe") end',
        'network': 'case :gen_tcp.connect({127,0,0,1}, 80, [], 100) do {:error, :eacces} -> IO.puts("blocked"); _ -> IO.puts("unsafe") end',
        'exec': 'IO.puts(:os.cmd(~c"id"))',
    },
    Erlang: {
        'sum': 'main(_) -> {ok,[A,B]}=io:fread("","~d ~d"), io:format("~B~n",[A+B]).',
        'wrong': 'main(_) -> io:format("0~n").',
        'syntax': 'this is not valid !!!',
        'timeout': 'main(_) -> F=fun Self() -> Self() end, F().',
        'memory': 'main(_) -> io:format("~p~n",[lists:seq(1,10000000)]).',
        'read': 'main(_) -> {error,eacces}=file:read_file("/judge.yml"), io:format("blocked~n").',
        'write': 'main(_) -> {error,eacces}=file:write_file("/tmp/beam-escape",<<"x">>), io:format("blocked~n").',
        'network': 'main(_) -> {error,eacces}=gen_tcp:connect({127,0,0,1},80,[],100), io:format("blocked~n").',
        'exec': 'main(_) -> io:format("~s",[os:cmd("id")]).',
    },
}


def run(executor, source, data=b'', time=2, memory=262144):
    program = executor('beamcheck', source.encode())
    try:
        process = program.launch(time=time, memory=memory, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate(data)
        return process, stdout, stderr
    finally:
        program.cleanup()


def main():
    for executor, programs in PROGRAMS.items():
        executor.runtime_dict = RUNTIMES
        assert executor.run_self_test()
        for a, b in [(2, 3), (-1000000000, 999999999), (1000000000, 1000000000)]:
            process, stdout, stderr = run(executor, programs['sum'], f'{a} {b}\n'.encode())
            assert process.returncode == 0 and stdout.strip() == str(a + b).encode(), (stdout, stderr)
        if executor is Erlang:
            process, stdout, stderr = run(executor, '#!/usr/bin/env escript\n' + programs['sum'], b'2 3\n')
            assert process.returncode == 0 and stdout.strip() == b'5', (stdout, stderr)
        process, stdout, _ = run(executor, programs['wrong'], b'2 3\n')
        assert process.returncode == 0 and stdout.strip() != b'5'
        process, _, _ = run(executor, programs['syntax'])
        assert process.returncode != 0 and not process.protection_fault
        process, _, _ = run(executor, programs['timeout'], time=1)
        assert process.is_tle
        process, _, stderr = run(executor, programs['memory'], memory=98304)
        assert process.is_mle, (process.returncode, process.max_memory, stderr)
        for check in ('read', 'write', 'network'):
            process, stdout, stderr = run(executor, programs[check])
            assert process.returncode == 0 and stdout.strip() == b'blocked', (check, stdout, stderr)
        process, _, _ = run(executor, programs['exec'])
        assert process.protection_fault
        print(f'{executor.name}: AC, wrong answer, syntax, TLE, MLE, file/network/exec isolation passed')


if __name__ == '__main__':
    main()
