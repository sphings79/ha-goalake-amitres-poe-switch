#!/bin/sh
# Run all tests: client tests need real sockets, flow tests need the Home Assistant plugin.
cd "$(dirname "$0")/.." || exit 1
.venv/bin/python -m pytest -q -p no:homeassistant tests/test_client.py || exit 1
.venv/bin/python -m pytest -q tests --ignore=tests/test_client.py
