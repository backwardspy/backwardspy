_default:
    @just --list

bootstrap:
    python -m venv .venv
    .venv/bin/pip install pip-tools

lock:
    .venv/bin/pip-compile --strip-extras --generate-hashes --quiet

install:
    .venv/bin/pip install -r requirements.txt

run:
    .venv/bin/python generate.py
