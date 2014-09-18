#!/bin/bash
NICE=nice
NICENESS=0

case $HOSTNAME in
	(taffey)
		CORES=8
		echo "I am taffey!"
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -n 39 -t 3 -r 20
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -n 39 -t 3 -r 20 -g 400 -p 150
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -n 39 -t 3 -r 20 -g 600 -p 100
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -n 39 -t 3 -r 20 -g 800 -p 75
		;;
	(zhora)
		CORES=8
		echo "I am zhora!"
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -n 40 -t 3 -r 20
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -n 40 -t 3 -r 20 -g 400 -p 150
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -n 40 -t 3 -r 20 -g 600 -p 100
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -n 40 -t 3 -r 20 -g 800 -p 75
		;;
	(aar)
		CORES=8
		echo "I am aar!"
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -n 41 -t 3 -r 20
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -n 41 -t 3 -r 20 -g 400 -p 150
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -n 41 -t 3 -r 20 -g 600 -p 100
		$NICE -n $NICENESS python -m scoop -n $CORES -q ga_runner.py -n 41 -t 3 -r 20 -g 800 -p 75
		;;

esac







