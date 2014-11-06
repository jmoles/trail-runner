import datetime
import re
import subprocess
import sys

MOVES = [100, 200, 300, 400]
TRAIL = 5
CORES = [1, 2, 4, 8]
GENERATIONS = 100

COMMAND = ("python -m scoop -n {0} ga_runner.py --generation {1} "
    "--variation 5 --mutate-type 5 --prob-mutate 1.0 --no-early-quit "
    "--prob-crossover 0.6 --selection 6 --script-mode --mean-check-length 300 "
    "{2} 100 0 {3} 1")

RUN_ID_RE = "Completed repeat \d* with run ID (\d*)."

results_dict = {}

for core in CORES:
    results_dict[core] = {}

    for moves in MOVES:
        results_dict[core][moves] = {}

        cmd = COMMAND.format(core, GENERATIONS, TRAIL, moves)
        cmd = cmd.split()

        start = datetime.datetime.now()
        cmd_results = subprocess.check_output(cmd)
        runtime = datetime.datetime.now() - start

        re_res = re.search(RUN_ID_RE, cmd_results)

        if re_res:
            run_id = re_res.group(1)
        else:
            print "WARNING: No run_id match found!!!!"
            print cmd_results
            run_id = 0

        results_dict[core][moves]["time"] = runtime
        results_dict[core][moves]["id"] = run_id

for ttype in ["time", "id"]:
    if ttype == "time":
        table = ["\nTime Results", "-------------"]
    elif ttype == "id":
        table = ["\nRun ID Results", "--------------"]

    hdr =  [" Cores \ Moves "]
    hdr += [ "{0:>10}".format(x) for x in MOVES ]
    table.append("|" +  " | ".join(hdr) + " |")
    table.append("|" + "-|-".join(["-" * len(x) for x in hdr]) + "-|")

    for core in sorted(results_dict.keys()):
        row = [ "{0:>15}".format(core) ]

        for move in sorted(results_dict[core].keys()):
            if ttype == "time":
                this_value = int(
                    round(results_dict[core][move][ttype].total_seconds()))
            else:
                this_value = results_dict[core][move][ttype]
            row.append("{0:>10}".format(this_value))

        table.append("|" + " | ".join(row) + " |")

    print "\n".join(table)





