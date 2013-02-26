#!/bin/sh

CFG=$1
MPM=`echo $CFG | sed -e 's/\\(^[^-]*\\)-.*/\\1/'`
OUT=`echo $CFG | sed -e 's/\\(^[^-]*-[^-]*\\).txt/\\1/'`.csv

SIM=$2

if test x"$SIM" = x""; then
    python simulate-$MPM.py $CFG > $OUT
else
    python simulate-$MPM-$SIM.py $CFG > $OUT
fi

python chart-$MPM.py $OUT
