#!/bin/bash
NICE=nice
NICENESS=0
REPEATS1=10
REPEATS2=10
MAX_MOVES=200
CORES=8

case $HOSTNAME in
	(inn)
		echo "I am inn!"
		for i in {1..19}; do
			$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -g 10000 -p 40 -n $i -t 3 -r $REPEATS1 -m $MAX_MOVES
		done
		;;
	(saane)
		echo "I am saane!"
		for i in {20..37}; do
			$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -g 10000 -p 40 -n $i -t 3 -r $REPEATS1 -m $MAX_MOVES
		done
		;;
	(rhine)
		echo "I am rhine!"
		for i in {1..19}; do
			$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -g 10000 -p 40 -n $i -t 3 -r $REPEATS1 -m $MAX_MOVES
		done
		;;
	(rhone)
		echo "I am rhone!"
		for i in {20..37}; do
			$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -g 10000 -p 40 -n $i -t 3 -r $REPEATS1 -m $MAX_MOVES
		done
		;;
	(thur)
		echo "I am thur"
		for i in {1..19}; do
			$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py --prob-mutate 0.3 -n $i -t 3 -g 800 -p 75 -r $REPEATS2 -m $MAX_MOVES
		done
		;;
	(zhora)
		echo "I am zhora"
		for i in {20..37}; do
			$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py --prob-mutate 0.3 -n $i -t 3 -g 800 -p 75 -r $REPEATS2 -m $MAX_MOVES
		done
		;;
	(taffey)
		echo "I am taffey"
		for i in {1..19}; do
			$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py --prob-mutate 0.6 -n $i -t 3 -g 800 -p 75 -r $REPEATS2 -m $MAX_MOVES
		done
		;;
	(eldon)
		echo "I am eldon."
		for i in {20..37}; do
			$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py --prob-mutate 0.6 -n $i -t 3 -g 800 -p 75 -r $REPEATS2 -m $MAX_MOVES
		done
		;;
	(gaff)
		echo "I am gaff."
		;;

esac







