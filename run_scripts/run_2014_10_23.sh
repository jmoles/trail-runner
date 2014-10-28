#!/bin/bash
NICE=nice
NICENESS=0

TRAIL=3
NETWORK=1
GENERATIONS=100
POPULATION=800
REPEAT=10

mutate_values=(0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9)
xover_values=(0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9)

case $HOSTNAME in
	(inn)
		SELECTION_TYPE=3
		MOVES=325
		for curr_xover in "${xover_values[@]}"
		do
			for curr_mutate in "${mutate_values[@]}"
			do
				$NICE -n $NICENESS python -m scoop -q ga_runner.py -r $REPEAT \
				-g $GENERATIONS --variation 2 --lambda 1600 \
				--selection $SELECTION_TYPE \
				--prob-crossover $curr_xover --prob-mutate $curr_mutate \
				$NETWORK $TRAIL $POPULATION $MOVES
			done
		done
		;;
	(saane)
		SELECTION_TYPE=2
		MOVES=325
		for curr_xover in "${xover_values[@]}"
		do
			for curr_mutate in "${mutate_values[@]}"
			do
				$NICE -n $NICENESS python -m scoop -q ga_runner.py \
				-r $REPEAT -g $GENERATIONS --variation 2 --lambda 1600 \
				--selection $SELECTION_TYPE \
				--prob-crossover $curr_xover --prob-mutate $curr_mutate \
				$NETWORK $TRAIL $POPULATION $MOVES
			done
		done
		;;
	(rhine)
		SELECTION_TYPE=1
		MOVES=325
		for curr_xover in "${xover_values[@]}"
		do
			for curr_mutate in "${mutate_values[@]}"
			do
				$NICE -n $NICENESS python -m scoop -q ga_runner.py \
				-r $REPEAT -g $GENERATIONS --variation 2 --lambda 1600 \
				--selection $SELECTION_TYPE --tournament-size 160 \
				--prob-crossover $curr_xover --prob-mutate $curr_mutate \
				$NETWORK $TRAIL $POPULATION $MOVES
			done
		done
		;;
	(rhone)
		SELECTION_TYPE=6
		MOVES=325
		for curr_xover in "${xover_values[@]}"
		do
			for curr_mutate in "${mutate_values[@]}"
			do
				$NICE -n $NICENESS python -m scoop -q ga_runner.py \
				-r $REPEAT -g $GENERATIONS --variation 2 --lambda 1600 \
				--selection $SELECTION_TYPE \
				--prob-crossover $curr_xover --prob-mutate $curr_mutate \
				$NETWORK $TRAIL $POPULATION $MOVES
			done
		done
		;;
	(thur)
		SELECTION_TYPE=3
		MOVES=200
		for curr_xover in "${xover_values[@]}"
		do
			for curr_mutate in "${mutate_values[@]}"
			do
				$NICE -n $NICENESS python -m scoop -q ga_runner.py \
				-r $REPEAT -g $GENERATIONS --variation 2 --lambda 1600 \
				--selection $SELECTION_TYPE \
				--prob-crossover $curr_xover --prob-mutate $curr_mutate \
				$NETWORK $TRAIL $POPULATION $MOVES
			done
		done
		;;
	(zhora)
		SELECTION_TYPE=2
		MOVES=200
		for curr_xover in "${xover_values[@]}"
		do
			for curr_mutate in "${mutate_values[@]}"
			do
				$NICE -n $NICENESS python -m scoop -q ga_runner.py \
				-r $REPEAT -g $GENERATIONS --variation 2 --lambda 1600 \
				--selection $SELECTION_TYPE \
				--prob-crossover $curr_xover --prob-mutate $curr_mutate \
				$NETWORK $TRAIL $POPULATION $MOVES
			done
		done
		;;
	(taffey)
		SELECTION_TYPE=1
		MOVES=200
		for curr_xover in "${xover_values[@]}"
		do
			for curr_mutate in "${mutate_values[@]}"
			do
				$NICE -n $NICENESS python -m scoop -q ga_runner.py \
				-r $REPEAT -g $GENERATIONS --variation 2 --lambda 1600 \
				--selection $SELECTION_TYPE --tournament-size 160 \
				--prob-crossover $curr_xover --prob-mutate $curr_mutate \
				$NETWORK $TRAIL $POPULATION $MOVES
			done
		done
		;;
	(eldon)
		SELECTION_TYPE=6
		MOVES=200
		for curr_xover in "${xover_values[@]}"
		do
			for curr_mutate in "${mutate_values[@]}"
			do
				$NICE -n $NICENESS python -m scoop -q ga_runner.py \
				-r $REPEAT -g $GENERATIONS --variation 2 --lambda 1600 \
				--selection $SELECTION_TYPE \
				--prob-crossover $curr_xover --prob-mutate $curr_mutate \
				$NETWORK $TRAIL $POPULATION $MOVES
			done
		done
		;;
	(gaff)
		;;
	(harry)
		;;
	(holden)
		;;
	(ticino)
		;;
esac
