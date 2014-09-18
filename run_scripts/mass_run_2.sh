#!/bin/bash

CORES=24
NICE=19

nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 1 -p 100 -g 600 -r 20
nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 2 -p 100 -g 600 -r 20
nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 3 -p 100 -g 600 -r 20 
nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 4 -p 100 -g 600 -r 20 
nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 5 -p 100 -g 600 -r 20 
nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 6 -p 100 -g 600 -r 20 
nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 7 -p 100 -g 600 -r 20 