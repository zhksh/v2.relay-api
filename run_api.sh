#!/bin/bash

scriptname=`basename "$0"`
config_file=""

if [ -f api.pid ];then
  pid=$(cat api.pid)
  echo "killing api $pid"
  kill $pid
  rm api.pid
else
  # source ~/.bashrc    # <- !!!
  # conda activate $env_name
	echo "running $scriptname"
	nohup python main.py > api.log 2>&1 & echo $! > api.pid 
  sleep 2
fi
