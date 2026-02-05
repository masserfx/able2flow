#!/bin/bash
# Spustit Python test bez načítání zsh konfigurace

export PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
cd /Users/lhradek/code/work/flowable
/usr/bin/python3 test_e2e_simple.py
