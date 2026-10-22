#!/bin/zsh
set -eu
cd -- "${0:A:h}"
if [[ ! -x .venv/bin/streamlit ]]; then
  print 'Create the Python 3.12 environment and install requirements-dev.txt first. See README.md.'
  exit 1
fi
exec .venv/bin/streamlit run app.py --server.address 127.0.0.1 --server.port 8501
