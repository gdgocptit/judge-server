# Local Elixir / Erlang judge

Pinned stable releases: Elixir 1.20.4 and Erlang/OTP 29.1.1, verified on
2026-09-25. The image uses the official Erlang slim image and the official
Elixir OTP 29 archive, with its SHA-256 checked during the build.

This worker runs alongside the local website, in Linux Docker (including ARM64
OrbStack on macOS). It does not replace the VPS workers.

With `site/`, `judge-server/`, `problems/` and `.local/` next to each other:

1. Start the website's local database/Redis and apply migrations as described in
   `site/dev/README.md`.
2. From `site/`, using its Python environment:

   ```sh
   python manage.py shell < dev/setup_beam.py
   python manage.py runbridged
   ```

   Keep the bridge running. The setup is restricted to DEBUG with a loopback
   database, registers both languages, enables them on existing problems, and
   creates `local-beam` with a generated key. Re-running preserves the key.
3. From `judge-server/`, in another terminal:

   ```sh
   docker compose -f deploy/compose.beam.yml up -d --build
   docker compose -f deploy/compose.beam.yml logs --tail 30
   ```

The default configuration is `../.local/beam-judge.yml` relative to the judge
repository. `DMOJ_BEAM_CONFIG` and `DMOJ_PROBLEM_ROOT` may override the mount
paths; use absolute paths for overrides. Do not commit generated judge keys.
The worker reaches the local bridge on `host.docker.internal:9999` (verified
with OrbStack); the bridge's Django endpoint stays on loopback port 9998.

New problems must allow ELIXIR/ERLANG and have test data under `problems/`.
The worker publishes runtime versions to the website after its self-tests pass.

- **Elixir:** submit an `.exs` script, reading stdin and writing stdout.
- **Erlang:** submit an `.erl` escript with `main/1`, for example:

  ```erlang
  main(_) ->
      {ok, [A, B]} = io:fread("", "~d ~d"),
      io:format("~B~n", [A + B]).
  ```

No shebang or module declaration is required. Both languages use one BEAM
scheduler; syntax errors are reported as runtime errors, as with script runtimes.
External commands and network access are blocked. BEAM's virtual address-space
allowance does not increase the problem's physical memory limit.

Run the real sandbox checks (AC, incorrect output, syntax, TLE/MLE, denied file
reads/writes, network and external command execution):

```sh
docker compose -f deploy/compose.beam.yml run --rm \
  --entrypoint /env/bin/python judge /judge/deploy/check_beam.py
```

Stop only this worker with `docker compose -f deploy/compose.beam.yml down`.
