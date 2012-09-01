#!/bin/sh

CFG=$1
MPM=`echo $CFG | sed -e 's/\\(^[^-]*\\)-.*/\\1/'`
OUT=`echo $CFG | sed -e 's/\\(^[^-]*-[^-]*\\).txt/\\1/'`.csv

python simulate-$MPM.py $CFG > $OUT
python chart.py $OUT
