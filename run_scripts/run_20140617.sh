#!/bin/bash
NICE=nice
NICENESS=0
REPEATS1=10
REPEATS2=20
MAX_MOVES=200

case $HOSTNAME in
	(thur)
		CORES=12
		echo "I am thur"
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -g 10000 -p 40 -n 33 -t 3 -r $REPEATS1 -m $MAX_MOVES
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -g 10000 -p 40 -n 9 -t 3 -r 2 -m $MAX_MOVES
		;;


esac







