#!/bin/bash

sudo apt-get install python3 python3-dev python3-pip libxml2-dev libxslt1-dev zlib1g-dev libffi-dev libssl-dev

python3 -m venv .venv

source "$PWD/.venv/bin/activate"

pip install -r requirements.txt

playwright install
playwright install-deps

#verify
python -c "from playwright.sync_api import sync_playwright; print('OK')"