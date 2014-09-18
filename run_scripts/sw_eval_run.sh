#!/bin/bash
NICE=19

for i in {1..37}; do
	nice -n $NICE python ga_runner.py -n $i -t 3 -r 2
done