#!/bin/bash
dir=`dirname $0`
cd $dir
nohup python server.py >/dev/null 2>&1 &
echo $! > pid
cd - >/dev/null
