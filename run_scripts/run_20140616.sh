#!/bin/bash
NICE=nice
NICENESS=0
REPEATS1=10
REPEATS2=20
MAX_MOVES=200

case $HOSTNAME in
	(inn)
		CORES=16
		echo "I am inn!"
		for i in {1..19}; do
			$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -g 10000 -p 40 -n $i -t 3 -r $REPEATS1 -m $MAX_MOVES
		done
		;;
	(saane)
		CORES=16
		echo "I am saane!"
		for i in {20..37}; do
			$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -g 10000 -p 40 -n $i -t 3 -r $REPEATS1 -m $MAX_MOVES
		done
		;;
	(rhine)
		CORES=16
		echo "I am rhine!"
		for i in {1..19}; do
			$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -g 10000 -p 40 -n $i -t 3 -r $REPEATS1 -m $MAX_MOVES
		done
		;;
	(harry)
		CORES=12
		echo "I am harry!"
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -g 10000 -p 40 -n 26 -t 3 -r $REPEATS1 -m $MAX_MOVES
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -g 10000 -p 40 -n 27 -t 3 -r $REPEATS1 -m $MAX_MOVES
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -g 10000 -p 40 -n 28 -t 3 -r $REPEATS1 -m $MAX_MOVES
		;;
	(thur)
		CORES=12
		echo "I am thur"
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -g 10000 -p 40 -n 29 -t 3 -r $REPEATS1 -m $MAX_MOVES
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -g 10000 -p 40 -n 30 -t 3 -r $REPEATS1 -m $MAX_MOVES
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -g 10000 -p 40 -n 31 -t 3 -r $REPEATS1 -m $MAX_MOVES
		;;
	(zhora)
		CORES=12
		echo "I am zhora"
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -g 10000 -p 40 -n 32 -t 3 -r $REPEATS1 -m $MAX_MOVES
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -g 10000 -p 40 -n 33 -t 3 -r $REPEATS1 -m $MAX_MOVES
		;;
	(taffey)
		CORES=12
		echo "I am taffey"
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -g 10000 -p 40 -n 34 -t 3 -r $REPEATS1 -m $MAX_MOVES
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -g 10000 -p 40 -n 35 -t 3 -r $REPEATS1 -m $MAX_MOVES
		;;
	(eldon)
		CORES=12
		echo "I am eldon."
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -g 10000 -p 40 -n 36 -t 3 -r $REPEATS1 -m $MAX_MOVES
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -g 10000 -p 40 -n 37 -t 3 -r $REPEATS1 -m $MAX_MOVES
		;;
	(gaff)
		CORES=12
		echo "I am gaff."
		;;

esac







