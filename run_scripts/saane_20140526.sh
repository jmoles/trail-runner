#!/bin/bash
NICE=19
CORES=16

for i in {1..37}; do
	nice -n $NICE python -m scoop -n $CORES ga_runner.py -n $i -t 3 -g 600 -p 100 -r 20
done