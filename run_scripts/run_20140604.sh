#!/bin/bash
NICE=nice
NICENESS=0
REPEATS=5
MAX_MOVES=200

case $HOSTNAME in
	(inn)
		CORES=16
		echo "I am inn!"
		for i in {1..19}; do
			$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -n $i -t 3 -r $REPEATS -m $MAX_MOVES
		done
		;;
	(saane)
		CORES=16
		echo "I am saane!"
		for i in {20..37}; do
			$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -n $i -t 3 -r $REPEATS -m $MAX_MOVES
		done
		;;
	(rhine)
		CORES=16
		echo "I am rhine!"
		for i in {1..19}; do
			$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -n $i -t 3 -g 400 -p 150 -r $REPEATS -m $MAX_MOVES
		done
		;;
	(rhone)
		CORES=16
		echo "I am rhone!"
		for i in {20..37}; do
			$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -n $i -t 3 -g 400 -p 150 -r $REPEATS -m $MAX_MOVES
		done
		;;
	(thur)
		CORES=12
		echo "I am thur"
		for i in {1..19}; do
			$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -n $i -t 3 -g 600 -p 100 -r $REPEATS -m $MAX_MOVES
		done
		;;
	(zhora)
		CORES=12
		echo "I am zhora"
		for i in {20..37}; do
			$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -n $i -t 3 -g 600 -p 100 -r $REPEATS -m $MAX_MOVES
		done
		;;
	(taffey)
		CORES=12
		echo "I am taffey"
		for i in {1..19}; do
			$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -n $i -t 3 -g 800 -p 75 -r $REPEATS -m $MAX_MOVES
		done
		;;
	(eldon)
		CORES=12
		echo "I am eldon."
		for i in {20..37}; do
			$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -n $i -t 3 -g 800 -p 75 -r $REPEATS -m $MAX_MOVES
		done
		;;
	(gaff)
		CORES=12
		echo "I am gaff."
		;;

esac







