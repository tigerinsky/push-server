#!/bin/bash
dir=`dirname $0`
cd $dir
kill -9 `cat pid` && rm -rf pid
cd - >/dev/null
