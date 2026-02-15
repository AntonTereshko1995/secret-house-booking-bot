#!/bin/bash
cd "$(dirname "$0")"
export ENV=debug
python src/main.py
