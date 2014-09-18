#!/bin/bash

CORES=24
NICE=19

nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 8 -r 20
nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 9 -r 20
nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 10 -r 20
nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 11 -r 20
nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 12 -r 20

nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 8 -r 20 -g 400
nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 9 -r 20 -g 400
nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 10 -r 20 -g 400 
nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 11 -r 20 -g 400 
nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 12 -r 20 -g 400 

nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 8 -r 20 -g 600 -p 100
nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 9 -r 20 -g 600 -p 100
nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 10 -r 20 -g 600 -p 100
nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 11 -r 20 -g 600 -p 100
nice -n $NICE python -m scoop -n $CORES -q ga_runner.py -n 12 -r 20 -g 600 -p 100

