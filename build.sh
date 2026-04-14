#!/bin/bash
set -e

cd ~/RemindMe
export PATH=$PATH:~/.local/bin

sed -i "s/\r$//" buildozer.spec
yes | ~/.local/bin/buildozer android clean
yes | ~/.local/bin/buildozer android release > build.log 2>&1
