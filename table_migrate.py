import argparse
import os
import shutil
import sys
import tables
import time
import uuid

FILTERS=tables.Filters(complevel=5, complib='zlib', fletcher32=True)


class GAConf_old(tables.IsDescription):
    population_size    = tables.UInt16Col()
    max_moves          = tables.UInt16Col()
    num_gens           = tables.UInt16Col()
    date               = tables.Time32Col()
    uuid4              = tables.StringCol(len(str(uuid.uuid4())))
    runtime_sec        = tables.Time32Col()
    network            = tables.StringCol(64)

class GAConf_new(tables.IsDescription):
    population_size    = tables.UInt16Col()
    max_moves          = tables.UInt16Col()
    num_gens           = tables.UInt16Col()
    date               = tables.Time32Col()
    uuid4              = tables.StringCol(len(str(uuid.uuid4())))
    runtime_sec        = tables.Time32Col()
    trail              = tables.StringCol(128)
    prob_mutate_bit    = tables.Float32Col()
    mutate_type        = tables.StringCol(32)
    prob_mutate        = tables.Float32Col()
    prob_crossover     = tables.Float32Col()
    tourn_size         = tables.UInt16Col()
    weight_min         = tables.Float32Col()
    weight_max         = tables.Float32Col()
    network            = tables.StringCol(64)
    hostname           = tables.StringCol(64)

def main():
    # Parse the arguments
    parser = argparse.ArgumentParser(
        description="Upgrades table format.")
    parser.add_argument('filename', type=str,
        help="Filenames of databases to perform upgrade on.")
    args = parser.parse_args()

    # Check that input file exists
    if not os.path.exists(args.filename):
        print "ERROR: Input file does not exist!"
        sys.exit(1)

    # Check that input file is a pytable
    try:
        with tables.openFile(args.filename) as fileh:
            pass
    except tables.exceptions.HDF5ExtError:
        print "ERROR: Input file does not appear to be a table!"
        sys.exit(2)

    # Create backup of file
    shutil.copy2(args.filename, args.filename + "_" + 
       str(int(time.time())) + ".bak")

    # Create a copy of table to work on.
    NEW_TABLE_TEMP_NAME = args.filename + ".wc"
    shutil.copy2(args.filename, NEW_TABLE_TEMP_NAME)

    # Start working on database
    with tables.openFile(NEW_TABLE_TEMP_NAME, mode="a", filters=FILTERS) as fileh:
        fileh.rename_node("/john_muir", name="run_conf", newname="run_conf_old")
        conf_table = fileh.createTable("/john_muir/", "run_conf", GAConf_new)
        conf_table_orig = fileh.getNode("/john_muir/run_conf_old")

        for old_row in conf_table_orig:
            new_row = conf_table.row
            new_row['population_size'] = old_row['population_size']
            new_row['max_moves']       = old_row['max_moves']
            new_row['num_gens']        = old_row['num_gens']
            new_row['date']            = old_row['date']
            new_row['uuid4']           = old_row['uuid4']
            new_row['runtime_sec']     = old_row['runtime_sec']
            new_row['trail']           = "John Muir Trail"
            new_row['prob_mutate_bit'] = 0.05
            new_row['mutate_type']     = "mutFlipBit"
            new_row['prob_mutate']     = 0.2
            new_row['prob_crossover']  = 0.5
            new_row['tourn_size']      = 3.0
            new_row['weight_min']      = -5.0
            new_row['weight_max']      = 5.0
            new_row['network']         = "Jefferson 2,5,4 NN v1"
            new_row['hostname']        = "Josh-Desk.joshmoles.com"

            new_row.append()

        conf_table.flush()

        conf_table_orig.remove()


    # If successful, move the working copy back over the original.
    shutil.move(NEW_TABLE_TEMP_NAME, args.filename)


if __name__ == '__main__':
    main()