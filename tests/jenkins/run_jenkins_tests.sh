#!/bin/bash

# Setup
source ~/.bashrc
conda activate quacc
pip install --force-reinstall --no-deps git+https://gitlab.com/ase/ase.git@gulp-dir
pip install -r tests/requirements.txt
pip install -e .[dev]

# Request and run Slurm job
salloc -N 1 -n 32 -t 00:10:00 tests/jenkins/hpc_tests.sh
