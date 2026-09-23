# VPS updates

Push changes to `gdgocptit/judge-server`, branch `master`, then run on the VPS:

```sh
bash /srv/dmoj/judge-server/deploy/update.sh
```

The script backs up data/configuration, pulls with `--ff-only`, builds the checked
out source into an image tagged with its commit, recreates both workers and runs
the existing seven-submission grading/sandbox check. Use a quiet period with no
active submissions: replacing workers interrupts jobs in progress.

`dmoj/judge-tier2:runtime-base` is a preserved copy of the originally installed
image (ID `sha256:0f1ce939c8cb7f558f91df0dfcc1d32d158039e21919fda494edf848d73adfda`).
It supplies the existing compilers/runtime configuration. The Dockerfile replaces
its judge source and recompiles the Python/Cython package from this repository.
This base exists on the current VPS only; save/load it or provision the upstream
runtime image separately when moving servers. Runtime/compiler upgrades require
a separate base image update.

Compose uses `gdgocptit/judge-server:production`; judge keys and problem data stay
in existing external mounts. The previous image is retained for manual rollback:

```sh
docker tag gdgocptit/judge-server:previous gdgocptit/judge-server:production
docker compose -f /srv/dmoj/compose.yml up -d --force-recreate
```

If a build fails, running workers are left on their previous image. If the grading
check fails after replacement, inspect logs and roll back. Commit-tagged images
accumulate; review disk use and remove obsolete images when no longer needed.
