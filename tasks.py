from invoke import task
import os
from pathlib import Path
import re

PTY = (os.name != 'nt')
DOCKER_RUN = f'docker run {"-it" if PTY else ""} --rm'


HOMEDIR = Path('.').resolve()
BUILDDIR = HOMEDIR / 'build'
DATADIR  = HOMEDIR / 'data'

BUILDDIR.mkdir(parents=True, exist_ok=True)


@task
def build(c, args=''):
    """Build docker image."""
    c.run(f'docker-compose build {args}', pty=PTY)


@task
def run(c, task):
    """Run python script."""

    # determine task type and run python script
    tasks = {
        'file': (
            re.compile(r'(?P<filename>[a-zA-Z][a-zA-Z0-9_]*\.py)'),
            f'python {{filename}}'),
        'function': (
            re.compile(r'(?P<module>[a-zA-Z][a-zA-Z0-9_]*):(?P<function>[a-zA-Z][a-zA-Z0-9_]*)(?P<args>\(.*\))'),
            f'python -c \'import {{module}}; {{module}}.{{function}}{{args}}\''),
        }
    cmdline = None
    for name, (rx, cmd) in tasks.items():
        m = rx.fullmatch(task)
        if m is not None:
            cmdline = cmd.format(**m.groupdict())
            break
    if cmdline is not None:
        c.run(f'docker-compose run master {cmdline}', replace_env=False, pty=PTY)
    else:
        raise ValueError(f'Unsupported task definition: {task}')


@task
def shell(c):
    """Open shell in docker container."""
    c.run(f'docker-compose run master /bin/bash', pty=PTY)


@task
def pyspark(c):
    """Run PySpark in client container."""
    c.run(f'docker-compose run --rm --no-deps client pyspark', pty=PTY)


@task
def submit(c, cmd):
    """Run Spark command."""
    c.run(f'docker-compose run --rm client spark-submit {cmd}', pty=PTY)
