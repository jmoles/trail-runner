#!/bin/bash

CORES=24
NICE=19

nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 1 -r 20
nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 2 -r 20
nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 3 -r 20 
nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 4 -r 20 
nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 5 -r 20 
nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 6 -r 20 
nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 7 -r 20 

